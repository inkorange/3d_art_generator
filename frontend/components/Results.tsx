'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Job, apiClient } from '@/lib/api';

interface ResultsProps {
  job: Job;
  onReset: () => void;
}

export function Results({ job, onReset }: ResultsProps) {
  const [selectedLayer, setSelectedLayer] = useState<number>(0);
  const [rotateX, setRotateX] = useState<number>(20);
  const [rotateY, setRotateY] = useState<number>(0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Zoom controls for preview
  const [previewZoom, setPreviewZoom] = useState<number>(1);
  const [previewPan, setPreviewPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanningPreview, setIsPanningPreview] = useState<boolean>(false);
  const [panStartPreview, setPanStartPreview] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  if (!job.result_manifest) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">No results available</p>
      </div>
    );
  }

  const layers = job.result_manifest.layers || [];
  const hasLayers = layers.length > 0;

  // Get list of downloadable files
  const getDownloadableFiles = () => {
    const files = ['01_original.png', '02_depth_map.png'];

    if (job.mode === 'photo-realistic') {
      files.push('03_composite_full.png');
      layers.forEach((layer) => {
        files.push(layer.name);
      });
    } else {
      files.push('03_painterly_output.png');
    }

    return files;
  };

  const downloadAll = () => {
    const files = getDownloadableFiles();
    files.forEach((filename, index) => {
      setTimeout(() => {
        const url = apiClient.getDownloadUrl(job.id, filename);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }, index * 200); // 200ms delay between each download
    });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    setRotateY(rotateY + deltaX * 0.5);
    setRotateX(Math.max(-90, Math.min(90, rotateX - deltaY * 0.5)));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetRotation = () => {
    setRotateX(20);
    setRotateY(0);
  };

  const handlePreviewWheel = (e: React.WheelEvent) => {
    e.preventDefault();

    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Calculate mouse position relative to current pan and zoom
    const relativeX = (mouseX - previewPan.x) / previewZoom;
    const relativeY = (mouseY - previewPan.y) / previewZoom;

    // Zoom factor
    const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(1, Math.min(10, previewZoom * zoomDelta));

    // Adjust pan to keep mouse position fixed
    const newPanX = mouseX - relativeX * newZoom;
    const newPanY = mouseY - relativeY * newZoom;

    setPreviewZoom(newZoom);
    setPreviewPan({ x: newPanX, y: newPanY });
  };

  const handlePreviewMouseDown = (e: React.MouseEvent) => {
    if (previewZoom > 1) {
      setIsPanningPreview(true);
      setPanStartPreview({ x: e.clientX - previewPan.x, y: e.clientY - previewPan.y });
    }
  };

  const handlePreviewMouseMove = (e: React.MouseEvent) => {
    if (isPanningPreview && previewZoom > 1) {
      setPreviewPan({
        x: e.clientX - panStartPreview.x,
        y: e.clientY - panStartPreview.y,
      });
    }
  };

  const handlePreviewMouseUp = () => {
    setIsPanningPreview(false);
  };

  const resetPreviewZoom = () => {
    setPreviewZoom(1);
    setPreviewPan({ x: 0, y: 0 });
  };

  const handleStackKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedLayer((prev) => Math.max(0, prev - 1));
      resetPreviewZoom();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedLayer((prev) => Math.min(layers.length - 1, prev + 1));
      resetPreviewZoom();
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Results</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <span className="font-medium">Completed in {job.processing_time?.toFixed(1)}s</span>
        </div>
      </div>

      {/* Layer Preview */}
      {hasLayers && (
        <>
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Layer Preview {previewZoom > 1 && `(${previewZoom.toFixed(1)}x)`}
              </h3>
              <div className="flex items-center gap-3">
                {previewZoom > 1 && (
                  <button
                    onClick={resetPreviewZoom}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Reset Zoom
                  </button>
                )}
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {layers[selectedLayer].description} ({layers[selectedLayer].coverage_percent.toFixed(1)}% coverage)
                </span>
              </div>
            </div>
            <div
              className={`relative aspect-video w-full overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-700 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBmaWxsPSIjY2NjIi8+PHJlY3QgeD0iMTAiIHk9IjEwIiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIGZpbGw9IiNjY2MiLz48L3N2Zz4=')] ${
                previewZoom > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-zoom-in'
              }`}
              onWheel={handlePreviewWheel}
              onMouseDown={handlePreviewMouseDown}
              onMouseMove={handlePreviewMouseMove}
              onMouseUp={handlePreviewMouseUp}
              onMouseLeave={handlePreviewMouseUp}
            >
              <div
                style={{
                  transform: `translate(${previewPan.x}px, ${previewPan.y}px) scale(${previewZoom})`,
                  transformOrigin: '0 0',
                  width: '100%',
                  height: '100%',
                  position: 'relative',
                }}
              >
                <Image
                  src={apiClient.getDownloadUrl(job.id, layers[selectedLayer].name)}
                  alt={layers[selectedLayer].description}
                  fill
                  className="object-contain pointer-events-none"
                  unoptimized
                />
              </div>

              {/* Zoom hint overlay */}
              {previewZoom === 1 && (
                <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-3 py-1 rounded-full pointer-events-none">
                  Scroll to zoom
                </div>
              )}
            </div>
          </div>

          {/* 3D Layer Stack Visualization */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                3D Layer Stack
              </h3>
              <button
                onClick={resetRotation}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Reset View
              </button>
            </div>

            <div
              className="relative w-full h-96 overflow-hidden rounded-lg bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 cursor-grab active:cursor-grabbing focus:outline-none select-none"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onKeyDown={handleStackKeyDown}
              tabIndex={0}
              style={{ perspective: '1200px', WebkitUserSelect: 'none', userSelect: 'none' }}
            >
              <div
                className="absolute inset-0 flex items-center justify-center"
                style={{
                  transformStyle: 'preserve-3d',
                  transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
                  transition: isDragging ? 'none' : 'transform 0.3s ease-out',
                }}
              >
                {layers.map((layer, index) => {
                  const spacing = 40;
                  const translateZ = index * spacing;
                  const isSelected = selectedLayer === index;

                  return (
                    <div
                      key={layer.name}
                      className={`absolute cursor-pointer transition-all duration-300 ${
                        isSelected ? 'ring-4 ring-blue-500 ring-offset-2 ring-offset-transparent' : ''
                      }`}
                      style={{
                        width: '280px',
                        height: '200px',
                        transform: `translateZ(${translateZ}px)`,
                        transformStyle: 'preserve-3d',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedLayer(index);
                      }}
                    >
                      {/* Layer card */}
                      <div className="relative w-full h-full rounded-lg overflow-hidden shadow-2xl hover:ring-2 hover:ring-white hover:ring-offset-2 hover:ring-offset-transparent transition-all duration-200">
                        <div className="absolute inset-0">
                          <Image
                            src={apiClient.getDownloadUrl(job.id, layer.name)}
                            alt={layer.description}
                            fill
                            className="object-contain"
                            unoptimized
                          />
                        </div>

                        {/* Layer label */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                          <div className="font-medium text-white text-sm">
                            {layer.description}
                          </div>
                          <div className="text-xs text-gray-300 mt-1">
                            Layer {index + 1} of {layers.length}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Instructions overlay */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/60 text-white text-xs px-4 py-2 rounded-full pointer-events-none">
                Drag to rotate • Click layer to select • ↑↓ arrows to cycle
              </div>
            </div>
          </div>
        </>
      )}

      {/* Download Buttons */}
      <div className="space-y-3">
        <button
          onClick={downloadAll}
          className="w-full py-3 px-6 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors shadow-lg hover:shadow-xl"
        >
          Download All Files
        </button>

        <div className="grid grid-cols-2 gap-3">
          {job.mode === 'photo-realistic' ? (
            <>
              <a
                href={apiClient.getDownloadUrl(job.id, '03_composite_full.png')}
                download
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-center text-sm rounded-lg transition-colors"
              >
                Composite
              </a>
              <a
                href={apiClient.getDownloadUrl(job.id, '02_depth_map.png')}
                download
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-center text-sm rounded-lg transition-colors"
              >
                Depth Map
              </a>
            </>
          ) : (
            <a
              href={apiClient.getDownloadUrl(job.id, '03_painterly_output.png')}
              download
              className="col-span-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-center text-sm rounded-lg transition-colors"
            >
              Painterly Output
            </a>
          )}
        </div>

        <button
          onClick={onReset}
          className="w-full py-2 px-4 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white text-sm rounded-lg transition-colors"
        >
          Generate Another
        </button>
      </div>

      {/* Job Info */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
            Job Details
          </summary>
          <div className="mt-3 space-y-2 text-xs font-mono bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <div>Job ID: {job.id}</div>
            <div>Mode: {job.mode}</div>
            <div>Layers: {job.num_layers}</div>
            <div>Export Layers: {job.export_layers ? 'Yes' : 'No'}</div>
            {job.export_layers && (
              <div>Feather Radius: {job.feather_radius}px</div>
            )}
            {job.mode === 'painterly' && (
              <>
                <div>Style: {job.painterly_style}</div>
                <div>Strength: {job.painterly_strength}</div>
                <div>Seed: {job.painterly_seed}</div>
              </>
            )}
          </div>
        </details>
      </div>
    </div>
  );
}
