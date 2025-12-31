#!/usr/bin/env python3
"""
Proof of Concept: Photo to Painterly 3D Image Generator
Phase 1 - Basic pipeline: Image -> Depth Map -> Painterly Output

This script demonstrates the core ML pipeline for generating painterly
images with depth information, optimized for Apple Silicon MPS.
"""

import os
import sys
import time
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import cv2
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionControlNetImg2ImgPipeline, ControlNetModel, DPMSolverMultistepScheduler
from transformers import DPTImageProcessor, DPTForDepthEstimation
from controlnet_aux import CannyDetector
from style_presets import get_preset, get_preset_names

# Configuration
OUTPUT_DIR = Path("storage/jobs/poc_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Device setup - use MPS on Apple Silicon
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ Using MPS (Apple Silicon GPU)")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("✅ Using CUDA GPU")
else:
    device = torch.device("cpu")
    print("⚠️  Using CPU (will be slow)")


def load_depth_model():
    """Load MiDaS DPT depth estimation model."""
    print("\n📥 Loading depth estimation model (MiDaS DPT)...")
    start = time.time()

    processor = DPTImageProcessor.from_pretrained("Intel/dpt-hybrid-midas")
    model = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas")
    model = model.to(device)
    model.eval()

    print(f"✅ Depth model loaded in {time.time() - start:.2f}s")
    return processor, model


def generate_depth_map(image, processor, model):
    """Generate depth map from input image."""
    print("\n🎨 Generating depth map...")
    start = time.time()

    # Prepare image for depth model
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate depth
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_depth = outputs.predicted_depth

    # Interpolate to original size
    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    )

    # Normalize to 0-255
    depth = prediction.squeeze().cpu().numpy()
    depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
    depth = depth.astype(np.uint8)

    # Convert to PIL Image
    depth_image = Image.fromarray(depth, mode='L')

    print(f"✅ Depth map generated in {time.time() - start:.2f}s")
    return depth_image


def generate_canny_edges(image, low_threshold=100, high_threshold=200):
    """Generate Canny edge map for ControlNet conditioning.

    Args:
        image: PIL Image
        low_threshold: Lower threshold for Canny edge detection
        high_threshold: Upper threshold for Canny edge detection

    Returns:
        PIL Image of Canny edges
    """
    print("\n🎨 Generating Canny edges for structure preservation...")
    start = time.time()

    # Convert PIL to numpy
    image_np = np.array(image)

    # Convert to grayscale for edge detection
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    # Apply Canny edge detection
    edges = cv2.Canny(gray, low_threshold, high_threshold)

    # Convert back to 3-channel image for ControlNet
    edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    # Convert to PIL
    edges_pil = Image.fromarray(edges_rgb)

    print(f"✅ Canny edges generated in {time.time() - start:.2f}s")
    return edges_pil


def load_sd_pipeline(use_controlnet=False):
    """Load Stable Diffusion 1.5 img2img pipeline with optional ControlNet.

    Args:
        use_controlnet: Whether to load ControlNet for edge conditioning

    Returns:
        SD pipeline (with or without ControlNet)
    """
    print(f"\n📥 Loading Stable Diffusion 1.5 pipeline{' with ControlNet' if use_controlnet else ''}...")
    print("   (This will download ~4GB on first run - please wait)")
    start = time.time()

    # Load SD 1.5 with optional ControlNet
    if use_controlnet:
        print("   Loading ControlNet Canny model...")
        controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-canny",
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        )

        pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            controlnet=controlnet,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            safety_checker=None,
        )
    else:
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            safety_checker=None,
        )

    # Optimize for Apple Silicon
    if device.type == "mps":
        # Enable attention slicing for memory efficiency
        pipe.enable_attention_slicing()
        pipe = pipe.to(device)
    else:
        pipe = pipe.to(device)

    # Use faster scheduler
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    print(f"✅ SD pipeline loaded in {time.time() - start:.2f}s")
    return pipe


def generate_painterly(image, pipe, style="oil_painting", strength=0.5, seed=42, control_image=None, controlnet_conditioning_scale=0.5):
    """Generate painterly version using img2img with style presets and optional ControlNet.

    Creates cohesive, flowing painterly compositions using pre-configured
    style presets that optimize prompts and parameters for each artistic style.
    Optional ControlNet Canny edge conditioning preserves structural details.

    Args:
        image: Input PIL Image
        pipe: Stable Diffusion pipeline (with or without ControlNet)
        style: Style preset name (e.g., 'oil_painting', 'watercolor')
        strength: Transformation strength (0.0-1.0)
        seed: Random seed for reproducibility
        control_image: Optional Canny edge image for ControlNet conditioning
        controlnet_conditioning_scale: How much to follow edges (0.0-1.0)
    """
    print(f"\n🎨 Generating painterly image (style: {style}, strength: {strength})...")
    if control_image is not None:
        print(f"   Using ControlNet edge conditioning (scale: {controlnet_conditioning_scale})")
    start = time.time()

    # Load style preset
    try:
        preset = get_preset(style)
        print(f"   Using preset: {preset.name}")
    except KeyError:
        # Fallback to oil_painting if preset not found
        print(f"   ⚠️  Unknown style '{style}', falling back to 'oil_painting'")
        preset = get_preset("oil_painting")

    # Set up generator for reproducibility
    generator = torch.Generator(device=device).manual_seed(seed)

    # Use preset prompts
    prompt = preset.base_prompt
    negative_prompt = preset.negative_prompt

    # Adaptive parameters based on both strength and preset recommendations
    # User strength overrides preset defaults, but uses preset as starting point
    if strength > 0.7:
        num_steps = max(preset.recommended_steps + 10, 50)  # More steps for high abstraction
        guidance = max(preset.recommended_guidance - 1.0, 5.5)  # Lower guidance for more freedom
    elif strength > 0.5:
        num_steps = preset.recommended_steps
        guidance = preset.recommended_guidance
    else:
        num_steps = max(preset.recommended_steps - 10, 30)  # Fewer steps for subtle changes
        guidance = min(preset.recommended_guidance + 0.5, 8.0)

    print(f"   Prompt: {prompt[:80]}...")
    print(f"   Parameters: steps={num_steps}, guidance={guidance}, strength={strength}")

    with torch.no_grad():
        # Build kwargs based on whether ControlNet is being used
        kwargs = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "image": image,
            "strength": strength,
            "guidance_scale": guidance,
            "num_inference_steps": num_steps,
            "generator": generator,
        }

        # Add ControlNet parameters if control image is provided
        if control_image is not None:
            kwargs["control_image"] = control_image
            kwargs["controlnet_conditioning_scale"] = controlnet_conditioning_scale

        result = pipe(**kwargs).images[0]

    print(f"✅ Painterly image generated in {time.time() - start:.2f}s")
    return result


def main(input_image_path, style="oil_painting", strength=0.5, seed=42, max_size=768, use_controlnet=False):
    """Main pipeline: Image -> Depth -> Painterly with optional ControlNet.

    Args:
        input_image_path: Path to input image
        style: Style preset name (e.g., 'oil_painting', 'watercolor', 'impressionist')
        strength: Transformation strength (0.0-1.0)
        seed: Random seed for reproducibility
        max_size: Maximum dimension for processing (256-2048)
        use_controlnet: Whether to use ControlNet for edge-preserving conditioning
    """
    print("=" * 60)
    print("🎨 3D Painterly Image Generator - Proof of Concept")
    print("=" * 60)
    print(f"\nAvailable styles: {', '.join(get_preset_names())}")

    # Load input image
    print(f"\n📂 Loading input image: {input_image_path}")
    image = Image.open(input_image_path).convert("RGB")

    # Resize to specified max size for processing
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        print(f"   Resized to {new_size} (max_size={max_size})")

    print(f"   Image size: {image.size}")

    # Save original
    original_path = OUTPUT_DIR / "01_original.png"
    image.save(original_path)
    print(f"   Saved: {original_path}")

    # Step 1: Generate depth map
    depth_processor, depth_model = load_depth_model()
    depth_map = generate_depth_map(image, depth_processor, depth_model)

    depth_path = OUTPUT_DIR / "02_depth_map.png"
    depth_map.save(depth_path)
    print(f"   Saved: {depth_path}")

    # Clear depth model from memory
    del depth_model, depth_processor
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()

    # Step 1.5: Generate Canny edges if using ControlNet
    control_image = None
    if use_controlnet:
        control_image = generate_canny_edges(image)
        canny_path = OUTPUT_DIR / "02b_canny_edges.png"
        control_image.save(canny_path)
        print(f"   Saved: {canny_path}")

    # Step 2: Generate painterly image
    sd_pipe = load_sd_pipeline(use_controlnet=use_controlnet)
    painterly = generate_painterly(
        image, sd_pipe,
        style=style,
        strength=strength,
        seed=seed,
        control_image=control_image,
        controlnet_conditioning_scale=0.5 if use_controlnet else 0.0
    )

    painterly_path = OUTPUT_DIR / "03_painterly_output.png"
    painterly.save(painterly_path)
    print(f"   Saved: {painterly_path}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ PROOF OF CONCEPT COMPLETE!")
    print("=" * 60)
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"  - Original: {original_path.name}")
    print(f"  - Depth Map: {depth_path.name}")
    print(f"  - Painterly: {painterly_path.name}")
    print("\nNext: Review outputs and verify depth influence on painterly effect")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        available_styles = get_preset_names()
        print("Usage: python poc_painterly.py <input_image_path> [style] [strength] [seed] [max_size] [use_controlnet]")
        print("\nAvailable Styles:")
        for style_name in available_styles:
            preset = get_preset(style_name)
            print(f"  - {style_name:20s} : {preset.description}")
        print("\nExamples:")
        print("  python poc_painterly.py test_photo.jpg")
        print("  python poc_painterly.py test_photo.jpg watercolor 0.6 123")
        print("  python poc_painterly.py test_photo.jpg oil_painting 0.5 42 512  # Fast preview")
        print("  python poc_painterly.py test_photo.jpg impressionist 0.55 42 1024")
        print("  python poc_painterly.py test_photo.jpg watercolor 0.6 42 1024 true  # With ControlNet edge preservation")
        sys.exit(1)

    input_path = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "oil_painting"
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    max_size = int(sys.argv[5]) if len(sys.argv) > 5 else 768
    use_controlnet = sys.argv[6].lower() == 'true' if len(sys.argv) > 6 else False

    if max_size < 256 or max_size > 2048:
        print("❌ max_size must be between 256 and 2048")
        sys.exit(1)

    main(input_path, style, strength, seed, max_size, use_controlnet)
