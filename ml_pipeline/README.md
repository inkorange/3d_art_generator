# ML Pipeline - Phase 1

## Proof of Concept Script

This directory contains the Phase 1 proof-of-concept implementation for the 3D Painterly Image Generator.

### What It Does

The `poc_painterly.py` script demonstrates the core ML pipeline:

1. **Load Input Image** - Accepts any photo (JPEG/PNG)
2. **Generate Depth Map** - Uses MiDaS DPT to extract depth information
3. **Generate Painterly Output** - Uses Stable Diffusion 1.5 img2img to create artistic version

### Requirements

- Python 3.9+
- Virtual environment activated
- Dependencies installed (see main README)

### Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Basic usage
python ml_pipeline/poc_painterly.py path/to/your/photo.jpg

# With custom parameters
python ml_pipeline/poc_painterly.py photo.jpg "watercolor" 0.6 123
```

### Parameters

- `input_image_path` - Path to input photo (required)
- `style` - Style description (default: "oil painting")
- `strength` - How much to transform (0.0-1.0, default: 0.5)
- `seed` - Random seed for reproducibility (default: 42)

### Outputs

All outputs are saved to `storage/jobs/poc_test/`:

- `01_original.png` - Resized input image
- `02_depth_map.png` - Grayscale depth map
- `03_painterly_output.png` - Final painterly result

### Performance (Apple Silicon)

Expected processing times on Mac:
- Depth map: 3-5 seconds
- Painterly generation: 30-60 seconds
- **Total: ~1 minute per image**

### First Run

On first run, the script will download models (~4-5GB total):
- MiDaS DPT: ~400MB
- Stable Diffusion 1.5: ~4GB

Models are cached in `~/.cache/huggingface/` for reuse.

### Optimizations for Mac

- Uses MPS (Metal Performance Shaders) for GPU acceleration
- Attention slicing enabled for memory efficiency
- Reduced to 30 inference steps (vs 50 standard)
- Resizes images to max 768px for processing

### Next Steps (Phase 2+)

- [ ] Add ControlNet depth conditioning
- [ ] Integrate into FastAPI backend
- [ ] Add batch processing
- [ ] Implement layer separation
- [ ] High-resolution upscaling

### Troubleshooting

**Memory errors on Mac:**
- Close other applications
- Reduce image size further (edit `max_size = 768` to `512`)
- Reduce inference steps (edit `num_inference_steps=30` to `20`)

**Slow generation:**
- This is normal on Mac (30-60s per image)
- NVIDIA GPUs are ~10x faster
- Consider reducing steps for faster iteration

**Model download fails:**
- Check internet connection
- May need to accept Hugging Face terms for SD 1.5
- Try manually: `huggingface-cli login`
