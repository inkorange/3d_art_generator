/**
 * API client for 3D Painterly Image Generator backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface JobCreate {
  filename: string;
  mode: 'photo-realistic' | 'painterly';
  num_layers: number;
  max_size: number;
  painterly_style?: string;
  painterly_strength?: number;
  painterly_seed?: number;
}

export interface Job {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  mode: 'photo-realistic' | 'painterly';
  num_layers: number;
  max_size: number;
  painterly_style?: string;
  painterly_strength?: number;
  painterly_seed?: number;
  input_filename: string;
  output_dir?: string;
  result_manifest?: LayerManifest;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  processing_time?: number;
}

export interface LayerManifest {
  job_id: string;
  mode: string;
  layer_count?: number;
  layers?: Layer[];
  style?: string;
  strength?: number;
  seed?: number;
}

export interface Layer {
  name: string;
  order: number;
  depth_range: [number, number];
  description: string;
  coverage_percent: number;
  is_opaque: boolean;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  original_filename: string;
  size_bytes: number;
  path: string;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload an image file
   */
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseUrl}/jobs/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || 'Upload failed');
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend. Is the backend running on http://localhost:8000?');
      }
      throw error;
    }
  }

  /**
   * Create a generation job
   */
  async createJob(params: JobCreate): Promise<Job> {
    const formData = new FormData();
    formData.append('filename', params.filename);
    formData.append('mode', params.mode);
    formData.append('num_layers', params.num_layers.toString());
    formData.append('max_size', params.max_size.toString());

    if (params.mode === 'painterly') {
      if (params.painterly_style) {
        formData.append('painterly_style', params.painterly_style);
      }
      if (params.painterly_strength !== undefined) {
        formData.append('painterly_strength', params.painterly_strength.toString());
      }
      if (params.painterly_seed !== undefined) {
        formData.append('painterly_seed', params.painterly_seed.toString());
      }
    }

    const response = await fetch(`${this.baseUrl}/jobs`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Job creation failed');
    }

    return response.json();
  }

  /**
   * Get job details
   */
  async getJob(jobId: string): Promise<Job> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get job');
    }

    return response.json();
  }

  /**
   * List all jobs
   */
  async listJobs(skip: number = 0, limit: number = 100): Promise<{ jobs: Job[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/jobs?skip=${skip}&limit=${limit}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list jobs');
    }

    return response.json();
  }

  /**
   * Get download URL for a result file
   */
  getDownloadUrl(jobId: string, filename: string): string {
    return `${this.baseUrl}/jobs/${jobId}/download/${filename}`;
  }

  /**
   * Delete a job
   */
  async deleteJob(jobId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete job');
    }
  }

  /**
   * Poll job status until completion
   */
  async pollJobStatus(
    jobId: string,
    onUpdate: (job: Job) => void,
    intervalMs: number = 2000
  ): Promise<Job> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const job = await this.getJob(jobId);
          onUpdate(job);

          if (job.status === 'completed' || job.status === 'failed') {
            resolve(job);
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }
}

export const apiClient = new APIClient();
