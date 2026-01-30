/**
 * Template Manager Page - Save and load frame combinations
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../state/store';
import { apiService } from '../services/api';
import { useCustomFrames } from '../hooks/useCustomFrames';
import type { Template, CustomFrame } from '../types';

const STORAGE_KEY = 'photobooth_templates';
const CUSTOM_FRAMES_KEY = 'photobooth_custom_frames';

export default function TemplateManagerPage() {
  const navigate = useNavigate();
  const { templates, setTemplates, setSelectedFrame, selectedFrames, availableFrames, setAvailableFrames } = useAppStore();
  const { customFrames } = useCustomFrames();
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isLoadingFrames, setIsLoadingFrames] = useState(false);

  // Load templates and available frames on mount
  useEffect(() => {
    const loadData = async () => {
      // Load templates from localStorage
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setTemplates(parsed);
        } else {
          // Fallback to API if nothing in storage
          apiService.getTemplates().then(setTemplates).catch(() => setTemplates([]));
        }
      } catch {
        setTemplates([]);
      }

      // Load available frames from API if not already loaded
      if (!availableFrames || availableFrames.length === 0) {
        console.log('[Template] Loading available frames from API...');
        setIsLoadingFrames(true);
        try {
          const frames = await apiService.getFrames();
          console.log('[Template] Loaded frames:', frames.map(f => f.id));
          setAvailableFrames(frames);
        } catch (err) {
          console.error('[Template] Failed to load frames:', err);
        } finally {
          setIsLoadingFrames(false);
        }
      }
    };

    loadData();
    // Only run on mount - remove availableFrames from dependencies to prevent re-running
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleUseTemplate = () => {
    if (!selectedTemplate) return;

    console.log('[Template] Loading template:', selectedTemplate.name);
    console.log('[Template] Template frame IDs:', selectedTemplate.frames);
    console.log('[Template] Available frames:', availableFrames.map(f => ({ id: f.id, name: f.name })));
    console.log('[Template] Custom frames:', customFrames.map(cf => ({ id: cf.id, name: cf.name })));

    // Apply template frames to selection using frame IDs
    selectedTemplate.frames.forEach((frameId, index) => {
      console.log(`[Template] Loading slot ${index}, frameId: ${frameId}`);

      // First try to find in built-in frames by exact ID match
      let frame = availableFrames.find(f => f.id === frameId);

      // If not found, try matching by URL filename (for backward compatibility)
      if (!frame) {
        frame = availableFrames.find(f => {
          const urlFilename = f.url.split('/').pop()?.replace(/\.[^/.]+$/, '');
          return urlFilename === frameId || f.url.includes(frameId);
        });
      }

      // If still not found, try custom frames
      if (!frame) {
        console.log(`[Template] Frame ${frameId} not found in available frames, checking custom frames`);
        const customFrame = customFrames.find(cf => cf.id === frameId);
        if (customFrame) {
          console.log(`[Template] Found in custom frames: ${customFrame.name}`);
          frame = {
            id: customFrame.id,
            name: customFrame.name,
            url: customFrame.dataUrl,
            created: customFrame.createdAt
          };
        }
      }

      if (frame) {
        console.log(`[Template] Setting frame at slot ${index}:`, frame.name);
        setSelectedFrame(index, [frame.url, frame.name]);
      } else {
        console.error(`[Template] Frame ${frameId} not found anywhere!`);
      }
    });

    navigate('/frames');
  };

  const handleDeleteTemplate = async () => {
    if (!selectedTemplate) return;

    if (!confirm(`Delete template "${selectedTemplate.name}"?`)) return;

    try {
      // Delete from localStorage
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const updated = parsed.filter((t: Template) => t.id !== selectedTemplate.id);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        setTemplates(updated);
      }

      // Also try to delete from API (will fail silently on serverless)
      try {
        await apiService.deleteTemplate(selectedTemplate.id);
      } catch {
        // Ignore API errors on serverless
      }

      setSelectedTemplate(null);
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete template');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--gradient-seashell)',
      color: 'var(--color-text-dark)',
      padding: 'var(--spacing-lg)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
        <button
          onClick={() => navigate('/frames')}
          className="btn"
          style={{ marginRight: 'var(--spacing-md)' }}
        >
          ← BACK
        </button>
        <h2 style={{ margin: 0 }}>TEMPLATES</h2>
      </div>

      {/* Two Column Layout */}
      <div style={{
        display: 'flex',
        gap: 'var(--spacing-xl)',
        flexWrap: 'wrap',
      }}>
        {/* Left: Template List */}
        <div style={{
          flex: '1',
          minWidth: '300px',
          backgroundColor: 'rgba(255, 255, 255, 0.6)',
          borderRadius: 'var(--border-radius-md)',
          padding: 'var(--spacing-md)',
        }}>
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Saved Templates</h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => setSelectedTemplate(template)}
                style={{
                  padding: 'var(--spacing-sm)',
                  backgroundColor: selectedTemplate?.id === template.id
                    ? 'var(--color-primary)'
                    : 'rgba(255, 255, 255, 0.8)',
                  borderRadius: 'var(--border-radius-sm)',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ fontWeight: 'bold' }}>{template.name}</div>
                <div style={{ fontSize: 'var(--font-size-sm)', opacity: 0.7 }}>
                  {new Date(template.created).toLocaleDateString()}
                </div>
              </div>
            ))}

            {templates.length === 0 && (
              <p style={{ textAlign: 'center', opacity: 0.6 }}>No templates saved yet</p>
            )}
          </div>
        </div>

        {/* Right: Preview & Actions */}
        <div style={{
          flex: '1',
          minWidth: '300px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}>
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Preview</h3>

          {selectedTemplate ? (
            <>
              {/* Frame Previews */}
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.6)',
                borderRadius: 'var(--border-radius-md)',
                padding: 'var(--spacing-md)',
                marginBottom: 'var(--spacing-lg)',
                width: '100%',
                maxWidth: '400px',
              }}>
                {selectedTemplate.frames.map((framePath, index) => {
                  // Resolve frame path to actual URL
                  // Check if it's a custom frame ID (starts with 'custom_')
                  let displaySrc = framePath;
                  if (framePath.startsWith('custom_')) {
                    const customFrame = customFrames.find(cf => cf.id === framePath);
                    if (customFrame) {
                      displaySrc = customFrame.dataUrl;
                    }
                  }

                  return (
                    <img
                      key={index}
                      src={displaySrc}
                      alt={`Frame ${index + 1}`}
                      style={{
                        width: '100%',
                        height: '80px',
                        objectFit: 'contain',
                        marginBottom: index < 3 ? 'var(--spacing-sm)' : 0,
                      }}
                    />
                  );
                })}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', width: '100%', maxWidth: '300px' }}>
                <button
                  onClick={handleUseTemplate}
                  disabled={isLoadingFrames || availableFrames.length === 0}
                  className="btn btn-primary"
                  style={{
                    opacity: (isLoadingFrames || availableFrames.length === 0) ? 0.6 : 1,
                  }}
                >
                  {isLoadingFrames ? '⏳ LOADING FRAMES...' : availableFrames.length === 0 ? '❌ NO FRAMES AVAILABLE' : 'USE THIS TEMPLATE'}
                </button>
                <button onClick={handleDeleteTemplate} className="btn" style={{ backgroundColor: '#FF6B6B', color: 'white' }}>
                  🗑 DELETE TEMPLATE
                </button>
              </div>
            </>
          ) : (
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.6)',
              borderRadius: 'var(--border-radius-md)',
              padding: 'var(--spacing-2xl)',
              textAlign: 'center',
            }}>
              <p>Select a template to preview</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
