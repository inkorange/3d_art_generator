# 3D Painterly Image Generator
## Project Vision

Build a local software tool that generates high-definition 3D painterly images from photo references, suitable for print production. The tool will use depth estimation, generative AI, and controlled randomness to create unique artistic interpretations with a 3D feel.

**Key Requirements:**
- Local-only deployment (no cloud hosting)
- Web-based UI for ease of use
- Print-quality output (300-600 DPI, up to 20k pixels wide)
- Deterministic generation (reproducible results via seeds)
- **Depth layer separation for physical 3D assembly** (glass prints, layered frames)
- Artistic iteration with style presets

---

## Technology Stack (Mac Apple Silicon Optimized)

### Frontend
- **Next.js** (App Router) with TypeScript
- **Tailwind CSS** for styling
- **React** for upload/preview interface

### Backend Orchestration
- **FastAPI** (Python) for API layer
- **SQLite** for job metadata (simpler than PostgreSQL for local use)
- **Local filesystem** for storage (no S3 needed for local-only)
- **Python multiprocessing** for job queue (no Redis needed initially)

### ML/Generation Layer
- **Python 3.10+** with Apple Silicon optimizations
- **PyTorch** with MPS (Metal Performance Shaders) backend
- **Diffusers** library (Hugging Face) for Stable Diffusion
- **ControlNet** for structure preservation
- **MiDaS** or **ZoeDepth** for depth estimation
- **Pillow** + **OpenCV** for image processing

### Important Mac-Specific Constraints
- Apple Silicon uses **MPS** (not CUDA) - compatible but slower
- **SDXL** may be too heavy - will use **SD 1.5 or SD 2.1** instead
- **8-16GB RAM models** (vs 24GB VRAM on NVIDIA)
- Generation times: **30-120 seconds** per image (vs 5-15s on RTX 4090)
- **ComfyUI** or **DiffusionBee** as fallback if custom pipeline too complex

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│          Web UI (Next.js)                   │
│  - Upload images                            │
│  - Set parameters (sliders)                 │
│  - View preview                             │
│  - Download high-res output                 │
└──────────────┬──────────────────────────────┘
               │ HTTP (localhost:3000)
               ▼
┌─────────────────────────────────────────────┐
│     Backend API (FastAPI)                   │
│  - Job queue management                     │
│  - Parameter validation                     │
│  - Job status tracking                      │
│  - File management                          │
└──────────────┬──────────────────────────────┘
               │ Python subprocess
               ▼
┌─────────────────────────────────────────────┐
│   GPU Worker (Python + PyTorch MPS)         │
│  1. Depth estimation                        │
│  2. Mode selection:                         │
│     A. Photo-Realistic → Skip to step 4    │
│     B. Painterly → Continue to step 3       │
│  3. Stable Diffusion img2img (Painterly)    │
│  4. Layer separation (depth-based)          │
│  5. Post-processing effects                 │
│  6. High-res upscaling                      │
└─────────────────────────────────────────────┘
               │
               ▼
     outputs/ directory (Layered PNGs)
```

---

## Core Pipeline Details

### 1. Image Ingestion
**Input:** User-uploaded JPEG/PNG
**Process:**
- Validate file format and size
- Convert to RGB color space
- Resize for processing (longest side = 768-1024px for Mac)
- Store original unmodified
- Generate unique `job_id`

**Tools:** Pillow, FastAPI file upload

---

### 2. Depth Map Generation
**Input:** Normalized input image
**Process:**
- Run MiDaS depth estimation model
- Output grayscale depth map (0-255)
- Apply Gaussian smoothing
- Save depth map for reuse

**Model:** `intel-isl/MiDaS` (small variant for speed)
**Output:** `{job_id}_depth.png`

**Why:** Enables 3D-aware effects, brush size variation, and future parallax

---

### 3. Structure Conditioning (ControlNet Preprocessing)
**Input:** Normalized image + depth map
**Process:**
- Generate Canny edge map
- Optional: Extract normal maps from depth
- Prepare ControlNet conditioning tensors

**Purpose:** Preserve composition and perspective during painterly transformation

---

### 4. Image Processing (Two Modes)

#### Mode A: Photo-Realistic (No AI Transformation)
**Process:**
- Skip Stable Diffusion entirely
- Use original high-quality photo as-is
- Apply optional sharpening/enhancement filters
- Proceed directly to layer separation using depth map

**Benefits:**
- **Much faster** (~5-10 seconds vs 30-60 seconds)
- Preserves photo details perfectly
- Ideal for family photos, portraits, product photography
- No randomness/seeds needed

**Use Case:** User wants 3D depth effect on glass but wants to keep the original photo quality (e.g., family portrait)

---

#### Mode B: Painterly Generation (Stable Diffusion)
**Model:** Stable Diffusion 1.5 or 2.1 (SDXL too heavy for Mac)
**Mode:** Image-to-image with ControlNet
**Key Parameters:**
- `strength` (denoising): 0.3-0.7 (higher = more painterly)
- `guidance_scale`: 7-12
- `seed`: User-controllable for reproducibility
- `negative_prompt`: "photorealistic, photo, camera, lens"
- `prompt`: "oil painting, impressionist, painterly, artistic, brushstrokes"

**ControlNet Models:**
- `lllyasviel/control_v11p_sd15_depth`
- `lllyasviel/control_v11p_sd15_canny`

**Controlled Randomness:**
- Base seed + layer offsets
- Depth-weighted noise (more variation in background)
- Seed jitter for "editions"

**Use Case:** User wants artistic interpretation for decorative prints

---

### 5. Post-Processing Enhancements
**Techniques:**
- **Brush stroke simulation** (directional bilateral filtering)
- **Color harmonization** (LAB color space adjustment)
- **Edge softening** (selective Gaussian blur)
- **Texture overlay** (optional canvas/paper texture)

**Tools:** OpenCV, Pillow, custom Python filters

---

### 6. High-Resolution Upscaling
**Strategy:**
- Generate base image at 768-1024px
- Tile-based upscaling to avoid memory issues
- Use Real-ESRGAN or diffusion-based upscaling

**Mac Constraints:**
- Upscale in **2x stages** (768 → 1536 → 3072 → 6144)
- Expect **5-10 minutes** per upscale pass
- May need to offload to external GPU service for 10k+ resolution

**Output Formats:**
- 16-bit PNG for archival
- 8-bit JPEG for preview
- Optional TIFF for print workflow

**Target:** 300 DPI at 24"x36" = 7200x10800 pixels

---

### 7. Depth Layer Separation (Physical 3D Assembly)

This is a **core feature** that separates the generated painterly image into depth-based layers for physical 3D printing (glass prints, acrylic layers, shadow boxes).

**Input:** Generated painterly image + depth map

**Process:**
1. Analyze depth map to identify natural depth breaks
2. Automatically separate into 2-5 layers based on depth distribution
3. Apply transparency/alpha channel to each layer
4. Apply subtle edge feathering to alpha masks (1-3 pixel gradient)
5. Export layers as separate PNG files with alpha

**Layer Strategy:**
- **Automatic depth-based clustering** using depth map histogram
- Variable layer count (2-5) based on image complexity
- Foreground objects on front layer, background on back layer
- Layers named sequentially: `Layer_1_front.png`, `Layer_2_mid.png`, `Layer_3_back.png`

**Output Format:**
```
outputs/{job_id}/
├── composite_full.png           # Full painterly image
├── depth_map.png                # Grayscale depth reference
├── Layer_1_front.png            # Closest layer (with alpha)
├── Layer_2_mid.png              # Middle layer(s) - optional
├── Layer_3_back.png             # Farthest layer (with alpha)
└── layer_manifest.json          # Layer metadata
```

**Layer Manifest Example:**
```json
{
  "job_id": "uuid",
  "layer_count": 3,
  "layers": [
    {
      "name": "Layer_1_front.png",
      "order": 1,
      "depth_range": [0, 85],
      "description": "Foreground objects"
    },
    {
      "name": "Layer_2_mid.png",
      "order": 2,
      "depth_range": [85, 170],
      "description": "Middle distance"
    },
    {
      "name": "Layer_3_back.png",
      "order": 3,
      "depth_range": [170, 255],
      "description": "Background elements"
    }
  ]
}
```

**Technical Implementation:**
- Use k-means clustering or histogram analysis on depth map
- Threshold-based segmentation with feathered edges (Gaussian blur on alpha masks)
- Configurable feather radius (1-3 pixels default, adjustable in advanced settings)
- PNG with full alpha channel support
- All layers same resolution as final output

**UI Control:**
- Checkbox: "Export depth layers for 3D assembly"
- When enabled, generates both composite + separated layers
- Preview shows layer separation overlay

**Use Cases:**
- Layered glass/acrylic prints (e.g., 3-5 glass panes separated by spacers)
- Shadow box frames with physical depth
- Lenticular printing with depth information
- Multi-plane parallax displays

---

## User Interface Controls

### Upload Section
- Drag-and-drop or file picker
- Preview uploaded image
- Display dimensions and size

### Generation Mode
**Primary Choice** (affects entire pipeline):

| Feature | Photo-Realistic Mode | Painterly Mode |
|---------|---------------------|----------------|
| **AI Transformation** | None | Stable Diffusion img2img |
| **Processing Time** | ~10 seconds | ~60 seconds |
| **Output Quality** | Original photo quality | Artistic interpretation |
| **Style Controls** | Disabled | Enabled (presets, strength, etc.) |
| **Randomness** | Not applicable | Seed-controlled |
| **Best For** | Family photos, portraits, product shots | Decorative art, creative prints |
| **Layer Output** | ✅ Yes (depth-based) | ✅ Yes (depth-based) |

**Both modes** support:
- Depth layer separation for 3D assembly
- High-resolution upscaling
- Batch generation (1-3 variations)
- Same export formats (PNG/TIFF/CMYK)

### Style Parameters (Painterly Mode Only)
| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| Painterliness | 0.2-0.8 | 0.5 | Denoising strength |
| Depth Influence | 0.0-1.0 | 0.6 | ControlNet depth weight |
| Brush Scale | 1-5 | 3 | Post-process stroke size |
| Randomness | 0-100 | 42 | Seed value |
| Style Preset | Dropdown | Oil Impressionist | Prompt + LoRA selection |

**Note:** Style parameters are hidden/disabled in Photo-Realistic Mode

### Style Presets (Painterly Mode Only)
- **Oil Impressionist** (Monet, Renoir)
- **Watercolor Loose** (Turner, Sargent)
- **Palette Knife Thick** (Van Gogh)
- **Pastel Soft** (Degas)
- **Custom** (manual prompt entry)

### Output Settings
- Resolution preset (8x10", 16x20", 24x36")
- DPI (300/600)
- Format (PNG/TIFF/CMYK TIFF)
- **Depth layer export:** Checkbox "Export layers for 3D assembly"
  - When enabled: Exports composite + separated depth layers
  - Auto-determines layer count (2-5) based on depth complexity

### Batch Generation (Optional)
- **Default:** 1 image (fastest feedback)
- **Range:** 1-3 variations max
- **UI:** Number input or +/- buttons
- **Behavior:** Uses sequential seeds (base_seed + 0, +1, +2)
- **Display:** Side-by-side preview of all variations
- **Download:** Individual downloads per variation
- **Note:** User can always re-render for more options

---

## Data Flow & Storage

### Directory Structure
```
3d_art_generator/
├── frontend/              # Next.js app
├── backend/               # FastAPI app
├── ml_pipeline/           # Python generation scripts
├── models/                # Downloaded ML models
├── storage/
│   ├── uploads/           # Original images
│   ├── jobs/              # Per-job working directory
│   │   └── {job_id}/
│   │       ├── input.png
│   │       ├── depth.png
│   │       ├── edges.png
│   │       ├── base_output.png
│   │       ├── final_highres.png
│   │       └── params.json
│   └── outputs/           # Final deliverables
└── database.sqlite        # Job metadata
```

### Job Record Schema
```json
{
  "job_id": "uuid",
  "created_at": "timestamp",
  "status": "pending|processing|completed|failed",
  "input_path": "storage/uploads/xyz.jpg",
  "parameters": {
    "strength": 0.5,
    "depth_weight": 0.6,
    "brush_scale": 3,
    "seed": 42,
    "style_preset": "oil-impressionist",
    "resolution": "16x20",
    "dpi": 300
  },
  "outputs": {
    "depth_map": "storage/jobs/{id}/depth.png",
    "base_result": "storage/jobs/{id}/base_output.png",
    "final_highres": "storage/outputs/{id}_final.png"
  },
  "error": null
}
```

---

## Development Phases

### Phase 1: Foundation & Proof of Concept (Week 1-2)
**Goal:** Validate that the ML pipeline works on Apple Silicon

**Tasks:**
1. Set up Python environment with MPS support
2. Install PyTorch, Diffusers, Transformers
3. Download and test SD 1.5 model
4. Create simple script: image → depth map → img2img → output
5. Verify performance benchmarks (time per generation)
6. Test ControlNet depth integration

**Deliverable:** Single Python script that takes photo, generates painterly version

**Success Criteria:**
- Generates 768px image in <60 seconds
- Depth map visibly influences output
- Results look painterly (not photorealistic)

---

### Phase 2: Backend API & Job Queue (Week 2-3)
**Goal:** Build FastAPI backend with job management

**Tasks:**
1. Initialize FastAPI project structure
2. Create SQLite database schema
3. Implement job CRUD endpoints:
   - `POST /api/upload` - Accept image file
   - `POST /api/jobs` - Create generation job
   - `GET /api/jobs/{id}` - Get job status
   - `GET /api/jobs/{id}/result` - Download result
4. Implement simple queue (Python multiprocessing)
5. Integrate Phase 1 ML script as worker
6. Add error handling and logging

**Deliverable:** Working API that accepts images and generates results

**Testing:** Use `curl` or Postman to submit jobs

---

### Phase 3: Frontend UI (Week 3-4)
**Goal:** Build Next.js interface for easy interaction

**Tasks:**
1. Initialize Next.js project with TypeScript
2. Create upload page with drag-and-drop
3. Build parameter control panel (sliders)
4. Implement job status polling
5. Add preview/download functionality
6. Style with Tailwind CSS
7. Connect to FastAPI backend (CORS setup)

**Deliverable:** Polished web UI running on `localhost:3000`

**UX Flow:**
1. User uploads image → sees preview
2. Adjusts sliders → sees parameter values
3. Clicks "Generate" → sees progress spinner
4. Job completes → preview appears
5. Downloads high-res file

---

### Phase 4: Depth Layer Separation (Week 4)
**Goal:** Implement automatic depth-based layer separation for 3D assembly

**Tasks:**
1. Implement depth histogram analysis to determine optimal layer count
2. Create k-means or threshold-based segmentation algorithm
3. Generate alpha-masked layers with feathered edges (Gaussian blur)
4. Implement configurable feather radius (default 1-3 pixels)
5. Export layer files with sequential naming
6. Create layer manifest JSON with metadata
7. Add UI checkbox for layer export toggle
8. Test with various image types (portraits, landscapes, complex scenes)

**Deliverable:** Depth layer export functionality

**Testing:** Generate layers, verify transparency, confirm stack recreates full image

---

### Phase 5: Advanced ML Features (Week 5)
**Goal:** Improve artistic quality and control

**Tasks:**
1. Add ControlNet Canny edge conditioning
2. Implement custom post-processing filters:
   - Directional stroke simulation
   - Color harmonization
   - Edge softening
3. Create style presets (prompt templates)
4. Add depth-weighted randomness
5. Implement seed jitter for variations
6. Fine-tune default parameters

**Deliverable:** Noticeably better artistic results

**Testing:** Generate same image with different presets, compare quality

---

### Phase 6: High-Resolution Pipeline (Week 6)
**Goal:** Enable print-quality output

**Tasks:**
1. Research Mac-compatible upscaling options:
   - Real-ESRGAN (if MPS-compatible)
   - Diffusion-based upscaling (slower but higher quality)
   - Tile-based approach for memory efficiency
2. Implement staged 2x upscaling
3. Add seam blending for tiled upscaling
4. Create 16-bit PNG export
5. Add resolution presets (8x10, 16x20, 24x36)
6. Test full pipeline: upload → generate → upscale → download
7. **Apply upscaling to depth layers** when layer export enabled

**Deliverable:** Ability to export 6000+ pixel images (composite + layers)

**Warning:** This phase may hit hardware limits. May need cloud GPU for 10k+ images.

---

### Phase 7: Polish & Optimization (Week 7)
**Goal:** Production-ready tool for personal use

**Tasks:**
1. Add job history view in UI
2. Implement result gallery
3. Add "regenerate with different seed" button
4. Optimize model loading (keep models in memory)
5. Add progress indicators (step-by-step feedback)
6. Create user documentation
7. Add error recovery (retry failed jobs)
8. Implement cleanup (delete old jobs)

**Deliverable:** Reliable, user-friendly tool

---

### Phase 8 (Optional): Advanced 3D Features
**Goal:** Experimental depth effects beyond layer separation

**Tasks:**
1. Experiment with Gaussian splatting
2. Generate depth-aware parallax animations
3. Re-render from offset camera angles
4. Create stereoscopic outputs (for lenticular prints)
5. Depth-aware inpainting (fill behind foreground objects)

**Note:** This is experimental and may not work well on Mac. Phase 4 already handles the core layer separation feature.

---

## Alternative Approach: ComfyUI Workflow

If custom coding becomes too complex, consider this hybrid approach:

**Use ComfyUI as the generation engine:**
- ComfyUI supports Apple Silicon natively
- Visual node-based workflow (less coding)
- Built-in ControlNet, upscaling, etc.
- Can be automated via API

**Custom Frontend Still Applies:**
- Next.js UI sends jobs to ComfyUI API
- Backend wraps ComfyUI calls
- User gets polished interface, not ComfyUI's technical UI

**Trade-off:**
- ✅ Faster to implement
- ✅ More stable (mature tool)
- ❌ Less customizable
- ❌ Requires learning ComfyUI workflow syntax

---

## Key Technical Decisions

### Why Not SDXL?
- Requires 12-16GB VRAM on NVIDIA
- Apple Silicon can run it but **very slowly** (2-5 minutes per image)
- SD 1.5 is **4x faster** with good quality for this use case

### Why Not Redis/PostgreSQL?
- Overkill for single-user local tool
- SQLite is file-based, no daemon needed
- Python multiprocessing sufficient for queue

### Why Not Cloud Deployment?
- Hosting GPU instances = ongoing cost
- Print files are large (100MB+)
- User wants local control and privacy

### Mac Performance Expectations
| Task | Time Estimate |
|------|---------------|
| Depth map generation | 3-5 seconds |
| SD 1.5 img2img (768px) | 30-60 seconds |
| Post-processing | 2-5 seconds |
| 2x upscale (1536px) | 45-90 seconds |
| **Total per image** | **2-3 minutes** |

For 10k+ pixel final output, expect **10-20 minutes total**.

---

## Project Requirements (Confirmed)

1. **Model Storage:** ✅ Sufficient disk space available for 15-20GB of models/LoRAs

2. **Memory:** ✅ 16GB RAM (meets minimum requirement)
   - Will use memory-efficient settings
   - May need to close other apps during generation
   - Consider attention slicing for larger images

3. **LoRA Strategy:** Use existing LoRAs from CivitAI/Hugging Face
   - No custom training needed initially
   - Curate collection of high-quality artistic styles
   - Can add custom training in future phases

4. **Print Export Options:** Both formats supported
   - **RGB PNG** (16-bit) - Default, widest compatibility
   - **CMYK TIFF** - Optional export for professional print services
   - User selects format in UI before download

5. **Batch Processing:** Simple approach
   - **Default:** 1 image per generation
   - **Max:** 3 variations at once
   - **Use case:** Quick comparison, can always re-render
   - **UI:** Number selector (1, 2, or 3)

6. **Settings Persistence:** ✅ Yes
   - Save user's last-used parameters
   - Named preset system ("My Oil Style", "Sunset Watercolor")
   - Export/import preset files for backup

---

## Success Metrics

**MVP Success:**
- ✅ Upload photo, download painterly version in <5 minutes
- ✅ Recognizable as artistic, not photo filter
- ✅ Depth influence visible (foreground/background separation)
- ✅ Reproducible results (same seed = same output)

**Production Success:**
- ✅ Generate 300 DPI print-ready files (6000+ pixels)
- ✅ <15 minute total pipeline (including upscaling)
- ✅ Multiple style presets available
- ✅ Reliable error handling (no crashes)
- ✅ **Depth layer separation working** (2-5 layers with transparency)
- ✅ **Layers stack to recreate full image** (no gaps or misalignment)

---

## Next Steps

1. **Immediate:** Validate ML models run on your Mac (Phase 1)
2. **Week 1:** Complete proof-of-concept script
3. **Week 2:** Build backend API
4. **Week 3:** Build frontend UI
5. **Iterate:** Improve quality in Phases 4-6

**First Command to Run:**
```bash
python3 -m pip install torch torchvision torchaudio
python3 -c "import torch; print(torch.backends.mps.is_available())"
```
If this prints `True`, you're ready to start Phase 1.
