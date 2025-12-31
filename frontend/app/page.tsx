'use client';

import { useState } from 'react';
import { ImageUpload } from '@/components/ImageUpload';
import { ParameterControls } from '@/components/ParameterControls';
import { JobStatus } from '@/components/JobStatus';
import { Results } from '@/components/Results';
import { apiClient, Job } from '@/lib/api';

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<{
    filename: string;
    originalFilename: string;
    preview: string;
  } | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Parameters
  const [mode, setMode] = useState<'photo-realistic' | 'painterly'>('photo-realistic');
  const [numLayers, setNumLayers] = useState(4);
  const [maxSize, setMaxSize] = useState(1024);
  const [painterlyStyle, setPainterlyStyle] = useState('oil painting');
  const [painterlyStrength, setPainterlyStrength] = useState(0.5);
  const [painterlySeed, setPainterlySeed] = useState(42);

  const handleFileUpload = async (file: File) => {
    setError(null);
    setIsUploading(true);

    try {
      const result = await apiClient.uploadFile(file);

      // Create preview URL
      const preview = URL.createObjectURL(file);

      setUploadedFile({
        filename: result.filename,
        originalFilename: result.original_filename,
        preview,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!uploadedFile) return;

    setError(null);
    setCurrentJob(null);

    try {
      const job = await apiClient.createJob({
        filename: uploadedFile.filename,
        mode,
        num_layers: numLayers,
        max_size: maxSize,
        painterly_style: mode === 'painterly' ? painterlyStyle : undefined,
        painterly_strength: mode === 'painterly' ? painterlyStrength : undefined,
        painterly_seed: mode === 'painterly' ? painterlySeed : undefined,
      });

      setCurrentJob(job);

      // Poll for status updates
      await apiClient.pollJobStatus(job.id, (updatedJob) => {
        setCurrentJob(updatedJob);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    }
  };

  const handleReset = () => {
    setUploadedFile(null);
    setCurrentJob(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
            3D Painterly Image Generator
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Transform your photos into layered artistic prints
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Upload & Parameters */}
          <div className="space-y-6">
            <ImageUpload
              onFileSelect={handleFileUpload}
              uploadedFile={uploadedFile}
              isUploading={isUploading}
              onReset={handleReset}
            />

            {uploadedFile && !currentJob && (
              <ParameterControls
                mode={mode}
                onModeChange={setMode}
                numLayers={numLayers}
                onNumLayersChange={setNumLayers}
                maxSize={maxSize}
                onMaxSizeChange={setMaxSize}
                painterlyStyle={painterlyStyle}
                onPainterlyStyleChange={setPainterlyStyle}
                painterlyStrength={painterlyStrength}
                onPainterlyStrengthChange={setPainterlyStrength}
                painterlySeed={painterlySeed}
                onPainterlySeedChange={setPainterlySeed}
                onGenerate={handleGenerate}
              />
            )}
          </div>

          {/* Right Column: Status & Results */}
          <div>
            {currentJob && currentJob.status !== 'completed' && (
              <JobStatus job={currentJob} />
            )}

            {currentJob && currentJob.status === 'completed' && (
              <Results job={currentJob} onReset={handleReset} />
            )}

            {currentJob && currentJob.status === 'failed' && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                  Generation Failed
                </h3>
                <p className="text-red-700 dark:text-red-300">
                  {currentJob.error_message || 'An unknown error occurred'}
                </p>
                <button
                  onClick={handleReset}
                  className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
