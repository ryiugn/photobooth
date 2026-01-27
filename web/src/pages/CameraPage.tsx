/**
 * Camera Page - Live camera feed with frame overlay and photo capture
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';

export default function CameraPage() {
  const navigate = useNavigate();
  const {
    selectedFrames,
    capturedPhotos,
    currentPhotoIndex,
    addCapturedPhoto,
    resetCapture,
  } = useAppStore();

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [sessionId] = useState(`session_${Date.now()}`);

  // Initialize camera on mount
  useEffect(() => {
    const initializeCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });

        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      } catch (err) {
        console.error('Camera access error:', err);
        alert('Camera access denied. Please allow camera permissions.');
      }
    };

    initializeCamera();

    // Cleanup on unmount
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleCapture = async () => {
    if (!videoRef.current) return;

    // Start countdown
    setCountdown(3);
  };

  // Handle countdown timer
  useEffect(() => {
    if (countdown === null) return;

    if (countdown === 0) {
      // Capture photo
      capturePhoto();
      return;
    }

    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob
    canvas.toBlob(async (blob) => {
      if (!blob) return;

      try {
        // Send to backend for frame application
        const response = await apiService.capturePhoto(
          blob,
          currentPhotoIndex,
          sessionId
        );

        // Show preview
        setPreviewImage(response.framed_photo);
        setShowPreview(true);
      } catch (err) {
        console.error('Capture error:', err);
        alert('Failed to capture photo');
      }
    }, 'image/png');
  };

  const handleKeep = () => {
    if (previewImage) {
      addCapturedPhoto(previewImage);

      // Check if all photos captured
      if (currentPhotoIndex + 1 >= 4) {
        // Navigate to composition
        navigate('/reveal');
      } else {
        // Reset for next photo
        setShowPreview(false);
        setPreviewImage(null);
      }
    }
  };

  const handleRetake = () => {
    setShowPreview(false);
    setPreviewImage(null);
  };

  const handleBack = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    resetCapture();
    navigate('/frames');
  };

  const currentFrame = selectedFrames[currentPhotoIndex]?.[0];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--color-background)',
      color: 'var(--color-text)',
      padding: 'var(--spacing-lg)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--spacing-lg)', width: '100%' }}>
        <button onClick={handleBack} className="btn" style={{ marginRight: 'var(--spacing-md)' }}>
          ← BACK
        </button>
        <h2 style={{ margin: 0 }}>Photo {currentPhotoIndex + 1} of 4</h2>
      </div>

      {/* Camera/Preview Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: '640px',
        aspectRatio: '4/3',
        backgroundColor: '#222',
        borderRadius: 'var(--border-radius-md)',
        overflow: 'hidden',
        marginBottom: 'var(--spacing-lg)',
      }}>
        {showPreview ? (
          <img
            src={previewImage || ''}
            alt="Captured"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            {/* Frame overlay */}
            {currentFrame && (
              <img
                src={currentFrame}
                alt="Frame overlay"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                  objectFit: 'contain',
                  opacity: 0.8,
                }}
              />
            )}
            {/* Countdown overlay */}
            {countdown !== null && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                fontSize: '120px',
                fontWeight: 'bold',
                color: 'var(--color-primary)',
              }}>
                {countdown}
              </div>
            )}
          </>
        )}
      </div>

      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Action Buttons */}
      {showPreview ? (
        <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
          <button onClick={handleRetake} className="btn btn-secondary">
            RETAKE
          </button>
          <button onClick={handleKeep} className="btn btn-primary">
            KEEP →
          </button>
        </div>
      ) : (
        <button
          onClick={handleCapture}
          disabled={countdown !== null}
          className="btn btn-primary"
          style={{
            fontSize: 'var(--font-size-xl)',
            padding: 'var(--spacing-md) var(--spacing-xl)',
          }}
        >
          📷 CAPTURE
        </button>
      )}
    </div>
  );
}
