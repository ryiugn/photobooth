/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import type { AppState, SelectedFrame, Frame, Template } from '../types';

interface AppStore extends AppState {
  // Actions
  setAuthenticated: (isAuthenticated: boolean, token: string | null) => void;
  setSelectedFrame: (index: number, frame: SelectedFrame) => void;
  clearSelectedFrames: () => void;
  addCapturedPhoto: (photoBase64: string) => void;
  setCurrentPhotoIndex: (index: number) => void;
  setFinalPhotostrip: (photostrip: string | null) => void;
  setTemplates: (templates: Template[]) => void;
  setAvailableFrames: (frames: Frame[]) => void;
  resetCapture: () => void;
  resetAll: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  // Initial state
  isAuthenticated: !!localStorage.getItem('access_token'),
  token: localStorage.getItem('access_token'),
  sessionId: null,
  selectedFrames: [null, null, null, null],
  capturedPhotos: [],
  currentPhotoIndex: 0,
  finalPhotostrip: null,
  templates: [],
  availableFrames: [],

  // Authentication actions
  setAuthenticated: (isAuthenticated, token) => {
    set({ isAuthenticated, token });
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
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
    set({ selectedFrames: [null, null, null, null] });
  },

  // Capture session actions
  addCapturedPhoto: (photoBase64) => {
    set((state) => ({
      capturedPhotos: [...state.capturedPhotos, photoBase64],
      currentPhotoIndex: state.currentPhotoIndex + 1,
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

  // Reset helpers
  resetCapture: () => {
    set({
      capturedPhotos: [],
      currentPhotoIndex: 0,
      finalPhotostrip: null,
    });
  },

  resetAll: () => {
    set({
      isAuthenticated: false,
      token: null,
      sessionId: null,
      selectedFrames: [null, null, null, null],
      capturedPhotos: [],
      currentPhotoIndex: 0,
      finalPhotostrip: null,
    });
    localStorage.removeItem('access_token');
  },
}));
