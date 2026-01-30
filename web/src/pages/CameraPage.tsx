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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [sessionId] = useState(`session_${Date.now()}`);
  const [cameraError, setCameraError] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);

  // Use ref to track media stream for cleanup (avoiding React.StrictMode double-mount issues)
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Initialize camera on mount
  useEffect(() => {
    let isComponentMounted = true;

    const initializeCamera = async () => {
      try {
        console.log('[Camera] Initializing camera...');
        setCameraReady(false);
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });

        if (!isComponentMounted) {
          // Component was unmounted while waiting for camera
          mediaStream.getTracks().forEach((track) => track.stop());
          return;
        }

        mediaStreamRef.current = mediaStream;
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          console.log('[Camera] Media stream attached to video element');

          // Set camera ready immediately - don't wait for metadata
          setCameraReady(true);
        }
        setCameraError(false);
      } catch (err) {
        console.error('[Camera] Camera access error:', err);
        if (isComponentMounted) {
          setCameraError(true);
          setCameraReady(false);
        }
      }
    };

    initializeCamera();

    // Cleanup on unmount
    return () => {
      isComponentMounted = false;
      setCameraReady(false);
      if (mediaStreamRef.current) {
        console.log('[Camera] Cleaning up camera stream');
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, []);

  // Re-attach media stream when video element is recreated after conditional rendering
  useEffect(() => {
    // When showPreview changes from true to false, video element is recreated
    if (!showPreview && videoRef.current && mediaStreamRef.current) {
      console.log('[Camera] Video element recreated, re-attaching media stream');
      videoRef.current.srcObject = mediaStreamRef.current;
      // Play the video to ensure it's active
      videoRef.current.play().catch(err => {
        console.error('[Camera] Failed to play video:', err);
      });
    }
  }, [showPreview]);

  const handleCapture = async () => {
    console.log('[Camera] handleCapture called, cameraReady:', cameraReady, 'videoRef:', !!videoRef.current);
    if (!videoRef.current) {
      console.error('[Camera] Cannot capture: videoRef is null');
      alert('Camera not ready. Please wait for the camera to initialize.');
      return;
    }

    if (!cameraReady) {
      console.error('[Camera] Cannot capture: camera not ready');
      alert('Camera is still initializing. Please wait a moment and try again.');
      return;
    }

    // Start countdown
    console.log('[Camera] Starting countdown...');
    setCountdown(3);
  };

  // Handle countdown timer
  useEffect(() => {
    console.log('[Camera] Countdown useEffect triggered, countdown:', countdown);
    if (countdown === null) return;

    if (countdown === 0) {
      console.log('[Camera] Countdown reached 0, capturing photo...');
      // Capture photo
      capturePhoto();
      return;
    }

    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  // Handle ESC key to close preview or go back
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showPreview) {
          handleRetake();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showPreview]);

  const capturePhoto = async () => {
    console.log('[Camera] capturePhoto called, videoRef:', !!videoRef.current, 'canvasRef:', !!canvasRef.current);
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw video frame to canvas (NOT mirrored - we want the actual photo)
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get current frame URL
    const currentFrameUrl = selectedFrames[currentPhotoIndex]?.[0];
    if (!currentFrameUrl) {
      console.error('[Capture] No frame selected for photo', currentPhotoIndex);
      alert('No frame selected. Please go back and select frames.');
      // Reset countdown on error
      setCountdown(null);
      return;
    }

    console.log('[Capture] Capturing photo with frame:', currentFrameUrl);

    // Convert to blob
    canvas.toBlob(async (blob) => {
      if (!blob) {
        console.error('[Capture] Failed to create blob from canvas');
        alert('Failed to capture photo');
        // Reset countdown on error
        setCountdown(null);
        return;
      }

      try {
        // Send to backend for frame application
        const response = await apiService.capturePhoto(
          blob,
          currentFrameUrl,
          currentPhotoIndex,
          sessionId
        );

        console.log('[Capture] Photo captured successfully');
        // Show preview
        setPreviewImage(response.framed_photo);
        setShowPreview(true);
      } catch (err) {
        console.error('[Capture] Capture error:', err);
        alert('Failed to capture photo. Please try again.');
        // Reset countdown on error
        setCountdown(null);
      }
    }, 'image/png');
  };

  const handleKeep = () => {
    console.log('[Camera] handleKeep called, currentPhotoIndex:', currentPhotoIndex, 'countdown:', countdown);
    if (previewImage) {
      addCapturedPhoto(previewImage);

      // Check if all photos captured
      if (currentPhotoIndex + 1 >= 4) {
        console.log('[Camera] All photos captured, navigating to reveal');
        // Navigate to composition
        navigate('/reveal');
      } else {
        console.log('[Camera] Resetting for next photo');
        // Reset for next photo
        setShowPreview(false);
        setPreviewImage(null);
        // Reset countdown to re-enable the CAPTURE button
        setCountdown(null);
        // Restart video playback after video element re-appears
        setTimeout(() => {
          if (videoRef.current) {
            console.log('[Camera] Restarting video playback');
            videoRef.current.play().catch(err => console.error('[Camera] Failed to play video:', err));
          }
        }, 0);
      }
    }
  };

  const handleRetake = () => {
    console.log('[Camera] handleRetake called');
    setShowPreview(false);
    setPreviewImage(null);
    // Reset countdown to re-enable the CAPTURE button
    setCountdown(null);
    // Restart video playback after video element re-appears
    setTimeout(() => {
      if (videoRef.current) {
        console.log('[Camera] Restarting video playback');
        videoRef.current.play().catch(err => console.error('[Camera] Failed to play video:', err));
      }
    }, 0);
  };

  const handleSkip = async () => {
    console.log('[Camera] handleSkip called, currentPhotoIndex:', currentPhotoIndex);

    // Get current frame URL
    const currentFrameUrl = selectedFrames[currentPhotoIndex]?.[0];
    if (!currentFrameUrl) {
      console.error('[Capture] No frame selected for photo', currentPhotoIndex);
      alert('No frame selected. Please go back and select frames.');
      return;
    }

    try {
      // Create a blank white image (1280x720)
      const blankCanvas = document.createElement('canvas');
      blankCanvas.width = 1280;
      blankCanvas.height = 720;
      const ctx = blankCanvas.getContext('2d');
      if (ctx) {
        // Fill with white background
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, blankCanvas.width, blankCanvas.height);
      }

      // Convert to blob
      blankCanvas.toBlob(async (blob) => {
        if (!blob) {
          console.error('[Capture] Failed to create blank image');
          alert('Failed to create blank image');
          return;
        }

        try {
          // Send blank image to backend for frame application
          const response = await apiService.capturePhoto(
            blob,
            currentFrameUrl,
            currentPhotoIndex,
            sessionId
          );

          console.log('[Capture] Blank photo with frame created successfully');
          // Add directly to captured photos (don't show preview)
          addCapturedPhoto(response.framed_photo);

          // Check if all photos captured
          if (currentPhotoIndex + 1 >= 4) {
            console.log('[Camera] All photos captured, navigating to reveal');
            // Navigate to composition
            navigate('/reveal');
          }
          // If not all photos captured, the component will re-render with updated currentPhotoIndex
        } catch (err) {
          console.error('[Capture] Skip error:', err);
          alert('Failed to process blank photo. Please try again.');
        }
      }, 'image/png');
    } catch (err) {
      console.error('[Capture] Skip error:', err);
      alert('Failed to create blank photo. Please try again.');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    console.log('[Camera] Processing uploaded file:', file.name);

    const currentFrameUrl = selectedFrames[currentPhotoIndex]?.[0];
    if (!currentFrameUrl) {
      console.error('[Capture] No frame selected for photo', currentPhotoIndex);
      alert('No frame selected. Please go back and select frames.');
      return;
    }

    try {
      // Send file directly to backend for frame application
      const response = await apiService.capturePhoto(
        file,
        currentFrameUrl,
        currentPhotoIndex,
        sessionId
      );

      console.log('[Capture] Photo captured successfully from file upload');
      // Show preview
      setPreviewImage(response.framed_photo);
      setShowPreview(true);
    } catch (err) {
      console.error('[Capture] Capture error:', err);
      alert('Failed to capture photo. Please try again.');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleBack = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
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
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
            }}
          />
        ) : cameraError ? (
          /* Camera Error State */
          <div style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#333',
            color: 'white',
            padding: 'var(--spacing-lg)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-md)' }}>📷</div>
            <p style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-sm)' }}>
              Camera not available
            </p>
            <p style={{ fontSize: 'var(--font-size-sm)', opacity: 0.8, marginBottom: 'var(--spacing-md)' }}>
              Upload an image to continue
            </p>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: 'scaleX(-1)', // Mirror the video horizontally
              }}
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
                  objectFit: 'cover', // Use 'cover' to match backend composition logic
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

      {/* Hidden file input for upload fallback */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFileUpload}
      />

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
      ) : cameraError ? (
        /* Show upload and skip buttons when camera failed */
        <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
          <button
            onClick={handleSkip}
            className="btn btn-secondary"
            style={{
              fontSize: 'var(--font-size-xl)',
              padding: 'var(--spacing-md) var(--spacing-xl)',
            }}
          >
            SKIP →
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn btn-primary"
            style={{
              fontSize: 'var(--font-size-xl)',
              padding: 'var(--spacing-md) var(--spacing-xl)',
            }}
          >
            📁 UPLOAD PHOTO
          </button>
        </div>
      ) : !cameraReady ? (
        /* Show loading state while camera initializes */
        <button
          disabled
          className="btn btn-primary"
          style={{
            fontSize: 'var(--font-size-xl)',
            padding: 'var(--spacing-md) var(--spacing-xl)',
            opacity: 0.6,
          }}
        >
          ⏳ STARTING CAMERA...
        </button>
      ) : (
        <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
          <button
            onClick={handleSkip}
            className="btn btn-secondary"
            style={{
              fontSize: 'var(--font-size-xl)',
              padding: 'var(--spacing-md) var(--spacing-xl)',
            }}
          >
            SKIP →
          </button>
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
        </div>
      )}
    </div>
  );
}
