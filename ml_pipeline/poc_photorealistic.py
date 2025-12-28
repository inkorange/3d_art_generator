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


def separate_into_layers(image, depth_array, num_layers=3):
    """
    Separate image into depth-based layers with alpha transparency.
    Uses adaptive percentile-based thresholding for better distribution.

    IMPORTANT: Background layer (Layer 1) is fully opaque with blurred fallback
    to prevent transparent holes when viewed from angles in physical prints.
    """
    print(f"\n🔪 Separating into {num_layers} depth layers...")
    start = time.time()

    # Convert image to RGBA
    image_rgba = image.convert("RGBA")
    img_array = np.array(image_rgba)

    # Create blurred version for background layer fallback
    img_rgb = np.array(image.convert("RGB"))
    blurred_img = cv2.GaussianBlur(img_rgb, (21, 21), 10)  # Heavy blur for fallback

    layers = []
    layer_info = []

    # IMPROVED: Use percentile-based thresholding for better distribution
    # This ensures each layer gets a more even distribution of pixels
    percentiles = np.linspace(0, 100, num_layers + 1)
    thresholds = np.percentile(depth_array, percentiles)

    print(f"   Depth distribution analysis:")
    print(f"   Min: {depth_array.min()}, Max: {depth_array.max()}")
    print(f"   Percentile thresholds: {[int(t) for t in thresholds]}")

    for i in range(num_layers):
        # Use percentile-based ranges instead of equal bins
        range_start = int(thresholds[i])
        range_end = int(thresholds[i + 1])

        # For last layer, include the max value
        if i == num_layers - 1:
            mask = ((depth_array >= range_start) & (depth_array <= range_end)).astype(np.uint8) * 255
        else:
            mask = ((depth_array >= range_start) & (depth_array < range_end)).astype(np.uint8) * 255

        # Calculate coverage for reporting
        coverage = (mask > 0).sum() / mask.size * 100

        # Apply feathering (Gaussian blur on mask)
        feather_radius = 2  # 2-pixel feather
        mask_feathered = cv2.GaussianBlur(mask, (5, 5), feather_radius)

        # SPECIAL HANDLING FOR BACKGROUND LAYER (Layer 1)
        if i == 0:  # Background layer
            # Start with blurred image as base
            layer = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
            layer[:, :, :3] = blurred_img  # Use blurred image as base

            # Apply extra smoothing to the blend mask for smoother transitions
            # This creates a gradual blend between sharp background and blur
            blend_feather_radius = 10  # Much larger feather for smooth transition
            mask_blend = cv2.GaussianBlur(mask_feathered, (21, 21), blend_feather_radius)

            # Overlay sharp background where mask is active
            mask_3d = np.stack([mask_blend] * 3, axis=2) / 255.0
            layer[:, :, :3] = (
                layer[:, :, :3] * (1 - mask_3d) +  # Blurred regions
                img_array[:, :, :3] * mask_3d       # Sharp background regions
            ).astype(np.uint8)

            # Background layer is FULLY OPAQUE (no transparency)
            layer[:, :, 3] = 255

            print(f"   Layer {i+1} (Background): OPAQUE with blurred fallback")
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


def main(input_image_path, num_layers=3):
    """Main pipeline: Image -> Depth -> Layers (no AI transformation)."""
    print("=" * 60)
    print("🎨 Photo-Realistic Depth Layer Generator")
    print("=" * 60)

    # Load input image
    print(f"\n📂 Loading input image: {input_image_path}")
    image = Image.open(input_image_path).convert("RGB")

    # Resize to reasonable size for processing
    max_size = 1024
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

    # Step 2: Separate into layers (NO AI transformation - use original photo)
    layers, layer_info = separate_into_layers(image, depth_array, num_layers)

    # Step 3: Save composite (full image with alpha)
    composite_path = OUTPUT_DIR / "03_composite_full.png"
    image.save(composite_path)
    print(f"\n💾 Saving outputs...")
    print(f"   Saved: {composite_path}")

    # Step 4: Save individual layers
    for i, (layer, info) in enumerate(zip(layers, layer_info)):
        layer_path = OUTPUT_DIR / info["name"]
        layer.save(layer_path)
        print(f"   Saved: {layer_path} (depth: {info['depth_range']})")

    # Step 5: Save manifest
    manifest_path = save_layer_manifest(layer_info, "photorealistic_test")

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
        print("Usage: python poc_photorealistic.py <input_image_path> [num_layers]")
        print("\nExample:")
        print("  python poc_photorealistic.py test_photo.jpg")
        print("  python poc_photorealistic.py test_photo.jpg 4")
        sys.exit(1)

    input_path = sys.argv[1]
    num_layers = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    if num_layers < 2 or num_layers > 5:
        print("❌ Number of layers must be between 2 and 5")
        sys.exit(1)

    main(input_path, num_layers)
