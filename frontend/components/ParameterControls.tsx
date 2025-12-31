'use client';

import { useState, useEffect } from 'react';
import { apiClient, StylePreset } from '@/lib/api';

interface ParameterControlsProps {
  mode: 'photo-realistic' | 'painterly';
  onModeChange: (mode: 'photo-realistic' | 'painterly') => void;
  numLayers: number;
  onNumLayersChange: (value: number) => void;
  maxSize: number;
  onMaxSizeChange: (value: number) => void;
  exportLayers: boolean;
  onExportLayersChange: (value: boolean) => void;
  featherRadius: number;
  onFeatherRadiusChange: (value: number) => void;
  painterlyStyle: string;
  onPainterlyStyleChange: (value: string) => void;
  painterlyStrength: number;
  onPainterlyStrengthChange: (value: number) => void;
  painterlySeed: number;
  onPainterlySeedChange: (value: number) => void;
  useControlNet: boolean;
  onUseControlNetChange: (value: boolean) => void;
  useInpainting: boolean;
  onUseInpaintingChange: (value: boolean) => void;
  onGenerate: () => void;
}

export function ParameterControls({
  mode,
  onModeChange,
  numLayers,
  onNumLayersChange,
  maxSize,
  onMaxSizeChange,
  exportLayers,
  onExportLayersChange,
  featherRadius,
  onFeatherRadiusChange,
  painterlyStyle,
  onPainterlyStyleChange,
  painterlyStrength,
  onPainterlyStrengthChange,
  painterlySeed,
  onPainterlySeedChange,
  useControlNet,
  onUseControlNetChange,
  useInpainting,
  onUseInpaintingChange,
  onGenerate,
}: ParameterControlsProps) {
  const [stylePresets, setStylePresets] = useState<StylePreset[]>([]);
  const [loadingPresets, setLoadingPresets] = useState(true);

  // Fetch style presets on component mount
  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const presets = await apiClient.getStylePresets();
        setStylePresets(presets);
      } catch (error) {
        console.error('Failed to load style presets:', error);
        // Fallback to default presets if API fails
        setStylePresets([
          { value: 'oil_painting', label: 'Oil Painting', description: 'Classic oil painting style' },
          { value: 'watercolor', label: 'Watercolor', description: 'Soft watercolor style' },
          { value: 'impressionist', label: 'Impressionist', description: 'Impressionist style' },
        ]);
      } finally {
        setLoadingPresets(false);
      }
    };

    fetchPresets();
  }, []);

  const getSizeLabel = (size: number) => {
    if (size <= 512) return 'Preview (Fast)';
    if (size <= 1024) return 'Balanced';
    return 'High-Res (Slow)';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 space-y-6">
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Parameters</h2>

      {/* Mode Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Generation Mode
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => onModeChange('photo-realistic')}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'photo-realistic'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="text-left">
              <div className="font-semibold text-gray-900 dark:text-white">Photo-Realistic</div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                ~5-7 sec • Preserves original
              </div>
            </div>
          </button>
          <button
            onClick={() => onModeChange('painterly')}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'painterly'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="text-left">
              <div className="font-semibold text-gray-900 dark:text-white">Painterly</div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                ~40 sec • AI artistic
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Output Size */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Output Size: {maxSize}px ({getSizeLabel(maxSize)})
        </label>
        <input
          type="range"
          min="256"
          max="2048"
          step="256"
          value={maxSize}
          onChange={(e) => onMaxSizeChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>256</span>
          <span>512</span>
          <span>768</span>
          <span>1024</span>
          <span>1280</span>
          <span>1536</span>
          <span>1792</span>
          <span>2048</span>
        </div>
      </div>

      {/* Number of Layers */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Number of Layers: {numLayers}
        </label>
        <input
          type="range"
          min="2"
          max="5"
          value={numLayers}
          onChange={(e) => onNumLayersChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>2</span>
          <span>3</span>
          <span>4</span>
          <span>5</span>
        </div>
      </div>

      {/* Export Layers Toggle */}
      <div>
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            checked={exportLayers}
            onChange={(e) => onExportLayersChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:focus:ring-blue-600"
          />
          <div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Export Depth Layers
            </span>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Generate separate PNG files for each depth layer (for 3D assembly)
            </p>
          </div>
        </label>
      </div>

      {/* Feather Radius - only show if layers are being exported */}
      {exportLayers && (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Edge Feathering: {featherRadius}px
          </label>
          <input
            type="range"
            min="1"
            max="5"
            value={featherRadius}
            onChange={(e) => onFeatherRadiusChange(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>Sharp (1px)</span>
            <span>Soft (5px)</span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Controls how soft the edges are between layers
          </p>
        </div>
      )}

      {/* Background Inpainting - only show for photo-realistic mode */}
      {mode === 'photo-realistic' && (
        <div>
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={useInpainting}
              onChange={(e) => onUseInpaintingChange(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:focus:ring-blue-600"
            />
            <div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                AI Background Fill (Stable Diffusion)
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Use AI to intelligently fill background instead of blur (~90s extra, highest quality)
              </p>
            </div>
          </label>
        </div>
      )}

      {/* Painterly-specific controls */}
      {mode === 'painterly' && (
        <>
          {/* Style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Painting Style
            </label>
            <select
              value={painterlyStyle}
              onChange={(e) => onPainterlyStyleChange(e.target.value)}
              disabled={loadingPresets}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingPresets ? (
                <option>Loading styles...</option>
              ) : (
                stylePresets.map((preset) => (
                  <option key={preset.value} value={preset.value} title={preset.description}>
                    {preset.label}
                  </option>
                ))
              )}
            </select>
            {!loadingPresets && stylePresets.length > 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {stylePresets.find(p => p.value === painterlyStyle)?.description || ''}
              </p>
            )}
          </div>

          {/* Strength */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Transformation Strength: {painterlyStrength.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={painterlyStrength}
              onChange={(e) => onPainterlyStrengthChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>Subtle</span>
              <span>Strong</span>
            </div>
          </div>

          {/* Seed */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Random Seed
            </label>
            <input
              type="number"
              value={painterlySeed}
              onChange={(e) => onPainterlySeedChange(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="42"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Same seed = reproducible results
            </p>
          </div>

          {/* ControlNet Preserve Edges */}
          <div>
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={useControlNet}
                onChange={(e) => onUseControlNetChange(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:focus:ring-blue-600"
              />
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Preserve Edges (ControlNet)
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Maintains structural details and composition during artistic transformation (+10% time)
                </p>
              </div>
            </label>
          </div>
        </>
      )}

      {/* Generate Button */}
      <button
        onClick={onGenerate}
        className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-lg hover:shadow-xl"
      >
        Generate {mode === 'painterly' ? 'Painterly' : 'Photo-Realistic'} Layers
      </button>
    </div>
  );
}
