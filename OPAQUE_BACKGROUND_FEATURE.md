# Opaque Background Layer Feature

## Problem Solved

When printing depth-separated layers on glass/acrylic for physical 3D assembly, transparent "holes" in the background layer can be visible when viewing from angles, creating an unfinished look.

## Solution

**Background Layer (Layer 1) is now fully opaque** with intelligent blurred fallback:

- **Sharp background regions** - Where the depth map identifies actual background content
- **Blurred fallback** - Where foreground/midground would normally create transparency
- **100% opaque** - No transparent holes anywhere

## How It Works

### Layer 1 (Background) - OPAQUE
```
1. Start with heavily blurred version of entire image (21x21 Gaussian blur)
2. Overlay sharp background content where depth map indicates background
3. Result: Sharp background + blurred fill = fully opaque image
4. Alpha channel = 255 (fully opaque) everywhere
```

### Layers 2-N (Foreground/Midground) - TRANSPARENT
```
1. Normal alpha transparency based on depth mask
2. Transparent where not part of this layer
3. Sharp content where part of this layer
```

## Example

**Beach scene with 4 layers:**

### Before (Old Approach)
```
Layer 1 (Background): Sky is sharp, but where sand/water would be = TRANSPARENT HOLES
Layer 2 (Midground): Water/distant beach (transparent background)
Layer 3 (Foreground): Mid-range elements (transparent background)
Layer 4 (Foreground): Closest elements (transparent background)
```
**Problem:** Looking at Layer 1 from the side shows empty transparent regions

### After (New Approach)
```
Layer 1 (Background): Sky is sharp, sand/water areas = BLURRED FALLBACK (opaque)
Layer 2 (Midground): Water/distant beach (transparent background)
Layer 3 (Foreground): Mid-range elements (transparent background)
Layer 4 (Foreground): Closest elements (transparent background)
```
**Solution:** Layer 1 is completely solid - no holes when viewed from any angle!

## Physical Print Assembly

When stacked:
1. **Back glass** - Layer 1 (opaque background with blur)
2. **Spacer** (3-5mm)
3. **Mid glass** - Layer 2 (transparent, shows through to blurred background)
4. **Spacer** (3-5mm)
5. **Front glass** - Layers 3-4 (transparent, override blur with sharp content)

**Final result:**
- From front: Sharp, complete image (foreground layers override background blur)
- From angles: No transparent holes, professional finish
- Physical depth: 3D effect from layer separation

## Technical Details

### Blur Parameters
```python
blurred_img = cv2.GaussianBlur(img_rgb, (21, 21), 10)
```
- **Kernel:** 21x21 pixels (heavy blur)
- **Sigma:** 10 (strong smoothing)
- **Purpose:** Creates soft, non-distracting fill for non-background regions

### Alpha Blending
```python
# Sharp background regions
mask_3d = np.stack([mask_feathered] * 3, axis=2) / 255.0
layer[:, :, :3] = (
    layer[:, :, :3] * (1 - mask_3d) +  # Blurred fallback
    img_array[:, :, :3] * mask_3d       # Sharp background
).astype(np.uint8)

# Fully opaque
layer[:, :, 3] = 255
```

### Manifest Indicator
```json
{
  "name": "Layer_1_background.png",
  "is_opaque": true  // Only background layer has this flag
}
```

## Benefits

✅ **Professional finish** - No transparent holes in physical prints
✅ **Viewing from angles** - Background always looks complete
✅ **Stacking works perfectly** - Foreground layers override blur
✅ **Print-ready** - No manual post-processing needed
✅ **Automatic** - No user configuration required

## Visual Comparison

### Layer 1 Content

**Old approach:**
```
████████████████  (sharp sky)
░░░░░░░░░░░░░░░░  (transparent - where water would be)
░░░░░░░░░░░░░░░░  (transparent - where sand would be)
```

**New approach:**
```
████████████████  (sharp sky)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  (blurred water fallback)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  (blurred sand fallback)
```

When Layers 2-4 are stacked on top:
```
████████████████  (sharp sky from Layer 1)
████████████████  (sharp water from Layer 2, overrides blur)
████████████████  (sharp sand from Layers 3-4, overrides blur)
```

**Result:** Perfect sharp image with no holes!

## Implementation Status

✅ **Implemented in:** `ml_pipeline/poc_photorealistic.py`
✅ **Tested on:** Beach, Charlie, Landscape, Spaceship photos
✅ **Manifest support:** `is_opaque` flag in layer metadata
✅ **Automatic:** Works for all layer counts (3-5 layers)

## Future Enhancements

Potential improvements (Phase 4+):
- [ ] Adjustable blur strength (user preference)
- [ ] Content-aware inpainting instead of blur (more realistic fill)
- [ ] Smart blur that matches background texture
- [ ] Option to disable for artistic purposes

## Usage

No changes needed - this feature is **automatic** for all photo-realistic layer exports:

```bash
# Background layer is automatically opaque with blur
python ml_pipeline/poc_photorealistic.py your_photo.jpg 4
```

The `Layer_1_background.png` will always be fully opaque with blurred fallback.
