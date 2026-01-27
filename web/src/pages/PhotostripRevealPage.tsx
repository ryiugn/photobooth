/**
 * Photostrip Reveal Page - Display final photostrip with download/print options
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';

export default function PhotostripRevealPage() {
  const navigate = useNavigate();
  const { capturedPhotos, selectedFrames, finalPhotostrip, setFinalPhotostrip, resetCapture } = useAppStore();
  const [isComposing, setIsComposing] = useState(true);
  const [sessionId] = useState(`session_${Date.now()}`);

  // Compose photostrip on mount
  useEffect(() => {
    const composeStrip = async () => {
      try {
        // Get frame paths from selected frames
        const framePaths = selectedFrames.map((f) => f?.[0] || '');

        const response = await apiService.composePhotostrip({
          session_id: sessionId,
          photo_ids: ['photo_0', 'photo_1', 'photo_2', 'photo_3'],
          frame_paths: framePaths,
        });

        setFinalPhotostrip(response.photostrip_base64);
      } catch (err) {
        console.error('Composition error:', err);
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
  }, [capturedPhotos, selectedFrames, finalPhotostrip, sessionId, setFinalPhotostrip]);

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
