/**
 * Photostrip Reveal Page - Display final photostrip with download/print options
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';

export default function PhotostripRevealPage() {
  const navigate = useNavigate();
  const { capturedPhotos, selectedFrames, finalPhotostrip, setFinalPhotostrip, resetCapture } = useAppStore();
  const [isComposing, setIsComposing] = useState(true);

  // Compose photostrip on mount (client-side)
  useEffect(() => {
    const composeStrip = async () => {
      try {
        console.log('[Composition] Composing photostrip from', capturedPhotos.length, 'photos (client-side)');

        if (capturedPhotos.length !== 4) {
          throw new Error(`Expected 4 photos, got ${capturedPhotos.length}`);
        }

        // Client-side composition: load images and compose on canvas
        const STRIP_WIDTH = 640;
        const PHOTO_HEIGHT = 480;
        const SPACING = 20;
        const stripHeight = (PHOTO_HEIGHT * 4) + (SPACING * 5);

        const canvas = document.createElement('canvas');
        canvas.width = STRIP_WIDTH;
        canvas.height = stripHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('Failed to get canvas context');

        // White background
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, STRIP_WIDTH, stripHeight);

        // Load all photos and draw them
        const loadImage = (src: string): Promise<HTMLImageElement> => {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
          });
        };

        const photos = await Promise.all(capturedPhotos.map(loadImage));

        // Draw each photo vertically
        photos.forEach((photo, index) => {
          const y = SPACING + (PHOTO_HEIGHT + SPACING) * index;
          ctx.drawImage(photo, 0, y, STRIP_WIDTH, PHOTO_HEIGHT);
        });

        // Convert to data URL
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        console.log('[Composition] Photostrip composed successfully (client-side)');

        setFinalPhotostrip(dataUrl);
      } catch (err) {
        console.error('[Composition] Composition error:', err);
        alert('Failed to compose photostrip');
      } finally {
        setIsComposing(false);
      }
    };

    if (capturedPhotos.length === 4 && !finalPhotostrip) {
      composeStrip();
    } else {
      setIsComposing(false);
    }
  }, [capturedPhotos, finalPhotostrip, setFinalPhotostrip]);

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
