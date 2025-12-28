#!/usr/bin/env python3
"""
Test setup script - Validates environment and downloads test image
"""

import sys
import torch
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path

def check_environment():
    """Verify environment is set up correctly."""
    print("🔍 Checking environment setup...")
    print()

    # Check Python version
    py_version = sys.version_info
    print(f"✅ Python: {py_version.major}.{py_version.minor}.{py_version.micro}")

    # Check PyTorch
    print(f"✅ PyTorch: {torch.__version__}")

    # Check MPS availability
    if torch.backends.mps.is_available():
        print("✅ MPS (Metal): Available")
        device = "mps"
    elif torch.cuda.is_available():
        print("✅ CUDA: Available")
        device = "cuda"
    else:
        print("⚠️  GPU: Not available (will use CPU)")
        device = "cpu"

    # Test MPS operation
    if device == "mps":
        try:
            x = torch.randn(100, 100, device=device)
            y = torch.matmul(x, x)
            torch.mps.synchronize()
            print("✅ MPS: Tensor operations working")
        except Exception as e:
            print(f"❌ MPS: Error - {e}")
            return False

    print()
    return True


def download_test_image():
    """Download a test landscape image."""
    print("📥 Downloading test image...")

    # Use a sample landscape from Unsplash (free to use)
    url = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))

        # Save to storage
        test_path = Path("storage/uploads/test_landscape.jpg")
        test_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(test_path)

        print(f"✅ Test image saved: {test_path}")
        print(f"   Size: {img.size}")
        print()
        return str(test_path)

    except Exception as e:
        print(f"❌ Failed to download test image: {e}")
        print("   You can manually add a test image to storage/uploads/")
        return None


def main():
    """Run all setup checks."""
    print("=" * 60)
    print("🧪 3D Painterly Generator - Setup Test")
    print("=" * 60)
    print()

    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return 1

    # Download test image
    test_image = download_test_image()

    if test_image:
        print("=" * 60)
        print("✅ Setup complete! Ready to run proof-of-concept")
        print("=" * 60)
        print()
        print("Next steps:")
        print(f"1. Run: source venv/bin/activate")
        print(f"2. Run: python ml_pipeline/poc_painterly.py {test_image}")
        print()
        print("Note: First run will download ML models (~4-5GB)")
        print("      This may take 5-10 minutes depending on internet speed")
        print()
        return 0
    else:
        print("⚠️  Could not download test image, but environment is ready")
        print("   Add your own image and run:")
        print("   python ml_pipeline/poc_painterly.py path/to/your/image.jpg")
        return 0


if __name__ == "__main__":
    sys.exit(main())
