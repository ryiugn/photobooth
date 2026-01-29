/**
 * API service for communicating with the FastAPI backend
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  Frame,
  Template,
  TemplateCreateRequest,
  CaptureResponse,
  ComposeRequest,
  ComposeResponse
} from '../types';

// Get API URL from environment or use default for development
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = sessionStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          sessionStorage.removeItem('access_token');
          window.location.href = '/';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(pin: string): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', { pin });
    if (response.data.access_token) {
      sessionStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
    sessionStorage.removeItem('access_token');
  }

  async verifyToken(): Promise<boolean> {
    try {
      const response = await this.client.get('/auth/verify');
      return response.data.valid;
    } catch {
      return false;
    }
  }

  // Frames
  async getFrames(): Promise<Frame[]> {
    const response = await this.client.get<{ frames: Frame[] }>('/frames');
    return response.data.frames;
  }

  async uploadFrame(file: File): Promise<Frame> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<Frame>('/frames/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async deleteFrame(frameId: string): Promise<void> {
    await this.client.delete(`/frames/${frameId}`);
  }

  // Templates
  async getTemplates(): Promise<Template[]> {
    const response = await this.client.get<{ templates: Template[] }>('/templates');
    return response.data.templates;
  }

  async createTemplate(request: TemplateCreateRequest): Promise<Template> {
    const response = await this.client.post<Template>('/templates', request);
    return response.data;
  }

  async deleteTemplate(templateId: string): Promise<void> {
    await this.client.delete(`/templates/${templateId}`);
  }

  // Camera & Capture
  async capturePhoto(
    photo: Blob,
    frameUrl: string,
    frameIndex: number,
    sessionId: string
  ): Promise<CaptureResponse> {
    const formData = new FormData();
    formData.append('photo', photo, `photo_${frameIndex}.png`);
    formData.append('frame_url', frameUrl);
    formData.append('frame_index', frameIndex.toString());
    formData.append('session_id', sessionId);

    console.log('[API] Capturing photo:', { frameUrl, frameIndex, sessionId });

    const response = await this.client.post<CaptureResponse>('/camera', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Composition
  async composePhotostrip(request: ComposeRequest): Promise<ComposeResponse> {
    const response = await this.client.post<ComposeResponse>('/composition', request);
    return response.data;
  }

  async downloadPhotostrip(stripId: string): Promise<Blob> {
    const response = await this.client.get(`/composition/download/${stripId}`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
