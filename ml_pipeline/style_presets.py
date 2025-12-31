"""
Style Presets for Painterly Generation

Each preset includes:
- name: Display name for the UI
- description: What the style looks like
- base_prompt: Core artistic description
- negative_prompt: What to avoid
- recommended_strength: Default transformation strength
- recommended_steps: Number of inference steps
- recommended_guidance: Guidance scale
"""

from typing import Dict, Any


class StylePreset:
    """A single style preset configuration."""

    def __init__(
        self,
        name: str,
        description: str,
        base_prompt: str,
        negative_prompt: str,
        recommended_strength: float = 0.5,
        recommended_steps: int = 40,
        recommended_guidance: float = 7.0,
    ):
        self.name = name
        self.description = description
        self.base_prompt = base_prompt
        self.negative_prompt = negative_prompt
        self.recommended_strength = recommended_strength
        self.recommended_steps = recommended_steps
        self.recommended_guidance = recommended_guidance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "base_prompt": self.base_prompt,
            "negative_prompt": self.negative_prompt,
            "recommended_strength": self.recommended_strength,
            "recommended_steps": self.recommended_steps,
            "recommended_guidance": self.recommended_guidance,
        }


# Define all available style presets
STYLE_PRESETS = {
    "oil_painting": StylePreset(
        name="Oil Painting",
        description="Classic oil painting with thick brushstrokes and rich colors",
        base_prompt="masterpiece oil painting, thick impasto brushstrokes, smooth flowing paint, rich vibrant colors, professional artwork, classical technique, painterly aesthetic, expressive texture, beautiful composition",
        negative_prompt="photograph, photorealistic, digital art, pixelated, jagged edges, fragmented, distorted, deformed, ugly, bad composition, chaotic, flat colors, watermark, text",
        recommended_strength=0.5,
        recommended_steps=40,
        recommended_guidance=7.0,
    ),

    "watercolor": StylePreset(
        name="Watercolor",
        description="Soft watercolor with flowing washes and delicate details",
        base_prompt="beautiful watercolor painting, soft flowing washes, delicate brushwork, translucent colors, paper texture, artistic rendering, light and airy, elegant composition, gentle blending",
        negative_prompt="photograph, photorealistic, oil painting, thick paint, harsh edges, digital art, pixelated, oversaturated, muddy colors, watermark",
        recommended_strength=0.45,
        recommended_steps=35,
        recommended_guidance=7.5,
    ),

    "impressionist": StylePreset(
        name="Impressionist",
        description="Impressionist style with visible brushstrokes and vibrant light",
        base_prompt="impressionist masterpiece, visible brushstrokes, dappled light, vibrant colors, atmospheric perspective, loose painting technique, beautiful light and shadow, artistic interpretation",
        negative_prompt="photograph, photorealistic, sharp details, hard edges, digital art, flat colors, dark and muddy, chaotic composition",
        recommended_strength=0.55,
        recommended_steps=40,
        recommended_guidance=6.5,
    ),

    "acrylic": StylePreset(
        name="Acrylic Paint",
        description="Bold acrylic painting with strong colors and defined strokes",
        base_prompt="vibrant acrylic painting, bold brushstrokes, strong colors, smooth paint application, contemporary style, professional artwork, clean composition, expressive technique",
        negative_prompt="photograph, photorealistic, watercolor, oil painting, muddy colors, pixelated, distorted, ugly composition",
        recommended_strength=0.5,
        recommended_steps=40,
        recommended_guidance=7.0,
    ),

    "abstract_expressionist": StylePreset(
        name="Abstract Expressionist",
        description="Expressive abstract interpretation with bold gestural marks",
        base_prompt="abstract expressionist painting, bold gestural brushstrokes, expressive colors, dynamic composition, emotional energy, artistic interpretation, cohesive abstract forms, masterful technique",
        negative_prompt="photograph, photorealistic, realistic details, tight rendering, pixelated, chaotic mess, ugly, muddy",
        recommended_strength=0.7,
        recommended_steps=45,
        recommended_guidance=6.0,
    ),

    "pastel": StylePreset(
        name="Soft Pastel",
        description="Gentle pastel with soft blended edges and muted colors",
        base_prompt="soft pastel artwork, gentle blended strokes, muted harmonious colors, delicate texture, artistic rendering, peaceful composition, smooth transitions, beautiful light",
        negative_prompt="photograph, photorealistic, harsh colors, sharp edges, digital art, oversaturated, dark and muddy, watermark",
        recommended_strength=0.4,
        recommended_steps=35,
        recommended_guidance=7.5,
    ),

    "gouache": StylePreset(
        name="Gouache",
        description="Opaque gouache with flat colors and clean edges",
        base_prompt="beautiful gouache painting, opaque matte finish, flat vibrant colors, clean shapes, poster-like quality, artistic illustration, smooth application, professional technique",
        negative_prompt="photograph, photorealistic, oil painting, glossy, transparent, pixelated, messy, watermark",
        recommended_strength=0.5,
        recommended_steps=40,
        recommended_guidance=7.0,
    ),

    "palette_knife": StylePreset(
        name="Palette Knife",
        description="Thick textured paint applied with palette knife",
        base_prompt="palette knife painting, thick textured paint, bold impasto technique, sculptural brushwork, rich colors, dramatic texture, expressive application, masterful craftsmanship",
        negative_prompt="photograph, photorealistic, smooth painting, flat, thin paint, digital art, pixelated, watermark",
        recommended_strength=0.6,
        recommended_steps=45,
        recommended_guidance=6.5,
    ),

    "chinese_brush": StylePreset(
        name="Chinese Brush Painting",
        description="Traditional Chinese brush painting with flowing ink",
        base_prompt="traditional chinese brush painting, flowing ink, elegant brushwork, harmonious composition, artistic simplicity, beautiful negative space, masterful technique, zen aesthetic",
        negative_prompt="photograph, photorealistic, western painting, oil paint, thick paint, oversaturated, chaotic, pixelated",
        recommended_strength=0.55,
        recommended_steps=40,
        recommended_guidance=7.0,
    ),

    "vintage_poster": StylePreset(
        name="Vintage Poster",
        description="Retro poster art with bold colors and simplified forms",
        base_prompt="vintage poster art, bold flat colors, simplified forms, retro aesthetic, clean graphic style, artistic illustration, beautiful composition, professional design",
        negative_prompt="photograph, photorealistic, detailed rendering, gradients, modern digital art, pixelated, messy, watermark",
        recommended_strength=0.6,
        recommended_steps=40,
        recommended_guidance=7.0,
    ),
}


def get_preset(preset_name: str) -> StylePreset:
    """
    Get a style preset by name.

    Args:
        preset_name: Name of the preset (e.g., 'oil_painting')

    Returns:
        StylePreset object

    Raises:
        KeyError: If preset name not found
    """
    if preset_name not in STYLE_PRESETS:
        raise KeyError(f"Unknown style preset: {preset_name}. Available: {list(STYLE_PRESETS.keys())}")

    return STYLE_PRESETS[preset_name]


def list_presets() -> Dict[str, Dict[str, Any]]:
    """
    Get all available presets as a dictionary.

    Returns:
        Dictionary mapping preset names to their configurations
    """
    return {name: preset.to_dict() for name, preset in STYLE_PRESETS.items()}


def get_preset_names() -> list[str]:
    """Get list of all available preset names."""
    return list(STYLE_PRESETS.keys())


def get_preset_for_display() -> list[Dict[str, str]]:
    """
    Get presets formatted for UI display.

    Returns:
        List of dicts with 'value', 'label', and 'description'
    """
    return [
        {
            "value": name,
            "label": preset.name,
            "description": preset.description,
        }
        for name, preset in STYLE_PRESETS.items()
    ]
