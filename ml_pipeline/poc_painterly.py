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
from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
from transformers import DPTImageProcessor, DPTForDepthEstimation

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


def load_sd_pipeline():
    """Load Stable Diffusion 1.5 img2img pipeline."""
    print("\n📥 Loading Stable Diffusion 1.5 pipeline...")
    print("   (This will download ~4GB on first run - please wait)")
    start = time.time()

    # Load SD 1.5 with img2img
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,  # Disable for local use
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


def generate_painterly(image, pipe, style="oil painting", strength=0.5, seed=42):
    """Generate painterly version using img2img.

    IMPORTANT: Uses moderate strength (0.5-0.55) with enhanced prompts
    for strong painterly effect while maintaining subject content.
    """
    print(f"\n🎨 Generating painterly image (style: {style}, strength: {strength})...")
    start = time.time()

    # Set up generator for reproducibility
    generator = torch.Generator(device=device).manual_seed(seed)

    # IMPROVED: Enhanced prompts for stronger painterly effect while preserving subject
    # Focus on painting techniques and artistic style
    prompt = f"{style}, thick paint strokes, impasto technique, canvas texture, painted by master artist, rich colors, visible brush marks"

    # IMPROVED: Negative prompt focuses on photographic qualities and artifacts
    # This helps achieve painterly effect while keeping subject recognizable
    negative_prompt = "photograph, camera, lens, photorealistic, smooth, digital, blurry, distorted, deformed, disfigured, ugly, bad anatomy, missing parts"

    # Use moderate-high strength for visible painterly effect
    # 0.5-0.55 gives strong artistic transformation while keeping content intact
    actual_strength = min(strength, 0.55)  # Cap at 0.55 for enhanced painterly effect

    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            strength=actual_strength,  # Lower strength preserves subject matter
            guidance_scale=7.5,
            num_inference_steps=30,  # Reduce for speed on Mac
            generator=generator,
        ).images[0]

    print(f"✅ Painterly image generated in {time.time() - start:.2f}s")
    print(f"   (Used strength: {actual_strength} for enhanced painterly effect)")
    return result


def main(input_image_path, style="oil painting", strength=0.5, seed=42):
    """Main pipeline: Image -> Depth -> Painterly."""
    print("=" * 60)
    print("🎨 3D Painterly Image Generator - Proof of Concept")
    print("=" * 60)

    # Load input image
    print(f"\n📂 Loading input image: {input_image_path}")
    image = Image.open(input_image_path).convert("RGB")

    # Resize to reasonable size for processing (Mac optimization)
    max_size = 768
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        print(f"   Resized to {new_size} for efficient processing")

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

    # Step 2: Generate painterly image
    sd_pipe = load_sd_pipeline()
    painterly = generate_painterly(image, sd_pipe, style=style, strength=strength, seed=seed)

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
        print("Usage: python poc_painterly.py <input_image_path> [style] [strength] [seed]")
        print("\nExample:")
        print("  python poc_painterly.py test_photo.jpg")
        print("  python poc_painterly.py test_photo.jpg 'watercolor' 0.6 123")
        sys.exit(1)

    input_path = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "oil painting"
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42

    main(input_path, style, strength, seed)
