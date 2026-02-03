/**
 * Photostrip Reveal Page - Display final photostrip with download/print/share options
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';

export default function PhotostripRevealPage() {
  const navigate = useNavigate();
  const { capturedPhotos, selectedFrames, finalPhotostrip, setFinalPhotostrip, resetCapture, photosPerStrip } = useAppStore();
  const [isComposing, setIsComposing] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Compose photostrip on mount (client-side)
  useEffect(() => {
    const composeStrip = async () => {
      try {
        console.log('[Composition] Composing photostrip from', capturedPhotos.length, 'photos (client-side)');

        const photoCount = capturedPhotos.length;
        if (photoCount !== 4 && photoCount !== 9) {
          throw new Error(`Expected 4 or 9 photos, got ${photoCount}`);
        }

        // Client-side composition: load images and compose on canvas
        const STRIP_WIDTH = photoCount === 9 ? 900 : 640;
        const PHOTO_HEIGHT = 480;
        const SPACING = 20;

        // Calculate dimensions based on photo count
        let canvasWidth: number;
        let canvasHeight: number;
        const gridCols = photoCount === 9 ? 3 : 2;
        const gridRows = photoCount === 9 ? 3 : 2;

        if (photoCount === 9) {
          // 3x3 grid layout for 9 frames
          const photoWidth = (STRIP_WIDTH - (SPACING * (gridCols + 1))) / gridCols;
          canvasWidth = STRIP_WIDTH;
          canvasHeight = (photoWidth * gridRows) + (SPACING * (gridRows + 1));
        } else {
          // 2x2 grid layout for 4 frames
          const photoWidth = (STRIP_WIDTH - (SPACING * (gridCols + 1))) / gridCols;
          canvasWidth = STRIP_WIDTH;
          canvasHeight = (photoWidth * gridRows) + (SPACING * (gridRows + 1));
        }

        const canvas = document.createElement('canvas');
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('Failed to get canvas context');

        // White background
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, canvasWidth, canvasHeight);

        // Load all photos
        const loadImage = (src: string): Promise<HTMLImageElement> => {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
          });
        };

        const photos = await Promise.all(capturedPhotos.map(loadImage));

        // Draw photos in grid layout
        const photoWidth = (canvasWidth - (SPACING * (gridCols + 1))) / gridCols;
        const photoHeight = photoCount === 9 ? photoWidth : (canvasHeight - (SPACING * (gridRows + 1))) / gridRows;

        photos.forEach((photo, index) => {
          const col = index % gridCols;
          const row = Math.floor(index / gridCols);
          const x = SPACING + (photoWidth + SPACING) * col;
          const y = SPACING + (photoHeight + SPACING) * row;
          ctx.drawImage(photo, x, y, photoWidth, photoHeight);
        });

        // Convert to data URL
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        console.log('[Composition] Photostrip composed successfully (client-side)');

        setFinalPhotostrip(dataUrl);

        // Upload to cloud in background (non-blocking)
        uploadToCloud(dataUrl);
      } catch (err) {
        console.error('[Composition] Composition error:', err);
        alert('Failed to compose photostrip');
      } finally {
        setIsComposing(false);
      }
    };

    const expectedCount = photosPerStrip;
    if (capturedPhotos.length === expectedCount && !finalPhotostrip) {
      composeStrip();
    } else {
      setIsComposing(false);
    }
  }, [capturedPhotos, finalPhotostrip, setFinalPhotostrip, photosPerStrip]);

  // Upload photostrip to cloud (async, non-blocking)
  const uploadToCloud = async (dataUrl: string) => {
    try {
      console.log('[Sharing] Uploading photostrip to cloud...');
      setIsUploading(true);
      setUploadError(null);

      const response = await apiService.uploadPhotostrip(dataUrl);

      console.log('[Sharing] Upload successful:', response.share_url);
      setShareUrl(response.share_url);
    } catch (err) {
      console.error('[Sharing] Upload error:', err);
      setUploadError('Failed to create share link. You can still download the photostrip.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = () => {
    if (!finalPhotostrip) return;

    // Convert base64 to blob and download
    const link = document.createElement('a');
    link.href = finalPhotostrip;
    link.download = `photostrip_${new Date().toISOString().slice(0, 10)}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    if (!finalPhotostrip) return;

    // Open image in new tab for printing
    const win = window.open();
    if (win) {
      win.document.write(`<img src="${finalPhotostrip}" style="max-width:100%;" onload="window.print();window.close();" />`);
    }
  };

  const handleRetake = () => {
    resetCapture();
    navigate('/frames');
  };

  const handleShare = () => {
    if (!shareUrl) return;

    // Copy share URL to clipboard
    navigator.clipboard.writeText(shareUrl).then(() => {
      alert('Share link copied to clipboard!');
    }).catch(() => {
      // Fallback: show the link
      prompt('Copy this share link:', shareUrl);
    });
  };

  if (isComposing) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'var(--color-background)',
        color: 'var(--color-text)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 'var(--font-size-xl)',
      }}>
        Composing your photostrip...
      </div>
    );
  }

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
      <h1 style={{ marginBottom: 'var(--spacing-xl)' }}>YOUR PHOTOSTRIP!</h1>

      {/* Upload Status */}
      {isUploading && (
        <div style={{
          padding: 'var(--spacing-sm) var(--spacing-md)',
          backgroundColor: 'rgba(255, 193, 7, 0.2)',
          borderRadius: 'var(--border-radius-sm)',
          marginBottom: 'var(--spacing-md)',
          fontSize: 'var(--font-size-sm)',
        }}>
          🔗 Creating share link...
        </div>
      )}

      {uploadError && (
        <div style={{
          padding: 'var(--spacing-sm) var(--spacing-md)',
          backgroundColor: 'rgba(244, 67, 54, 0.2)',
          borderRadius: 'var(--border-radius-sm)',
          marginBottom: 'var(--spacing-md)',
          fontSize: 'var(--font-size-sm)',
        }}>
          ⚠️ {uploadError}
        </div>
      )}

      {/* Photostrip Display */}
      {finalPhotostrip && (
        <img
          src={finalPhotostrip}
          alt="Photostrip"
          style={{
            maxWidth: '100%',
            maxHeight: '70vh',
            borderRadius: 'var(--border-radius-md)',
            boxShadow: 'var(--shadow-lg)',
            marginBottom: 'var(--spacing-xl)',
          }}
        />
      )}

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 'var(--spacing-md)',
        justifyContent: 'center',
      }}>
        <button
          onClick={handleDownload}
          className="btn btn-primary"
          style={{ fontSize: 'var(--font-size-lg)' }}
        >
          💾 DOWNLOAD
        </button>

        {shareUrl ? (
          <button
            onClick={handleShare}
            className="btn btn-primary"
            style={{ fontSize: 'var(--font-size-lg)' }}
            title={shareUrl}
          >
            🔗 SHARE
          </button>
        ) : isUploading ? (
          <button
            disabled
            className="btn"
            style={{
              fontSize: 'var(--font-size-lg)',
              opacity: 0.6,
              cursor: 'not-allowed',
            }}
          >
            🔗 UPLOADING...
          </button>
        ) : null}

        <button
          onClick={handlePrint}
          className="btn"
          style={{ fontSize: 'var(--font-size-lg)' }}
        >
          🖨 PRINT
        </button>

        <button
          onClick={handleRetake}
          className="btn btn-secondary"
          style={{ fontSize: 'var(--font-size-lg)' }}
        >
          ↺ RETAKE
        </button>
      </div>
    </div>
  );
}
