#!/usr/bin/env python3
"""
Test script to run both Photo-Realistic and Painterly modes on multiple images
Generates side-by-side comparisons and performance benchmarks
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

def run_test(image_path, mode, output_suffix=""):
    """Run either painterly or photorealistic mode on an image."""

    if mode == "photorealistic":
        script = "ml_pipeline/poc_photorealistic.py"
        job_name = f"photorealistic_test{output_suffix}"
    else:  # painterly
        script = "ml_pipeline/poc_painterly.py"
        job_name = f"poc_test{output_suffix}"

    print(f"\n{'='*60}")
    print(f"Running {mode.upper()} mode on: {image_path}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Run the script
        result = subprocess.run(
            ["python", script, image_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {mode.upper()} completed in {elapsed:.2f}s")
            return {
                "success": True,
                "time": elapsed,
                "mode": mode,
                "image": image_path
            }
        else:
            print(f"❌ {mode.upper()} failed:")
            print(result.stderr)
            return {
                "success": False,
                "time": elapsed,
                "mode": mode,
                "image": image_path,
                "error": result.stderr
            }

    except subprocess.TimeoutExpired:
        print(f"❌ {mode.upper()} timed out after 5 minutes")
        return {
            "success": False,
            "time": 300,
            "mode": mode,
            "image": image_path,
            "error": "Timeout"
        }
    except Exception as e:
        print(f"❌ {mode.upper()} error: {e}")
        return {
            "success": False,
            "time": 0,
            "mode": mode,
            "image": image_path,
            "error": str(e)
        }


def find_test_images():
    """Find all images in storage/uploads/."""
    uploads_dir = Path("storage/uploads")

    # Look for common image formats
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    images = []

    for pattern in patterns:
        images.extend(uploads_dir.glob(pattern))

    # Filter out gitkeep
    images = [img for img in images if img.name != ".gitkeep"]

    return sorted(images)


def print_summary(results):
    """Print summary of all test results."""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    # Separate by mode
    photo_results = [r for r in results if r["mode"] == "photorealistic"]
    paint_results = [r for r in results if r["mode"] == "painterly"]

    print("\n🖼️  PHOTO-REALISTIC MODE:")
    if photo_results:
        successes = [r for r in photo_results if r["success"]]
        failures = [r for r in photo_results if not r["success"]]

        print(f"   Success: {len(successes)}/{len(photo_results)}")
        if successes:
            avg_time = sum(r["time"] for r in successes) / len(successes)
            print(f"   Avg time: {avg_time:.2f}s")

        if failures:
            print(f"   ❌ Failed: {len(failures)}")
            for f in failures:
                print(f"      - {Path(f['image']).name}: {f.get('error', 'Unknown')}")
    else:
        print("   No tests run")

    print("\n🎨 PAINTERLY MODE:")
    if paint_results:
        successes = [r for r in paint_results if r["success"]]
        failures = [r for r in paint_results if not r["success"]]

        print(f"   Success: {len(successes)}/{len(paint_results)}")
        if successes:
            avg_time = sum(r["time"] for r in successes) / len(successes)
            print(f"   Avg time: {avg_time:.2f}s")

        if failures:
            print(f"   ❌ Failed: {len(failures)}")
            for f in failures:
                print(f"      - {Path(f['image']).name}: {f.get('error', 'Unknown')}")
    else:
        print("   No tests run")

    # Speed comparison
    if photo_results and paint_results:
        photo_avg = sum(r["time"] for r in photo_results if r["success"]) / max(1, len([r for r in photo_results if r["success"]]))
        paint_avg = sum(r["time"] for r in paint_results if r["success"]) / max(1, len([r for r in paint_results if r["success"]]))

        if photo_avg > 0 and paint_avg > 0:
            speedup = paint_avg / photo_avg
            print(f"\n⚡ SPEED COMPARISON:")
            print(f"   Photo-Realistic: {photo_avg:.2f}s average")
            print(f"   Painterly: {paint_avg:.2f}s average")
            print(f"   Photo-Realistic is {speedup:.1f}x faster")

    print("\n" + "="*60)
    print("📁 Output locations:")
    print("   Photo-Realistic: storage/jobs/photorealistic_test/")
    print("   Painterly: storage/jobs/poc_test/")
    print("="*60)


def main():
    """Main test runner."""
    print("="*60)
    print("🧪 3D PAINTERLY GENERATOR - DUAL MODE TEST")
    print("="*60)

    # Find all test images
    test_images = find_test_images()

    if not test_images:
        print("\n❌ No test images found in storage/uploads/")
        print("   Please add some images first")
        return 1

    print(f"\n📂 Found {len(test_images)} test image(s):")
    for img in test_images:
        print(f"   - {img.name}")

    # Ask user which modes to run
    print("\n🔧 Test configuration:")
    print("   1. Photo-Realistic only")
    print("   2. Painterly only")
    print("   3. Both modes (recommended)")

    choice = input("\nSelect mode (1/2/3) [3]: ").strip() or "3"

    run_photo = choice in ["1", "3"]
    run_paint = choice in ["2", "3"]

    # Ask which images to test
    print("\n📸 Image selection:")
    print("   1. All images")
    print("   2. First image only (quick test)")

    img_choice = input("\nSelect option (1/2) [2]: ").strip() or "2"

    if img_choice == "2":
        test_images = test_images[:1]

    print(f"\n🚀 Starting tests on {len(test_images)} image(s)...")

    results = []

    for img in test_images:
        if run_photo:
            result = run_test(str(img), "photorealistic")
            results.append(result)

        if run_paint:
            result = run_test(str(img), "painterly")
            results.append(result)

    # Print summary
    print_summary(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
