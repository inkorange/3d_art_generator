'use client';

import { useEffect, useState } from 'react';
import { Job } from '@/lib/api';

interface JobStatusProps {
  job: Job;
}

export function JobStatus({ job }: JobStatusProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (job.status === 'processing') {
      const interval = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [job.status]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  // Calculate estimated progress based on mode, size, and elapsed time
  const getProgress = () => {
    if (job.status !== 'processing') return 0;

    // Base times for 1024px (balanced size)
    let baseTime = job.mode === 'photo-realistic' ? 7 : 40;

    // Add AI inpainting time if enabled (photo-realistic only)
    // Includes model loading (~20-30s) + inference (~50-70s) = ~80-100s total
    if (job.mode === 'photo-realistic' && job.use_inpainting) {
      baseTime += 90; // Stable Diffusion inpainting adds ~90 seconds (model load + inference)
    }

    // Add ControlNet time if enabled (painterly only)
    if (job.mode === 'painterly' && job.use_controlnet) {
      baseTime *= 1.1; // ControlNet adds ~10% processing time
    }

    // Scale factor based on max_size (processing time scales roughly with pixel count)
    // 256px = 0.25x, 512px = 0.5x, 1024px = 1x, 1536px = 2x, 2048px = 4x
    const sizeScaleFactor = Math.pow(job.max_size / 1024, 1.5);

    // Adjust for layer export (if disabled, saves ~30% of photo-realistic time)
    const exportFactor = (!job.export_layers && job.mode === 'photo-realistic') ? 0.7 : 1.0;

    const expectedTime = baseTime * sizeScaleFactor * exportFactor;
    const progress = Math.min((elapsed / expectedTime) * 100, 95);
    return progress;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
        Processing
      </h2>

      {/* Status Badge */}
      <div className="mb-6">
        <div className="flex items-center space-x-3">
          {job.status === 'pending' && (
            <>
              <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
              <span className="text-lg text-gray-700 dark:text-gray-300">Waiting in queue...</span>
            </>
          )}
          {job.status === 'processing' && (
            <>
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-lg text-gray-700 dark:text-gray-300">Generating layers...</span>
            </>
          )}
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="mb-6">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${getProgress()}%` }}
          ></div>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Mode:</span>
          <span className="font-medium text-gray-900 dark:text-white capitalize">
            {job.mode.replace('-', ' ')}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Layers:</span>
          <span className="font-medium text-gray-900 dark:text-white">{job.num_layers}</span>
        </div>
        {job.mode === 'painterly' && job.painterly_style && (
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Style:</span>
            <span className="font-medium text-gray-900 dark:text-white capitalize">
              {job.painterly_style}
            </span>
          </div>
        )}
        {job.mode === 'photo-realistic' && job.use_inpainting && (
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">AI Background Fill:</span>
            <span className="font-medium text-blue-600 dark:text-blue-400">Enabled (+90s)</span>
          </div>
        )}
        {job.mode === 'painterly' && job.use_controlnet && (
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">ControlNet:</span>
            <span className="font-medium text-blue-600 dark:text-blue-400">Enabled (+10%)</span>
          </div>
        )}
        {job.status === 'processing' && (
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Elapsed:</span>
            <span className="font-medium text-gray-900 dark:text-white">{formatTime(elapsed)}</span>
          </div>
        )}
      </div>

      {/* Spinner */}
      <div className="mt-8 flex justify-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
        This may take a few moments...
      </p>
    </div>
  );
}
