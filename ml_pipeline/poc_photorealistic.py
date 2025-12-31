#!/usr/bin/env python3
"""
Proof of Concept: Photo-Realistic Depth Layer Generation
Demonstrates photo-realistic mode: Photo -> Depth Map -> Layered output (no AI transformation)

This is MUCH faster than painterly mode since it skips Stable Diffusion.
"""

import os
import sys
import time
import json
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from transformers import DPTImageProcessor, DPTForDepthEstimation
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
from diffusers import StableDiffusionInpaintPipeline
import cv2

# Configuration
OUTPUT_DIR = Path("storage/jobs/photorealistic_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Device setup
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
    depth_image = Image.fromarray(depth)

    print(f"✅ Depth map generated in {time.time() - start:.2f}s")
    return depth_image, depth


def load_segmentation_model():
    """Load semantic segmentation model for detecting people, animals, objects."""
    print("\n📥 Loading semantic segmentation model...")
    start = time.time()

    # Use nvidia/segformer-b5-finetuned-ade-640-640 - excellent for person/object detection
    model_name = "nvidia/segformer-b5-finetuned-ade-640-640"
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModelForSemanticSegmentation.from_pretrained(model_name)
    model = model.to(device)
    model.eval()

    print(f"✅ Segmentation model loaded in {time.time() - start:.2f}s")
    return processor, model


def inpaint_background_opencv(image, subject_mask):
    """
    Use OpenCV NS (Navier-Stokes) inpainting for better background filling.
    Slower than Telea (~1-2s vs ~0.5s) but significantly better quality.

    Args:
        image: PIL Image - original image
        subject_mask: numpy array - binary mask where 1=subject, 0=background

    Returns:
        PIL Image - background with subjects inpainted
    """
    print("\n🎨 Inpainting background with OpenCV NS algorithm...")
    start = time.time()

    # Convert to numpy arrays
    img_np = np.array(image.convert("RGB"))
    mask_np = (subject_mask > 0).astype(np.uint8) * 255

    # Dilate mask slightly to ensure complete coverage
    kernel = np.ones((5, 5), np.uint8)
    mask_dilated = cv2.dilate(mask_np, kernel, iterations=3)

    # Use cv2.INPAINT_NS (Navier-Stokes) for better quality inpainting
    inpainted = cv2.inpaint(img_np, mask_dilated, inpaintRadius=10, flags=cv2.INPAINT_NS)

    # Convert back to PIL
    result = Image.fromarray(inpainted)

    print(f"✅ Background inpainted in {time.time() - start:.2f}s")
    return result


def load_inpainting_model():
    """Load Stable Diffusion inpainting model for highest quality background filling."""
    print("\n📥 Loading SD inpainting model (slow but highest quality)...")
    start = time.time()

    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        "runwayml/stable-diffusion-inpainting",
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,
    )
    pipe = pipe.to(device)

    print(f"✅ Inpainting model loaded in {time.time() - start:.2f}s")
    return pipe


def inpaint_background_sd(image, subject_mask, inpaint_pipe):
    """
    Use Stable Diffusion inpainting for highest quality background filling.
    Much slower than OpenCV (~5-7s) but better quality.

    Args:
        image: PIL Image - original image
        subject_mask: numpy array - binary mask where 1=subject, 0=background
        inpaint_pipe: Stable Diffusion inpainting pipeline

    Returns:
        PIL Image - background with subjects inpainted
    """
    print("\n🎨 Inpainting background with Stable Diffusion...")
    start = time.time()

    # Convert subject mask to PIL Image
    mask_img = Image.fromarray((subject_mask > 0).astype(np.uint8) * 255)

    # Inpaint the masked areas
    prompt = "natural scenery, background, seamless, photorealistic, high quality"
    negative_prompt = "people, person, human, animal, text, watermark, blurry"

    result = inpaint_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=image,
        mask_image=mask_img,
        num_inference_steps=30,
        guidance_scale=7.5,
    ).images[0]

    print(f"✅ Background inpainted in {time.time() - start:.2f}s")
    return result


def detect_subjects_semantic(image, processor, model):
    """
    Use semantic segmentation to detect people, animals, and key objects.
    Each detected subject gets a unique ID in the returned mask.

    Returns:
        subject_mask: numpy array where 0=background, 1=subject1, 2=subject2, etc.
        subject_count: number of subjects detected
    """
    print("\n👥 Detecting subjects using semantic segmentation...")
    start = time.time()

    # Process image
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Run segmentation
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    # Resize to original image size
    h, w = image.size[1], image.size[0]
    segmentation = torch.nn.functional.interpolate(
        logits,
        size=(h, w),
        mode="bilinear",
        align_corners=False
    )

    # Get the class predictions
    seg_map = segmentation.argmax(dim=1)[0].cpu().numpy()

    # ADE20K class IDs for subjects we want to isolate
    # 12 = person, 13 = animal/dog/cat, 20 = car, 6 = building, etc.
    # Priority classes that should be isolated on their own layer
    SUBJECT_CLASSES = {
        12: "person",      # People - highest priority
        13: "animal",      # Animals
        17: "dog",
        18: "cat",
        19: "bird",
        20: "car",
        21: "truck",
        26: "horse",
        62: "statue",
        72: "bicycle",
        85: "bottle",
        88: "vase"
    }

    # Create subject mask with unique IDs for each detected object
    subject_mask = np.zeros_like(seg_map, dtype=np.int32)
    subject_id = 1
    subject_info = []

    # Find each subject class in the image
    for class_id, class_name in SUBJECT_CLASSES.items():
        class_mask = (seg_map == class_id)

        if class_mask.sum() > (seg_map.size * 0.01):  # At least 1% of image
            # Use connected components to separate multiple instances
            num_labels, labels = cv2.connectedComponents(class_mask.astype(np.uint8))

            # Process each connected component (each separate object)
            for component_id in range(1, num_labels):  # Skip 0 (background)
                component_mask = (labels == component_id)
                component_size = component_mask.sum()

                # Only keep significant components (>0.5% of image)
                if component_size > (seg_map.size * 0.005):
                    subject_mask[component_mask] = subject_id
                    coverage = component_size / seg_map.size * 100
                    subject_info.append({
                        "id": subject_id,
                        "class": class_name,
                        "coverage": coverage
                    })
                    print(f"   Subject {subject_id}: {class_name} ({coverage:.1f}% of image)")
                    subject_id += 1

    subject_count = subject_id - 1

    print(f"✅ Subject detection completed in {time.time() - start:.2f}s")
    print(f"   Found {subject_count} subjects")

    return subject_mask, subject_count


def separate_into_layers(image, depth_array, num_layers=3, subject_mask=None, feather_radius=2, inpainted_background=None):
    """
    Separate image into depth-based layers with alpha transparency.
    Uses semantic segmentation to keep subjects together on the same layer.

    IMPORTANT: Background layer (Layer 1) uses AI-inpainted background or blurred fallback
    to prevent transparent holes when viewed from angles in physical prints.

    Args:
        image: Input PIL Image
        depth_array: Depth map as numpy array
        num_layers: Number of layers to create
        subject_mask: Optional semantic segmentation mask where each subject has unique ID
        feather_radius: Radius for feathering edges
        inpainted_background: Optional AI-inpainted background image (PIL Image)
    """
    print(f"\n🔪 Separating into {num_layers} depth layers...")
    start = time.time()

    # Convert image to RGBA
    image_rgba = image.convert("RGBA")
    img_array = np.array(image_rgba)

    # Use inpainted background if available, otherwise use blurred fallback
    if inpainted_background is not None:
        background_img = np.array(inpainted_background.convert("RGB"))
        print(f"   Using AI-inpainted background")
    else:
        img_rgb = np.array(image.convert("RGB"))
        background_img = cv2.GaussianBlur(img_rgb, (21, 21), 10)  # Heavy blur for fallback
        print(f"   Using blurred background fallback")

    layers = []
    layer_info = []

    # IMPROVED: Combine depth percentiles with subject-aware layering
    percentiles = np.linspace(0, 100, num_layers + 1)
    thresholds = np.percentile(depth_array, percentiles)

    print(f"   Depth distribution analysis:")
    print(f"   Min: {depth_array.min()}, Max: {depth_array.max()}")
    print(f"   Percentile thresholds: {[int(t) for t in thresholds]}")

    # If we have subject masks, assign each subject to a layer based on its median depth
    subject_to_layer = {}
    if subject_mask is not None and subject_mask.max() > 0:
        print(f"   Assigning {int(subject_mask.max())} subjects to layers...")
        for subject_id in range(1, int(subject_mask.max()) + 1):
            subject_pixels = depth_array[subject_mask == subject_id]
            if len(subject_pixels) > 0:
                median_depth = np.median(subject_pixels)
                # Find which layer this median depth belongs to
                assigned_layer = 0
                for i in range(num_layers):
                    if median_depth >= thresholds[i] and (i == num_layers - 1 or median_depth < thresholds[i + 1]):
                        assigned_layer = i
                        break
                subject_to_layer[subject_id] = assigned_layer
                print(f"      Subject {subject_id}: median depth {median_depth:.1f} -> Layer {assigned_layer + 1}")

    for i in range(num_layers):
        # Use percentile-based ranges instead of equal bins
        range_start = int(thresholds[i])
        range_end = int(thresholds[i + 1])

        # Start with depth-based mask
        if i == num_layers - 1:
            depth_mask = ((depth_array >= range_start) & (depth_array <= range_end))
        else:
            depth_mask = ((depth_array >= range_start) & (depth_array < range_end))

        # SUBJECT-AWARE MODIFICATION: Keep subjects together
        # If a subject's median depth assigns it to this layer, include ALL of it
        # If a subject belongs to another layer, remove it from this depth mask
        if subject_mask is not None and len(subject_to_layer) > 0:
            for subject_id, assigned_layer in subject_to_layer.items():
                subject_region = (subject_mask == subject_id)
                if assigned_layer == i:
                    # This subject belongs to THIS layer - force include entire subject
                    depth_mask = depth_mask | subject_region
                else:
                    # This subject belongs to a DIFFERENT layer - remove it from this layer
                    # Only remove it if there's significant overlap (>10% of subject in this depth range)
                    overlap = depth_mask & subject_region
                    overlap_ratio = np.sum(overlap) / np.sum(subject_region) if np.sum(subject_region) > 0 else 0
                    if overlap_ratio > 0.1:  # More than 10% overlap
                        # Subject split across layers - remove it from wrong layer
                        depth_mask = depth_mask & ~subject_region

        mask = depth_mask.astype(np.uint8) * 255

        # Calculate coverage for reporting
        coverage = (mask > 0).sum() / mask.size * 100

        # Apply feathering (Gaussian blur on mask)
        # Use configurable feather radius
        mask_feathered = cv2.GaussianBlur(mask, (5, 5), feather_radius)

        # SPECIAL HANDLING FOR BACKGROUND LAYER (Layer 1)
        if i == 0:  # Background layer
            # Background layer shows the actual background sharply,
            # and fills areas that will be covered by other layers with blur
            layer = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)

            # Start with full blurred image
            layer[:, :, :3] = background_img

            # Create inverse mask - everything NOT in foreground/midground layers
            # This means: blur everything except what's actually in this background layer
            foreground_midground_mask = np.zeros_like(mask, dtype=bool)
            if subject_mask is not None and len(subject_to_layer) > 0:
                # Mark all pixels that belong to other layers (foreground/midground subjects)
                for subject_id, assigned_layer in subject_to_layer.items():
                    if assigned_layer > i:  # Layers in front of background
                        foreground_midground_mask |= (subject_mask == subject_id)

            # Also add depth-based pixels from other layers
            for j in range(i + 1, num_layers):
                if j == num_layers - 1:
                    other_layer_mask = ((depth_array >= thresholds[j]) & (depth_array <= thresholds[j + 1]))
                else:
                    other_layer_mask = ((depth_array >= thresholds[j]) & (depth_array < thresholds[j + 1]))
                foreground_midground_mask |= other_layer_mask

            # Apply smoothing for gradual transition
            blend_feather_radius = 10
            foreground_blur = foreground_midground_mask.astype(np.uint8) * 255
            foreground_blur = cv2.GaussianBlur(foreground_blur, (21, 21), blend_feather_radius)

            # Where the actual background is, show it sharply
            background_mask_3d = np.stack([mask_feathered] * 3, axis=2) / 255.0
            layer[:, :, :3] = (
                layer[:, :, :3] * (1 - background_mask_3d) +  # Blurred fill
                img_array[:, :, :3] * background_mask_3d      # Sharp actual background
            ).astype(np.uint8)

            # Background layer is FULLY OPAQUE (no transparency)
            layer[:, :, 3] = 255

            print(f"   Layer {i+1} (Background): OPAQUE with blurred fill for removed foreground")
        else:
            # Other layers use standard alpha transparency
            layer = img_array.copy()
            layer[:, :, 3] = mask_feathered  # Set alpha channel

        # Convert to PIL
        layer_img = Image.fromarray(layer, mode='RGBA')
        layers.append(layer_img)

        # Store metadata
        description = ["Background", "Midground", "Foreground"][min(i, 2)]
        layer_info.append({
            "name": f"Layer_{i+1}_{description.lower()}.png",
            "order": num_layers - i,  # Reverse order (furthest = 1, closest = num_layers)
            "depth_range": [range_start, range_end],
            "description": description,
            "coverage_percent": round(coverage, 1),
            "is_opaque": i == 0  # Only background is opaque
        })

        print(f"   Layer {i+1} ({description}): depth {range_start}-{range_end}, {coverage:.1f}% coverage")

    print(f"✅ {num_layers} layers created in {time.time() - start:.2f}s")
    return layers, layer_info


def save_layer_manifest(layer_info, job_id):
    """Save layer metadata to JSON file."""
    manifest = {
        "job_id": job_id,
        "mode": "photo-realistic",
        "layer_count": len(layer_info),
        "layers": layer_info
    }

    manifest_path = OUTPUT_DIR / "layer_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"   Saved: {manifest_path}")
    return manifest_path


def main(input_image_path, num_layers=3, max_size=1024, export_layers=True, feather_radius=2, use_inpainting=False):
    """Main pipeline: Image -> Depth -> Layers (no AI transformation).

    Args:
        use_inpainting: If True, use AI inpainting for background (slower but higher quality).
                       If False, use Gaussian blur (10x faster, default).
    """
    print("=" * 60)
    print("🎨 Photo-Realistic Depth Layer Generator")
    print("=" * 60)

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
    depth_map, depth_array = generate_depth_map(image, depth_processor, depth_model)

    depth_path = OUTPUT_DIR / "02_depth_map.png"
    depth_map.save(depth_path)
    print(f"   Saved: {depth_path}")

    # Clear depth model from memory
    del depth_model, depth_processor
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()

    # Step 1.5: Detect subjects using semantic segmentation
    seg_processor, seg_model = load_segmentation_model()
    subject_mask, subject_count = detect_subjects_semantic(image, seg_processor, seg_model)

    # Clear segmentation model from memory
    del seg_model, seg_processor
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()

    # Step 1.6: Optionally inpaint background if subjects were detected
    inpainted_background = None
    if use_inpainting and subject_count > 0:
        # Use Stable Diffusion inpainting (highest quality, ~50s)
        print("\n✨ AI background fill enabled (Stable Diffusion)")
        inpaint_pipe = load_inpainting_model()
        inpainted_background = inpaint_background_sd(image, subject_mask, inpaint_pipe)

        # Clear inpainting model from memory
        del inpaint_pipe
        if device.type == "mps":
            torch.mps.empty_cache()
        elif device.type == "cuda":
            torch.cuda.empty_cache()

        # Save inpainted background for reference
        inpainted_bg_path = OUTPUT_DIR / "02b_inpainted_background.png"
        inpainted_background.save(inpainted_bg_path)
        print(f"   Saved: {inpainted_bg_path}")
    elif not use_inpainting and subject_count > 0:
        print("\n💨 Using fast Gaussian blur for background (use_inpainting=False)")

    print(f"\n💾 Saving outputs...")

    # Save composite (full image with alpha)
    composite_path = OUTPUT_DIR / "03_composite_full.png"
    image.save(composite_path)
    print(f"   Saved: {composite_path}")

    # Conditionally export layers
    if export_layers:
        # Step 2: Separate into layers with subject-aware processing
        layers, layer_info = separate_into_layers(image, depth_array, num_layers, subject_mask, feather_radius, inpainted_background)

        # Step 3: Save individual layers
        for i, (layer, info) in enumerate(zip(layers, layer_info)):
            layer_path = OUTPUT_DIR / info["name"]
            layer.save(layer_path)
            print(f"   Saved: {layer_path} (depth: {info['depth_range']})")

        # Step 4: Save manifest
        manifest_path = save_layer_manifest(layer_info, "photorealistic_test")
    else:
        print(f"   Skipping layer export (export_layers=False)")
        layers = []
        layer_info = []
        manifest_path = None

    # Summary
    print("\n" + "=" * 60)
    print("✅ PHOTO-REALISTIC LAYER SEPARATION COMPLETE!")
    print("=" * 60)
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"  - Original: {original_path.name}")
    print(f"  - Depth Map: {depth_path.name}")
    print(f"  - Composite: {composite_path.name}")
    for info in layer_info:
        print(f"  - {info['name']} ({info['description']})")
    print(f"  - layer_manifest.json")
    print("\n📝 Note: Stack these layers on glass/acrylic with spacers for 3D effect!")
    print("         Original photo quality is preserved (no AI transformation)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python poc_photorealistic.py <input_image_path> [num_layers] [max_size] [export_layers] [feather_radius] [use_inpainting]")
        print("\nExample:")
        print("  python poc_photorealistic.py test_photo.jpg")
        print("  python poc_photorealistic.py test_photo.jpg 4 1024 true 2 false  # Fast (default)")
        print("  python poc_photorealistic.py test_photo.jpg 4 1024 true 2 true   # High quality (10x slower)")
        print("  python poc_photorealistic.py test_photo.jpg 4 512 true 3  # Fast preview with 3px feathering")
        print("  python poc_photorealistic.py test_photo.jpg 3 1024 false 2  # No layer export")
        sys.exit(1)

    input_path = sys.argv[1]
    num_layers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    export_layers = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
    feather_radius = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    use_inpainting = sys.argv[6].lower() == 'true' if len(sys.argv) > 6 else False

    if num_layers < 2 or num_layers > 5:
        print("❌ Number of layers must be between 2 and 5")
        sys.exit(1)

    if max_size < 256 or max_size > 2048:
        print("❌ max_size must be between 256 and 2048")
        sys.exit(1)

    if feather_radius < 1 or feather_radius > 5:
        print("❌ feather_radius must be between 1 and 5")
        sys.exit(1)

    main(input_path, num_layers, max_size, export_layers, feather_radius, use_inpainting)
