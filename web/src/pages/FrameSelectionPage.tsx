/**
 * Frame Selection Page - Choose frames for 4 photo slots
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';
import type { SelectedFrame, Frame } from '../types';

export default function FrameSelectionPage() {
  const navigate = useNavigate();
  const { selectedFrames, setSelectedFrame, availableFrames, setAvailableFrames, clearSelectedFrames } = useAppStore();
  const [showFramePicker, setShowFramePicker] = useState(false);
  const [currentSlotIndex, setCurrentSlotIndex] = useState(0);

  // Load frames on mount
  useEffect(() => {
    if (availableFrames.length === 0) {
      apiService.getFrames().then(setAvailableFrames).catch(console.error);
    }
  }, [availableFrames, setAvailableFrames]);

  const allFramesSelected = selectedFrames.every((f) => f !== null);

  const handleSlotClick = (index: number) => {
    setCurrentSlotIndex(index);
    setShowFramePicker(true);
  };

  const handleSaveTemplate = async () => {
    if (!allFramesSelected) return;

    // Prompt for template name
    const name = prompt('Enter a name for this template:');
    if (!name || !name.trim()) {
      return;
    }

    try {
      // Get frame IDs from selected frames
      const frameIds = selectedFrames.map((f) => {
        // Extract frame ID from URL
        // URL format: https://photoboothf.vercel.app/frames/frame_simple.png
        const filename = f![0].split('/').pop() || '';
        // Map filename to frame ID
        const frameMap: Record<string, string> = {
          'frame_simple.png': 'frame_simple',
          'frame_kawaii.png': 'frame_kawaii',
          'frame_classic.png': 'frame_classic',
          'custom_20260127_095644_pwumpd.webp': 'custom_pwumpd',
          'custom_20260127_204241_lyazbf.PNG': 'custom_lyazbf',
          'custom_20260127_210302_egptpm.PNG': 'custom_egptpm',
          'custom_20260127_210302_hxgbqw.PNG': 'custom_hxgbqw',
          'custom_20260127_210302_ieyzow.PNG': 'custom_ieyzow',
          'custom_20260127_210302_jhmwdz.PNG': 'custom_jhmwdz',
        };
        return frameMap[filename] || filename.split('.')[0];
      });

      await apiService.createTemplate({
        name: name.trim(),
        frames: frameIds
      });
      alert('Template saved successfully!');
    } catch (error: any) {
      console.error('Failed to save template:', error);
      alert(error.response?.data?.detail || 'Failed to save template');
    }
  };

  const handleFrameSelect = (frame: Frame) => {
    setSelectedFrame(currentSlotIndex, [frame.url, frame.name]);
    setShowFramePicker(false);
  };

  const handleStartSession = () => {
    if (allFramesSelected) {
      navigate('/camera');
    }
  };

  const handleBack = () => {
    clearSelectedFrames();
    // Optionally logout
    useAppStore.getState().setAuthenticated(false, null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--gradient-seashell)',
      padding: 'var(--spacing-lg)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <button onClick={handleBack} className="btn" style={{ marginRight: 'var(--spacing-md)' }}>
          ← BACK
        </button>
        <h2 style={{ color: 'var(--color-text-dark)', margin: 0 }}>CHOOSE YOUR FRAMES</h2>
      </div>

      {/* Frame Slots */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 'var(--spacing-lg)',
        marginBottom: 'var(--spacing-2xl)',
        flexWrap: 'wrap',
      }}>
        {[0, 1, 2, 3].map((index) => (
          <div
            key={index}
            onClick={() => handleSlotClick(index)}
            style={{
              width: '180px',
              height: '220px',
              borderRadius: 'var(--border-radius-md)',
              backgroundColor: selectedFrames[index]
                ? 'rgba(255, 255, 255, 0.6)'
                : 'rgba(255, 255, 255, 0.4)',
              border: selectedFrames[index]
                ? '3px solid var(--color-accent)'
                : '3px solid #D4A574',
              padding: 'var(--spacing-sm)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Photo Number */}
            <p style={{
              color: 'var(--color-text-dark)',
              fontWeight: 'bold',
              marginBottom: 'var(--spacing-sm)',
            }}>
              PHOTO {index + 1}
            </p>

            {/* Thumbnail or Placeholder */}
            {selectedFrames[index] ? (
              <img
                src={selectedFrames[index]![0]}
                alt={selectedFrames[index]![1]}
                style={{
                  width: '160px',
                  height: '160px',
                  objectFit: 'contain',
                }}
              />
            ) : (
              <div style={{
                width: '160px',
                height: '160px',
                backgroundColor: 'rgba(200, 180, 160, 0.5)',
                border: '3px dashed #D4A574',
                borderRadius: 'var(--border-radius-sm)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '48px',
                color: 'var(--color-text-dark)',
              }}>
                +
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Buttons */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 'var(--spacing-md)',
        flexWrap: 'wrap',
      }}>
        <button
          onClick={() => navigate('/templates')}
          className="btn"
          style={{ backgroundColor: '#E3F2FD', color: 'var(--color-text-dark)' }}
        >
          📂 LOAD TEMPLATE
        </button>

        <button
          onClick={handleSaveTemplate}
          className="btn"
          disabled={!allFramesSelected}
          style={{ backgroundColor: '#E3F2FD', color: 'var(--color-text-dark)' }}
        >
          💾 SAVE AS TEMPLATE
        </button>

        <button
          onClick={handleStartSession}
          className="btn btn-primary"
          disabled={!allFramesSelected}
        >
          START PHOTO SESSION
        </button>
      </div>

      {/* Frame Picker Modal */}
      {showFramePicker && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: '#FFF8DC',
            borderRadius: 'var(--border-radius-lg)',
            padding: 'var(--spacing-lg)',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflow: 'auto',
          }}>
            <h3 style={{ color: 'var(--color-text-dark)', marginBottom: 'var(--spacing-lg)' }}>
              CHOOSE A FRAME FOR PHOTO {currentSlotIndex + 1}
            </h3>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: 'var(--spacing-md)',
            }}>
              {availableFrames.map((frame) => (
                <div
                  key={frame.id}
                  onClick={() => handleFrameSelect(frame)}
                  style={{
                    cursor: 'pointer',
                    padding: 'var(--spacing-sm)',
                    backgroundColor: 'rgba(255, 255, 255, 0.6)',
                    border: '2px solid #D4A574',
                    borderRadius: 'var(--border-radius-sm)',
                    textAlign: 'center',
                  }}
                >
                  <img
                    src={frame.url}
                    alt={frame.name}
                    style={{
                      width: '160px',
                      height: '160px',
                      objectFit: 'contain',
                    }}
                  />
                  <p style={{
                    color: 'var(--color-text-dark)',
                    marginTop: 'var(--spacing-xs)',
                    fontSize: 'var(--font-size-sm)',
                  }}>
                    {frame.name}
                  </p>
                </div>
              ))}
            </div>

            <button
              onClick={() => setShowFramePicker(false)}
              className="btn"
              style={{
                marginTop: 'var(--spacing-lg)',
                width: '100%',
              }}
            >
              CANCEL
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
