/**
 * Frame Selection Page - Choose frames for 4 or 9 photo slots
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';
import { useCustomFrames } from '../hooks/useCustomFrames';
import { FrameUploadButton } from '../components/FrameUploadButton';
import type { PhotoCount } from '../types';

export default function FrameSelectionPage() {
  const navigate = useNavigate();
  const {
    photosPerStrip,
    selectedFrames,
    setSelectedFrame,
    setPhotosPerStrip,
    availableFrames,
    setAvailableFrames,
    clearSelectedFrames
  } = useAppStore();

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
  const allFrames = [
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
  const hasSelections = selectedFrames.some((f) => f !== null);

  const handleSlotClick = (index: number) => {
    setCurrentSlotIndex(index);
    setShowFramePicker(true);
  };

  const handleFrameCountChange = (count: PhotoCount) => {
    if (count === photosPerStrip) return;

    // Check if user has selections and warn them
    if (hasSelections) {
      if (!confirm(
        `Changing to ${count} frames will clear your current frame selections.\n\nDo you want to continue?`
      )) {
        return;
      }
    }

    setPhotosPerStrip(count);
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
        const frameName = f![1];

        // Check if it's a custom frame (data URL starts with 'data:')
        if (frameUrl.startsWith('data:')) {
          // Find matching custom frame by data URL
          const customFrame = customFrames.find(cf => cf.dataUrl === frameUrl);
          if (customFrame) {
            return customFrame.id;
          }
          // Fallback: try to find by name
          const customFrameByName = customFrames.find(cf => cf.name === frameName);
          if (customFrameByName) {
            return customFrameByName.id;
          }
          // Last resort: generate a stable ID from the data URL
          return `custom_${btoa(frameUrl.substring(0, 32)).replace(/[^a-zA-Z0-9]/g, '')}`;
        }

        // For built-in frames, find by URL in availableFrames to get the proper ID
        const matchingFrame = availableFrames.find(af => af.url === frameUrl || af.url.includes(frameUrl));
        if (matchingFrame) {
          return matchingFrame.id;
        }

        // Fallback: extract filename from URL and use as ID
        const filename = frameUrl.split('/').pop() || '';
        return filename.replace(/\.[^/.]+$/, '');
      });

      // Create template object
      const template = {
        id: `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: name.trim(),
        frames: frameIds,
        frameCount: photosPerStrip,
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

  const handleFrameSelect = (frame: any) => {
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

  // Calculate grid layout
  const is9Frames = photosPerStrip === 9;
  const gridCols = is9Frames ? 3 : 4;
  const gridRows = is9Frames ? 3 : 1;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--gradient-seahell)',
      padding: 'var(--spacing-lg)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--spacing-md)', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
        <button onClick={handleBack} className="btn" style={{ marginRight: 'var(--spacing-md)' }}>
          ← BACK
        </button>
        <h2 style={{ color: 'var(--color-text-dark)', margin: 0 }}>CHOOSE YOUR FRAMES</h2>
      </div>

      {/* 4/9 Frame Toggle */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 'var(--spacing-md)',
        marginBottom: 'var(--spacing-xl)'
      }}>
        <button
          onClick={() => handleFrameCountChange(4)}
          className="btn"
          style={{
            backgroundColor: photosPerStrip === 4 ? 'var(--color-accent)' : undefined,
            opacity: photosPerStrip === 4 ? 1 : 0.7,
            minWidth: '150px',
            padding: 'var(--spacing-sm) var(--spacing-md)',
          }}
        >
          4 FRAMES
        </button>
        <button
          onClick={() => handleFrameCountChange(9)}
          className="btn"
          style={{
            backgroundColor: photosPerStrip === 9 ? 'var(--color-accent)' : undefined,
            opacity: photosPerStrip === 9 ? 1 : 0.7,
            minWidth: '150px',
            padding: 'var(--spacing-sm) var(--spacing-md)',
          }}
        >
          9 FRAMES
        </button>
      </div>

      {/* Frame Slots */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${gridCols}, 1fr)`,
        gap: 'var(--spacing-lg)',
        marginBottom: 'var(--spacing-2xl)',
        justifyItems: 'center',
      }}>
        {Array.from({ length: photosPerStrip }).map((_, index) => (
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
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: 'var(--spacing-md)',
            }}>
              {allFrames.map((frame) => (
                <div
                  key={frame.id}
                  onClick={() => handleFrameSelect(frame)}
                  style={{
                    cursor: 'pointer',
                    border: '2px solid #D4A574',
                    borderRadius: 'var(--border-radius-md)',
                    overflow: 'hidden',
                    transition: 'transform 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  <img
                    src={frame.url}
                    alt={frame.name}
                    style={{
                      width: '100%',
                      height: '150px',
                      objectFit: 'cover',
                      display: 'block',
                    }}
                  />
                  <p style={{
                    margin: 0,
                    padding: 'var(--spacing-xs)',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: 'var(--color-text-dark)',
                    textAlign: 'center',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  }}>
                    {frame.name}
                  </p>
                </div>
              ))}
            </div>

            {/* Custom Frames Section with Delete Buttons */}
            {customFrames.length > 0 && (
              <div style={{ marginTop: 'var(--spacing-lg)' }}>
                <h4 style={{
                  color: 'var(--color-text-dark)',
                  marginBottom: 'var(--spacing-md)',
                  fontSize: '16px',
                  fontWeight: 'bold',
                }}>
                  YOUR CUSTOM FRAMES
                </h4>
                <div style={{
                  display: 'flex',
                  gap: 'var(--spacing-md)',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                }}>
                  {customFrames.map((customFrame) => (
                    <div
                      key={customFrame.id}
                      onClick={() => handleFrameSelect(customFrame)}
                      style={{
                        position: 'relative',
                        cursor: 'pointer',
                        border: '2px solid #D4A574',
                        borderRadius: 'var(--border-radius-md)',
                        overflow: 'hidden',
                        transition: 'transform 0.2s',
                        width: '150px',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                      }}
                    >
                      <img
                        src={customFrame.dataUrl}
                        alt={customFrame.name}
                        style={{
                          width: '100%',
                          height: '120px',
                          objectFit: 'cover',
                          display: 'block',
                        }}
                      />
                      <p style={{
                        margin: 0,
                        padding: 'var(--spacing-xs)',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: 'var(--color-text-dark)',
                        textAlign: 'center',
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      }}>
                        {customFrame.name}
                      </p>
                      <button
                        onClick={(e) => handleDeleteFrame(customFrame.id, e)}
                        style={{
                          position: 'absolute',
                          top: '5px',
                          right: '5px',
                          backgroundColor: 'rgba(255, 107, 107, 0.9)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '50%',
                          width: '24px',
                          height: '24px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                        title="Delete custom frame"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => setShowFramePicker(false)}
              className="btn"
              style={{
                marginTop: 'var(--spacing-lg)',
                width: '100%',
                backgroundColor: '#E3F2FD',
                color: 'var(--color-text-dark)'
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
