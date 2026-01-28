/**
 * Main Application Component
 * Handles routing and provides global state
 */

import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from './state/store';
import { apiService } from './services/api';
import LoginPage from './pages/LoginPage';
import FrameSelectionPage from './pages/FrameSelectionPage';
import CameraPage from './pages/CameraPage';
import PhotostripRevealPage from './pages/PhotostripRevealPage';
import TemplateManagerPage from './pages/TemplateManagerPage';

function App() {
  const { isAuthenticated, setAvailableFrames, setTemplates, setAuthenticated } = useAppStore();
  const [isTokenVerified, setIsTokenVerified] = useState(false);

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const isValid = await apiService.verifyToken();
          if (!isValid) {
            // Token is invalid, clear authentication
            setAuthenticated(false, null);
          }
        } catch {
          // Error verifying token, clear authentication
          setAuthenticated(false, null);
        }
      }
      setIsTokenVerified(true);
    };

    verifyToken();
  }, [setAuthenticated]);

  // Load available frames on mount
  useEffect(() => {
    if (isAuthenticated && isTokenVerified) {
      apiService.getFrames().then(setAvailableFrames).catch(console.error);
      apiService.getTemplates().then(setTemplates).catch(console.error);
    }
  }, [isAuthenticated, isTokenVerified, setAvailableFrames, setTemplates]);

  // Don't render until token is verified
  if (!isTokenVerified) {
    return null; // or a loading spinner
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Login page */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to="/frames" replace />
            ) : (
              <LoginPage />
            )
          }
        />

        {/* Frame selection page */}
        <Route
          path="/frames"
          element={
            isAuthenticated ? (
              <FrameSelectionPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* Template manager page */}
        <Route
          path="/templates"
          element={
            isAuthenticated ? (
              <TemplateManagerPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* Camera capture page */}
        <Route
          path="/camera"
          element={
            isAuthenticated ? (
              <CameraPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* Photostrip reveal page */}
        <Route
          path="/reveal"
          element={
            isAuthenticated ? (
              <PhotostripRevealPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
