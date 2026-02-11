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
    photosPerStrip,
    selectedFrames,
    capturedPhotos,
    currentPhotoIndex,
    addCapturedPhoto,
    resetCapture,
    currentExposure,
    setCurrentExposure,
    resetExposures,
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

  /**
   * Preload frames to ensure fast capture
   * Loads all selected frames into browser cache before capture starts
   */
  useEffect(() => {
    const preloadFrames = async () => {
      const frameUrls = selectedFrames
        .map((f) => f?.[0])
        .filter((url): url is string => !!url);

      if (frameUrls.length === 0) {
        return;
      }

      console.log('[Camera] Preloading frames:', frameUrls);

      // Create abort controller for cleanup
      const abortController = new AbortController();
      const signal = abortController.signal;

      // Preload each frame
      const loadPromises = frameUrls.map((url) => {
        return new Promise<void>((resolve) => {
          // Check if aborted
          if (signal.aborted) {
            resolve();
            return;
          }

          const img = new Image();

          const cleanup = () => {
            img.onload = null;
            img.onerror = null;
          };

          img.onload = () => {
            console.log('[Camera] Preloaded frame:', url);
            cleanup();
            resolve();
          };

          img.onerror = () => {
            console.warn('[Camera] Failed to preload frame:', url);
            cleanup();
            resolve(); // Resolve anyway to not block
          };

          img.src = url;
        });
      });

      await Promise.all(loadPromises);
      console.log('[Camera] All frames preloaded');
    };

    if (selectedFrames.some((f) => f !== null)) {
      preloadFrames();
    }
  }, [selectedFrames]); // This is correct - reload when frames change

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

    // Get the displayed dimensions of the video element (what user sees)
    // The container has maxWidth: 640px and aspectRatio: 4/3 (height = 480px)
    const displayedWidth = 640;
    const displayedHeight = 480;

    // Calculate the crop region to match objectFit: 'cover'
    // objectFit: 'cover' scales the video to cover the entire container and centers it
    const videoAspect = video.videoWidth / video.videoHeight;
    const displayAspect = displayedWidth / displayedHeight;

    let sourceX = 0, sourceY = 0, sourceWidth = video.videoWidth, sourceHeight = video.videoHeight;

    if (videoAspect > displayAspect) {
      // Video is wider than display - crop the sides
      sourceWidth = video.videoHeight * displayAspect;
      sourceX = (video.videoWidth - sourceWidth) / 2;
    } else {
      // Video is taller than display - crop the top/bottom
      sourceHeight = video.videoWidth / displayAspect;
      sourceY = (video.videoHeight - sourceHeight) / 2;
    }

    console.log('[Camera] Capturing with crop:', {
      videoSize: `${video.videoWidth}x${video.videoHeight}`,
      displaySize: `${displayedWidth}x${displayedHeight}`,
      cropRegion: `${Math.round(sourceX)},${Math.round(sourceY)},${Math.round(sourceWidth)}x${Math.round(sourceHeight)}`
    });

    // Set canvas size to match displayed size (not full video resolution)
    canvas.width = displayedWidth;
    canvas.height = displayedHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Apply exposure filter if set (using filter property on context)
    const exposureFilter = `brightness(${2 ** currentExposure})`;
    ctx.filter = exposureFilter;

    // Mirror horizontally to match the preview (transform: scaleX(-1))
    ctx.translate(displayedWidth, 0);
    ctx.scale(-1, 1);

    // Draw only the cropped region that matches what the user sees in preview
    ctx.drawImage(video, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, displayedWidth, displayedHeight);

    // Reset transform and filter before drawing frame (exposure should only affect photo, not frame)
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.filter = 'none';

    // Get current frame URL
    const currentFrameUrl = selectedFrames[currentPhotoIndex]?.[0];
    if (!currentFrameUrl) {
      console.error('[Capture] No frame selected for photo', currentPhotoIndex);
      alert('No frame selected. Please go back and select frames.');
      // Reset countdown on error
      setCountdown(null);
      return;
    }

    console.log('[Capture] Capturing photo with frame (client-side):', currentFrameUrl);

    // Load frame image and apply overlay client-side
    const frameImg = new Image();
    frameImg.crossOrigin = 'anonymous';
    frameImg.onload = () => {
      // Draw frame overlay with same cover logic as preview
      const frameAspect = frameImg.width / frameImg.height;
      let drawX = 0, drawY = 0, drawWidth = displayedWidth, drawHeight = displayedHeight;

      if (frameAspect > displayAspect) {
        // Frame is wider - crop sides
        drawWidth = displayedHeight * frameAspect;
        drawX = (displayedWidth - drawWidth) / 2;
      } else {
        // Frame is taller - crop top/bottom
        drawHeight = displayedWidth / frameAspect;
        drawY = (displayedHeight - drawHeight) / 2;
      }

      // Draw frame with transparency
      ctx.drawImage(frameImg, drawX, drawY, drawWidth, drawHeight);

      // Convert to data URL for preview (instant, no API call)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      console.log('[Capture] Photo captured with frame (client-side)', dataUrl.length);

      // Show preview immediately
      setPreviewImage(dataUrl);
      setShowPreview(true);
    };

    frameImg.onerror = () => {
      console.error('[Capture] Failed to load frame image:', currentFrameUrl);
      alert('Failed to load frame. Using photo without frame.');
      // Show photo without frame
      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      setPreviewImage(dataUrl);
      setShowPreview(true);
    };

    frameImg.src = currentFrameUrl;
  };

  const handleKeep = () => {
    console.log('[Camera] handleKeep called, currentPhotoIndex:', currentPhotoIndex, 'countdown:', countdown);
    if (previewImage) {
      // Store photo with its exposure value
      addCapturedPhoto(previewImage, currentExposure);

      // Check if all photos captured
      if (currentPhotoIndex + 1 >= photosPerStrip) {
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
        // Reset exposure slider for next photo
        setCurrentExposure(0);
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
    // Reset exposure slider for retake
    setCurrentExposure(0);
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
          addCapturedPhoto(response.framed_photo, currentExposure);

          // Check if all photos captured
          if (currentPhotoIndex + 1 >= photosPerStrip) {
            console.log('[Camera] All photos captured, navigating to reveal');
            // Navigate to composition
            navigate('/reveal');
          } else {
            // Reset exposure for next photo
            setCurrentExposure(0);
          }
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
    resetExposures();
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
        <h2 style={{ margin: 0 }}>Photo {currentPhotoIndex + 1} of {photosPerStrip}</h2>
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
                filter: `brightness(${2 ** currentExposure})`, // Apply exposure adjustment
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
                  opacity: 1,
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

      {/* Exposure adjustment slider */}
      {!showPreview && (
        <div style={{
          width: '100%',
          maxWidth: '500px',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-lg)',
        }}>
          <span style={{ fontSize: 'var(--font-size-md)', fontWeight: 'bold', minWidth: '80px' }}>
            Exposure:
          </span>
          <input
            type="range"
            min="-20"
            max="20"
            value={currentExposure * 10}
            onChange={(e) => setCurrentExposure(Number(e.target.value) / 10)}
            style={{
              flex: 1,
              height: '8px',
              borderRadius: '4px',
              background: 'linear-gradient(to right, #888 0%, #fff 50%, #888 100%)',
              cursor: 'pointer',
            }}
          />
          <span style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: 'bold',
            minWidth: '50px',
            textAlign: 'center',
          }}>
            {currentExposure > 0 ? '+' : ''}{currentExposure.toFixed(1)}
          </span>
        </div>
      )}

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
