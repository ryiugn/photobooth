/**
 * Type definitions for the Photobooth application
 */

// Frame types
export interface Frame {
  id: string;
  name: string;
  url: string;
  thumbnail_url?: string;
  created: string;
}

// Custom frame types (user-uploaded, stored in localStorage)
export interface CustomFrame {
  id: string;              // UUID for unique identification
  name: string;            // User-provided display name
  dataUrl: string;         // Base64-encoded image data
  type: string;            // 'image/png', 'image/webp', etc.
  createdAt: string;       // ISO timestamp
  source: 'user-upload';   // Distinguishes from built-in frames
}

// Unified frame type for rendering (either built-in or custom)
export interface DisplayFrame {
  id: string;
  name: string;
  url: string;              // URL for built-in, dataUrl for custom
  source: 'built-in' | 'user-upload';
  createdAt: string;
}

export type SelectedFrame = [string, string] | null; // [path, name] tuple or null

// Photo count type
export type PhotoCount = 4 | 9;

// Template types
export interface Template {
  id: string;
  name: string;
  frames: string[]; // Array of 4 or 9 frame paths
  frameCount: PhotoCount; // 4 or 9
  created: string;
}

export interface TemplateCreateRequest {
  name: string;
  frames: string[];
}

export interface TemplateCategory {
  value: 'all' | '4' | '9';
  label: string;
}

// Authentication types
export interface LoginRequest {
  pin: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  sessionId: string | null;
}

// Capture types
export interface CaptureResponse {
  photo_id: string;
  framed_photo: string; // Base64 encoded
  frame_used: string;
}

export interface ComposeRequest {
  photos: string[]; // Array of 4 or 9 base64-encoded framed photos
  exposureValues?: number[]; // Exposure adjustment for each photo [-2.0, +2.0]
}

export interface ComposeResponse {
  strip_id: string;
  photostrip_base64: string;
  download_url: string;
}

// Sharing types
export interface ShareResponse {
  strip_id: string;
  share_url: string;
  expires_at: string;
}

// App state
export interface AppState {
  // Authentication
  isAuthenticated: boolean;
  token: string | null;
  sessionId: string | null;

  // Frame selection
  photosPerStrip: PhotoCount; // 4 or 9 frames
  selectedFrames: SelectedFrame[]; // Array of selected frames (length 4 or 9)

  // Capture session
  capturedPhotos: string[]; // Base64 framed photos
  currentPhotoIndex: number;
  finalPhotostrip: string | null;
  exposureValues: number[]; // Exposure value for each captured photo [-2.0, +2.0]
  currentExposure: number; // Current exposure slider value for next photo

  // Templates
  templates: Template[];
  availableFrames: Frame[];
}
