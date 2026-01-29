/**
 * Frame Selection Page - Choose frames for 4 photo slots
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';
import { useCustomFrames } from '../hooks/useCustomFrames';
import { FrameUploadButton } from '../components/FrameUploadButton';
import type { SelectedFrame, Frame } from '../types';

export default function FrameSelectionPage() {
  const navigate = useNavigate();
  const { selectedFrames, setSelectedFrame, availableFrames, setAvailableFrames, clearSelectedFrames } = useAppStore();
  const [showFramePicker, setShowFramePicker] = useState(false);
  const [currentSlotIndex, setCurrentSlotIndex] = useState(0);

  // Custom frames hook
  const {
    customFrames,
    isLoading: loadingCustomFrames,
    uploadProgress,
    addCustomFrame,
    deleteCustomFrame
  } = useCustomFrames();

  // Combine built-in and custom frames
  const allFrames: Frame[] = [
    ...availableFrames,
    ...customFrames.map(cf => ({
      id: cf.id,
      name: cf.name,
      url: cf.dataUrl,
      created: cf.createdAt
    }))
  ];

  // Load frames on mount
  useEffect(() => {
    if (availableFrames.length === 0) {
      apiService.getFrames().then(setAvailableFrames).catch(console.error);
    }
  }, [availableFrames, setAvailableFrames]);

  // Handle ESC key to close frame picker modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showFramePicker) {
        setShowFramePicker(false);
      }
    };

    if (showFramePicker) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [showFramePicker]);

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
        const frameUrl = f![0];

        // Check if it's a custom frame (data URL starts with 'data:')
        if (frameUrl.startsWith('data:')) {
          // Find matching custom frame by data URL
          const customFrame = customFrames.find(cf => cf.dataUrl === frameUrl);
          if (customFrame) {
            return customFrame.id;
          }
          // Fallback: try to find by name
          const customFrameByName = customFrames.find(cf => cf.name === f![1]);
          if (customFrameByName) {
            return customFrameByName.id;
          }
        }

        // For built-in frames, extract ID from URL
        // URL format: https://photoboothf.vercel.app/frames/frame_simple.png
        const filename = frameUrl.split('/').pop() || '';
        // Remove extension to get frame ID
        return filename.replace(/\.[^/.]+$/, '');
      });

      // Create template object
      const template = {
        id: `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: name.trim(),
        frames: frameIds,
        created: new Date().toISOString()
      };

      // Save to localStorage
      const STORAGE_KEY = 'photobooth_templates';
      const stored = localStorage.getItem(STORAGE_KEY);
      const templates = stored ? JSON.parse(stored) : [];
      templates.push(template);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(templates));

      // Also try to save to API (will fail silently on serverless)
      try {
        await apiService.createTemplate({
          name: name.trim(),
          frames: frameIds
        });
      } catch {
        // Ignore API errors - localStorage is the primary storage
      }

      alert('Template saved successfully!');
    } catch (error: any) {
      console.error('Failed to save template:', error);
      alert('Failed to save template');
    }
  };

  const handleFrameSelect = (frame: Frame) => {
    setSelectedFrame(currentSlotIndex, [frame.url, frame.name]);
    setShowFramePicker(false);
  };

  // Handle custom frame upload
  const handleFrameUpload = async (files: File[]) => {
    if (files.length === 0) return;

    const file = files[0];
    const name = prompt('Enter a name for your custom frame:', file.name.replace(/\.[^/.]+$/, ''));

    if (!name || !name.trim()) {
      alert('Please enter a name for the frame.');
      return;
    }

    try {
      await addCustomFrame(file, name.trim());
      alert('Custom frame uploaded successfully!');
    } catch (error) {
      alert(`Failed to upload frame: ${(error as Error).message}`);
    }
  };

  // Handle custom frame deletion
  const handleDeleteFrame = (frameId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent frame selection

    if (confirm('Are you sure you want to delete this custom frame?')) {
      deleteCustomFrame(frameId);

      // If this frame was selected in any slot, clear that slot
      selectedFrames.forEach((frame, index) => {
        if (frame && frame[0].includes(frameId)) {
          setSelectedFrame(index, null);
        }
      });
    }
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
        <FrameUploadButton
          onFilesSelected={handleFrameUpload}
          isLoading={uploadProgress > 0}
        />

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
              {allFrames.map((frame) => {
                const isCustomFrame = customFrames.some(cf => cf.id === frame.id);

                return (
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
                      position: 'relative',
                    }}
                  >
                    {/* Delete button for custom frames */}
                    {isCustomFrame && (
                      <button
                        onClick={(e) => handleDeleteFrame(frame.id, e)}
                        style={{
                          position: 'absolute',
                          top: '4px',
                          right: '4px',
                          backgroundColor: '#ff6b6b',
                          color: 'white',
                          border: 'none',
                          borderRadius: '50%',
                          width: '24px',
                          height: '24px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          lineHeight: '1',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                        title="Delete custom frame"
                      >
                        ×
                      </button>
                    )}

                    {/* Custom frame badge */}
                    {isCustomFrame && (
                      <div style={{
                        position: 'absolute',
                        top: '4px',
                        left: '4px',
                        backgroundColor: '#9b59b6',
                        color: 'white',
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: '10px',
                        fontWeight: 'bold',
                      }}>
                          CUSTOM
                        </div>
                    )}

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
                );
              })}
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
