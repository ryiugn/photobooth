/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import type { AppState, SelectedFrame, Frame, Template } from '../types';

type PhotoCount = 4 | 9;

interface AppStore extends AppState {
  // Actions
  setAuthenticated: (isAuthenticated: boolean, token: string | null) => void;
  setSelectedFrame: (index: number, frame: SelectedFrame) => void;
  clearSelectedFrames: () => void;
  setPhotosPerStrip: (count: PhotoCount) => void;
  addCapturedPhoto: (photoBase64: string, exposureValue?: number) => void;
  setCurrentPhotoIndex: (index: number) => void;
  setFinalPhotostrip: (photostrip: string | null) => void;
  setTemplates: (templates: Template[]) => void;
  setAvailableFrames: (frames: Frame[]) => void;
  resetCapture: () => void;
  resetAll: () => void;
  // Exposure actions
  setCurrentExposure: (exposure: number) => void;
  resetExposures: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  // Initial state - check sessionStorage instead of localStorage
  isAuthenticated: !!sessionStorage.getItem('access_token'),
  token: sessionStorage.getItem('access_token'),
  sessionId: null,
  photosPerStrip: 4,
  selectedFrames: [null, null, null, null],
  capturedPhotos: [],
  currentPhotoIndex: 0,
  finalPhotostrip: null,
  templates: [],
  availableFrames: [],
  exposureValues: [],
  currentExposure: 0,

  // Authentication actions
  setAuthenticated: (isAuthenticated, token) => {
    set({ isAuthenticated, token });
    if (token) {
      sessionStorage.setItem('access_token', token);
    } else {
      sessionStorage.removeItem('access_token');
    }
  },

  // Frame selection actions
  setSelectedFrame: (index, frame) => {
    set((state) => {
      const newSelectedFrames = [...state.selectedFrames];
      newSelectedFrames[index] = frame;
      return { selectedFrames: newSelectedFrames };
    });
  },

  clearSelectedFrames: () => {
    set((state) => ({
      selectedFrames: Array(state.photosPerStrip).fill(null),
    }));
  },

  setPhotosPerStrip: (count) => {
    set((state) => ({
      photosPerStrip: count,
      selectedFrames: Array(count).fill(null),
      capturedPhotos: [],
      currentPhotoIndex: 0,
      finalPhotostrip: null,
    }));
  },

  // Capture session actions
  addCapturedPhoto: (photoBase64, exposureValue = 0) => {
    set((state) => ({
      capturedPhotos: [...state.capturedPhotos, photoBase64],
      currentPhotoIndex: state.currentPhotoIndex + 1,
      exposureValues: [...state.exposureValues, exposureValue],
    }));
  },

  setCurrentPhotoIndex: (index) => {
    set({ currentPhotoIndex: index });
  },

  setFinalPhotostrip: (photostrip) => {
    set({ finalPhotostrip: photostrip });
  },

  // Template actions
  setTemplates: (templates) => {
    set({ templates });
  },

  setAvailableFrames: (frames) => {
    set({ availableFrames: frames });
  },

  // Exposure actions
  setCurrentExposure: (exposure) => {
    set({ currentExposure: exposure });
  },

  resetExposures: () => {
    set({ exposureValues: [], currentExposure: 0 });
  },

  // Reset helpers
  resetCapture: () => {
    set({
      capturedPhotos: [],
      currentPhotoIndex: 0,
      finalPhotostrip: null,
      exposureValues: [],
      currentExposure: 0,
    });
  },

  resetAll: () => {
    set({
      isAuthenticated: false,
      token: null,
      sessionId: null,
      photosPerStrip: 4,
      selectedFrames: Array(4).fill(null),
      capturedPhotos: [],
      currentPhotoIndex: 0,
      finalPhotostrip: null,
      exposureValues: [],
      currentExposure: 0,
    });
    sessionStorage.removeItem('access_token');
  },
}));
