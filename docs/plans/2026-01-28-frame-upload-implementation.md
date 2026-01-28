# Frame Upload Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add client-side frame upload functionality to the photobooth web app, allowing users to upload custom frames that persist in localStorage.

**Architecture:** Pure client-side implementation using localStorage for persistence. No backend changes required. Custom frames are merged with built-in API frames at render time.

**Tech Stack:** React, TypeScript, Zustand (state management), localStorage (persistence)

---

## Task 1: Add TypeScript Types for Custom Frames

**Files:**
- Modify: `web/src/types/index.ts`

**Step 1: Read existing types file**

Run: View the file to understand current type structure
Expected: See `Frame`, `Template`, `SelectedFrame` interfaces

**Step 2: Add CustomFrame type to types/index.ts**

Add after line 12 (after `Frame` interface):

```typescript
// Custom frame types (user-uploaded, stored in localStorage)
export interface CustomFrame {
  id: string;              // UUID for unique identification
  name: string;            // User-provided display name
  dataUrl: string;         // Base64-encoded image data
  type: string;            // 'image/png', 'image/webp', etc.
  createdAt: string;       // ISO timestamp
  source: 'user-upload';   // Distinguishes from built-in frames
}

// Unified frame type for rendering (either built-in or custom)
export interface DisplayFrame {
  id: string;
  name: string;
  url: string;              // URL for built-in, dataUrl for custom
  source: 'built-in' | 'user-upload';
  createdAt: string;
}
```

**Step 3: Verify types compile**

Run: `cd web && npm run type-check` (or `npx tsc --noEmit`)
Expected: No type errors

**Step 4: Commit**

```bash
git add web/src/types/index.ts
git commit -m "feat: add CustomFrame and DisplayFrame types"
```

---

## Task 2: Create Image Processor Utility

**Files:**
- Create: `web/src/utils/imageProcessor.ts`

**Step 1: Create the image processor utility**

Create file with complete implementation:

```typescript
/**
 * Image processing utilities for frame upload
 */

export interface ProcessedImageResult {
  dataUrl: string;
  width: number;
  height: number;
  size: number; // in bytes
}

export interface ValidationError {
  valid: false;
  error: string;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
}

/**
 * Validate an uploaded image file
 */
export function validateImageFile(file: File): ValidationResult {
  // Check file type
  const allowedTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'];
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Please select PNG, JPEG, WebP, or SVG files'
    };
  }

  // Check file size (5MB max)
  const MAX_SIZE = 5 * 1024 * 1024;
  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: 'Image must be under 5MB'
    };
  }

  return { valid: true };
}

/**
 * Process an image file to data URL with optional resizing
 */
export async function processImageFile(
  file: File,
  maxSize: number = 1920
): Promise<ProcessedImageResult> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;

      // Create an image to get dimensions
      const img = new Image();
      img.onload = () => {
        // Check if resizing is needed
        if (img.width <= maxSize && img.height <= maxSize) {
          resolve({
            dataUrl,
            width: img.width,
            height: img.height,
            size: file.size
          });
          return;
        }

        // Resize the image
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }

        // Calculate new dimensions maintaining aspect ratio
        let newWidth = img.width;
        let newHeight = img.height;

        if (img.width > img.height) {
          if (newWidth > maxSize) {
            newHeight = (maxSize / newWidth) * newHeight;
            newWidth = maxSize;
          }
        } else {
          if (newHeight > maxSize) {
            newWidth = (maxSize / newHeight) * newWidth;
            newHeight = maxSize;
          }
        }

        canvas.width = newWidth;
        canvas.height = newHeight;

        // Draw resized image
        ctx.drawImage(img, 0, 0, newWidth, newHeight);

        // Get the resized data URL
        const resizedDataUrl = canvas.toDataURL(file.type, 0.9);
        resolve({
          dataUrl: resizedDataUrl,
          width: newWidth,
          height: newHeight,
          size: Math.round((resizedDataUrl.length * 3) / 4) // Approximate size
        });
      };

      img.onerror = () => reject(new Error('Could not load image'));
      img.src = dataUrl;
    };

    reader.onerror = () => reject(new Error('Could not read file'));
    reader.readAsDataURL(file);
  });
}

/**
 * Calculate localStorage usage for custom frames
 */
export function getStorageUsage(): { used: number; total: number; percentage: number } {
  const STORAGE_KEY = 'photobooth_custom_frames';
  const stored = localStorage.getItem(STORAGE_KEY);

  const used = stored ? new Blob([stored]).size : 0;
  const total = 5 * 1024 * 1024; // 5MB typical localStorage limit

  return {
    used,
    total,
    percentage: (used / total) * 100
  };
}

/**
 * Check if storage quota is exceeded
 */
export function isStorageQuotaExceeded(): boolean {
  const { percentage } = getStorageUsage();
  return percentage >= 95; // Warn at 95%
}
```

**Step 2: Verify the file exists**

Run: `ls -la web/src/utils/imageProcessor.ts`
Expected: File exists

**Step 3: Commit**

```bash
git add web/src/utils/imageProcessor.ts
git commit -m "feat: add image processor utility for validation and resizing"
```

---

## Task 3: Create Custom Frames Hook

**Files:**
- Create: `web/src/hooks/useCustomFrames.ts`

**Step 1: Create the custom frames hook**

Create file with complete implementation:

```typescript
/**
 * Hook for managing user-uploaded custom frames
 */

import { useState, useEffect } from 'react';
import type { CustomFrame } from '../types';
import { processImageFile, validateImageFile, isStorageQuotaExceeded } from '../utils/imageProcessor';

const STORAGE_KEY = 'photobooth_custom_frames';

export function useCustomFrames() {
  const [customFrames, setCustomFrames] = useState<CustomFrame[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Load custom frames from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const frames = JSON.parse(stored) as CustomFrame[];
        // Sort by creation date (newest first)
        frames.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        setCustomFrames(frames);
      }
    } catch (error) {
      console.error('Failed to load custom frames:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save custom frames to localStorage whenever they change
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(customFrames));
      } catch (error) {
        console.error('Failed to save custom frames:', error);
        throw new Error('Storage quota exceeded. Please delete some custom frames.');
      }
    }
  }, [customFrames, isLoading]);

  /**
   * Add a new custom frame from a file
   */
  const addCustomFrame = async (file: File, name: string): Promise<CustomFrame> => {
    // Validate file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // Check storage quota
    if (isStorageQuotaExceeded()) {
      throw new Error('Storage full. Delete some custom frames first.');
    }

    setUploadProgress(10);

    // Process image
    const processed = await processImageFile(file);
    setUploadProgress(50);

    // Create custom frame object
    const customFrame: CustomFrame = {
      id: `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: name.trim(),
      dataUrl: processed.dataUrl,
      type: file.type,
      createdAt: new Date().toISOString(),
      source: 'user-upload'
    };

    setUploadProgress(90);

    // Add to state
    setCustomFrames((prev) => [customFrame, ...prev]);
    setUploadProgress(100);

    // Reset progress after a delay
    setTimeout(() => setUploadProgress(0), 500);

    return customFrame;
  };

  /**
   * Delete a custom frame by ID
   */
  const deleteCustomFrame = (id: string) => {
    setCustomFrames((prev) => prev.filter((f) => f.id !== id));
  };

  /**
   * Get storage usage info
   */
  const getStorageUsage = () => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const used = stored ? new Blob([stored]).size : 0;
    const total = 5 * 1024 * 1024; // 5MB

    return {
      used: (used / (1024 * 1024)).toFixed(2),
      total: (total / (1024 * 1024)).toFixed(2),
      percentage: ((used / total) * 100).toFixed(0)
    };
  };

  return {
    customFrames,
    isLoading,
    uploadProgress,
    addCustomFrame,
    deleteCustomFrame,
    getStorageUsage
  };
}
```

**Step 2: Create hooks directory if needed**

Run: `mkdir -p web/src/hooks`
Expected: Directory created

**Step 3: Commit**

```bash
git add web/src/hooks/useCustomFrames.ts
git commit -m "feat: add useCustomFrames hook for managing uploaded frames"
```

---

## Task 4: Create Frame Upload Button Component

**Files:**
- Create: `web/src/components/FrameUploadButton.tsx`

**Step 1: Create the upload button component**

Create file with complete implementation:

```typescript
/**
 * Button component for uploading custom frames
 */

import { useRef } from 'react';
import type { ChangeEvent } from 'react';

interface FrameUploadButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export default function FrameUploadButton({
  onFilesSelected,
  disabled = false,
  isLoading = false
}: FrameUploadButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onFilesSelected(files);
      // Reset input to allow selecting the same file again
      e.target.value = '';
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled || isLoading}
        className="btn"
        style={{
          backgroundColor: 'var(--color-primary)',
          color: 'var(--color-text-dark)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-xs)',
          cursor: disabled || isLoading ? 'not-allowed' : 'pointer'
        }}
      >
        {isLoading ? (
          <>
            <span className="spinner">↻</span>
            UPLOADING...
          </>
        ) : (
          <>
            <span>+</span>
            UPLOAD CUSTOM FRAME
          </>
        )}
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/svg+xml"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
    </>
  );
}
```

**Step 2: Create components directory if needed**

Run: `mkdir -p web/src/components`
Expected: Directory created

**Step 3: Commit**

```bash
git add web/src/components/FrameUploadButton.tsx
git commit -m "feat: add FrameUploadButton component"
```

---

## Task 5: Create Frame Name Modal Component

**Files:**
- Create: `web/src/components/FrameNameModal.tsx`

**Step 1: Create the name prompt modal**

Create file with complete implementation:

```typescript
/**
 * Modal component for prompting user to name their uploaded frame
 */

import { useState, useEffect, useRef } from 'react';
import type { File } from '../types';

interface FrameNameModalProps {
  file: File;
  previewUrl: string;
  onSave: (name: string) => void;
  onCancel: () => void;
}

export default function FrameNameModal({
  file,
  previewUrl,
  onSave,
  onCancel
}: FrameNameModalProps) {
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Auto-fill name from filename
  useEffect(() => {
    const baseName = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
    setName(baseName);
  }, [file.name]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('Please enter a name for this frame');
      return;
    }

    onSave(name.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
      }}
      onClick={onCancel}
    >
      <div
        style={{
          backgroundColor: '#FFF8DC',
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-lg)',
          maxWidth: '400px',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <h3 style={{ color: 'var(--color-text-dark)', marginBottom: 'var(--spacing-md)' }}>
          NAME YOUR FRAME
        </h3>

        {/* Preview */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          <img
            src={previewUrl}
            alt="Preview"
            style={{
              maxWidth: '200px',
              maxHeight: '200px',
              objectFit: 'contain',
              border: '2px solid #D4A574',
              borderRadius: 'var(--border-radius-sm)',
            }}
          />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setError('');
            }}
            placeholder="Enter frame name"
            style={{
              width: '100%',
              marginBottom: 'var(--spacing-sm)',
            }}
          />

          {error && (
            <p className="text-error" style={{ marginBottom: 'var(--spacing-sm)' }}>
              {error}
            </p>
          )}

          <div
            style={{
              display: 'flex',
              gap: 'var(--spacing-sm)',
              justifyContent: 'center',
            }}
          >
            <button type="button" onClick={onCancel} className="btn">
              CANCEL
            </button>
            <button type="submit" className="btn btn-primary">
              SAVE
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

**Step 2: Fix type import**

Need to add File to types. Modify `web/src/types/index.ts` - add to global exports at the end:

```typescript
// Re-export common types
export type { File } from '@types/file'; // Or just use global File type
```

Actually, `File` is a global DOM type. Remove `import type { File } from '../types';` from FrameNameModal and use the global `File` type directly.

**Step 3: Fix the import**

Modify line 6 in FrameNameModal.tsx - remove the File import entirely since it's a global DOM type.

**Step 4: Commit**

```bash
git add web/src/components/FrameNameModal.tsx
git commit -m "feat: add FrameNameModal component for naming uploaded frames"
```

---

## Task 6: Create Storage Usage Indicator Component

**Files:**
- Create: `web/src/components/StorageUsageIndicator.tsx`

**Step 1: Create storage indicator component**

Create file with complete implementation:

```typescript
/**
 * Displays localStorage usage for custom frames
 */

interface StorageUsageIndicatorProps {
  used: string;      // e.g., "3.2"
  total: string;     // e.g., "5.0"
  percentage: string; // e.g., "64"
}

export default function StorageUsageIndicator({
  used,
  total,
  percentage
}: StorageUsageIndicatorProps) {
  const pct = parseFloat(percentage);
  const isWarning = pct >= 80;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-xs)',
        fontSize: 'var(--font-size-sm)',
        color: isWarning ? 'var(--color-error)' : 'var(--color-text-dark)',
        marginTop: 'var(--spacing-sm)',
      }}
    >
      <span>📦 Storage:</span>
      <span>{used} MB / {total} MB used</span>
      {isWarning && <span>⚠️</span>}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add web/src/components/StorageUsageIndicator.tsx
git commit -m "feat: add StorageUsageIndicator component"
```

---

## Task 7: Create Custom Frame Card Component

**Files:**
- Create: `web/src/components/CustomFrameCard.tsx`

**Step 1: Create custom frame card**

Create file with complete implementation:

```typescript
/**
 * Frame card component with delete button for custom frames
 */

import type { DisplayFrame } from '../types';

interface CustomFrameCardProps {
  frame: DisplayFrame;
  isSelected: boolean;
  onClick: () => void;
  onDelete: () => void;
}

export default function CustomFrameCard({
  frame,
  isSelected,
  onClick,
  onDelete
}: CustomFrameCardProps) {
  return (
    <div
      onClick={onClick}
      style={{
        cursor: 'pointer',
        padding: 'var(--spacing-sm)',
        backgroundColor: isSelected
          ? 'rgba(76, 175, 80, 0.2)'
          : 'rgba(255, 255, 255, 0.6)',
        border: isSelected
          ? '3px solid var(--color-accent)'
          : '2px solid #D4A574',
        borderRadius: 'var(--border-radius-sm)',
        textAlign: 'center',
        position: 'relative',
      }}
    >
      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        style={{
          position: 'absolute',
          top: '4px',
          right: '4px',
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          backgroundColor: 'var(--color-error)',
          color: 'white',
          border: 'none',
          cursor: 'pointer',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        title="Delete this frame"
      >
        ×
      </button>

      {/* Custom badge */}
      <div
        style={{
          position: 'absolute',
          top: '4px',
          left: '4px',
          backgroundColor: 'var(--color-primary)',
          color: 'var(--color-text-dark)',
          fontSize: '10px',
          padding: '2px 6px',
          borderRadius: '4px',
          fontWeight: 'bold',
        }}
      >
        CUSTOM
      </div>

      {/* Frame preview */}
      <img
        src={frame.url}
        alt={frame.name}
        style={{
          width: '160px',
          height: '160px',
          objectFit: 'contain',
        }}
      />

      {/* Frame name */}
      <p
        style={{
          color: 'var(--color-text-dark)',
          marginTop: 'var(--spacing-xs)',
          fontSize: 'var(--font-size-sm)',
          wordBreak: 'break-word',
        }}
      >
        {frame.name}
      </p>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add web/src/components/CustomFrameCard.tsx
git commit -m "feat: add CustomFrameCard component with delete button"
```

---

## Task 8: Update FrameSelectionPage to Integrate Upload

**Files:**
- Modify: `web/src/pages/FrameSelectionPage.tsx`

**Step 1: Add imports to FrameSelectionPage.tsx**

Add after line 9:

```typescript
import { useCustomFrames } from '../hooks/useCustomFrames';
import { useMemo, useState, useRef } from 'react';
import FrameUploadButton from '../components/FrameUploadButton';
import FrameNameModal from '../components/FrameNameModal';
import StorageUsageIndicator from '../components/StorageUsageIndicator';
import CustomFrameCard from '../components/CustomFrameCard';
import type { DisplayFrame } from '../types';
```

**Step 2: Add custom frames hook and state**

Add after line 15:

```typescript
  const { customFrames, addCustomFrame, deleteCustomFrame, getStorageUsage, uploadProgress } = useCustomFrames();
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState<string>('');
  const [uploadError, setUploadError] = useState<string>('');
```

**Step 3: Create memoized combined frames list**

Add after line 37 (after the ESC key handler):

```typescript
  // Combine built-in and custom frames
  const allFrames: DisplayFrame[] = useMemo(() => {
    const builtIn = availableFrames.map((f) => ({
      id: f.id,
      name: f.name,
      url: f.url,
      source: 'built-in' as const,
      createdAt: f.created
    }));

    const custom = customFrames.map((f) => ({
      id: f.id,
      name: f.name,
      url: f.dataUrl,
      source: 'user-upload' as const,
      createdAt: f.createdAt
    }));

    return [...builtIn, ...custom];
  }, [availableFrames, customFrames]);
```

**Step 4: Add upload handlers**

Add after line 110 (after handleFrameSelect):

```typescript
  const handleFilesSelected = async (files: File[]) => {
    setUploadError('');

    for (const file of files) {
      try {
        // Create preview URL
        const previewUrl = URL.createObjectURL(file);
        setPendingPreviewUrl(previewUrl);
        setPendingFile(file);
      } catch (error: any) {
        setUploadError(error.message || 'Failed to process file');
      }
    }
  };

  const handleFrameNameSave = async (name: string) => {
    if (!pendingFile) return;

    try {
      await addCustomFrame(pendingFile, name);
      setPendingFile(null);
      setPendingPreviewUrl('');
    } catch (error: any) {
      setUploadError(error.message || 'Failed to upload frame');
      setPendingFile(null);
      setPendingPreviewUrl('');
    }
  };

  const handleFrameNameCancel = () => {
    setPendingFile(null);
    setPendingPreviewUrl('');
  };
```

**Step 5: Update handleFrameSelect to work with DisplayFrame**

Modify the handleFrameSelect function (around line 107-110):

```typescript
  const handleFrameSelect = (frame: DisplayFrame) => {
    setSelectedFrame(currentSlotIndex, [frame.url, frame.name]);
    setShowFramePicker(false);
  };

  const handleDeleteFrame = (frameId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this custom frame?')) {
      deleteCustomFrame(frameId);
    }
  };
```

**Step 6: Add upload button and storage indicator to UI**

Modify the buttons section (around line 209-240) - add before the existing buttons:

```typescript
      {/* Upload Section */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: 'var(--spacing-lg)',
      }}>
        <FrameUploadButton
          onFilesSelected={handleFilesSelected}
          isLoading={uploadProgress > 0 && uploadProgress < 100}
        />

        {uploadError && (
          <p className="text-error" style={{ marginTop: 'var(--spacing-sm)' }}>
            {uploadError}
          </p>
        )}

        {customFrames.length > 0 && (
          <StorageUsageIndicator {...getStorageUsage()} />
        )}
      </div>

      {/* Existing Buttons */}
      <div style={{...existing styles...}}>
```

**Step 7: Update frame picker modal to render custom frames**

Modify the frame picker modal content (around line 268-304):

```typescript
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: 'var(--spacing-md)',
            }}>
              {allFrames.map((frame) => (
                frame.source === 'user-upload' ? (
                  <CustomFrameCard
                    key={frame.id}
                    frame={frame}
                    isSelected={selectedFrames[currentSlotIndex]?.[0] === frame.url}
                    onClick={() => handleFrameSelect(frame)}
                    onDelete={(e) => handleDeleteFrame(frame.id, e)}
                  />
                ) : (
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
                )
              ))}
            </div>
```

**Step 8: Add name modal at end of component**

Add before the closing `</div>` (before line 321):

```typescript
      {/* Frame Name Modal */}
      {pendingFile && pendingPreviewUrl && (
        <FrameNameModal
          file={pendingFile}
          previewUrl={pendingPreviewUrl}
          onSave={handleFrameNameSave}
          onCancel={handleFrameNameCancel}
        />
      )}
```

**Step 9: Verify no TypeScript errors**

Run: `cd web && npx tsc --noEmit`
Expected: No type errors

**Step 10: Commit**

```bash
git add web/src/pages/FrameSelectionPage.tsx
git commit -m "feat: integrate frame upload into FrameSelectionPage"
```

---

## Task 9: Add Spinner Style for Upload State

**Files:**
- Modify: `web/src/index.css`

**Step 1: Add spinner animation**

Add to the end of index.css:

```css
/* Spinner animation for upload state */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}
```

**Step 2: Commit**

```bash
git add web/src/index.css
git commit -m "feat: add spinner animation for upload button"
```

---

## Task 10: Manual Testing Checklist

**Files:** None (manual testing)

**Step 1: Start dev server**

Run: `cd web && npm run dev`
Expected: Dev server starts successfully

**Step 2: Test upload flow**

1. Navigate to Frame Selection page
2. Click "UPLOAD CUSTOM FRAME" button
3. Select a PNG/JPEG/WebP file from your device
4. Verify name modal appears with preview
5. Enter a name and click "SAVE"
6. Verify frame appears in the picker modal
7. Verify frame has "CUSTOM" badge
8. Select frame for a photo slot
9. Verify frame is applied correctly

**Step 3: Test deletion**

1. Open frame picker
2. Click "×" on a custom frame
3. Confirm deletion
4. Verify frame is removed

**Step 4: Test validation**

1. Try uploading a non-image file (PDF, TXT)
2. Verify error message appears
3. Try uploading a file > 5MB
4. Verify error message appears

**Step 5: Test persistence**

1. Upload a custom frame
2. Refresh the page
3. Verify custom frame still appears

**Step 6: Test template saving with custom frames**

1. Select custom frames for all 4 slots
2. Save as template
3. Navigate away and back
4. Load template
5. Verify custom frames are restored

**Step 7: Test storage limit**

1. Upload multiple large images until near limit
2. Verify storage usage indicator appears
3. Verify warning appears when approaching limit

**Step 8: All tests pass?**

If all tests pass: Ready for deployment
If any tests fail: Debug and fix issues

---

## Task 11: Update API Service for Template Compatibility

**Files:**
- Modify: `web/src/pages/FrameSelectionPage.tsx`

**Step 1: Update template saving to handle custom frames**

Modify the `handleSaveTemplate` function (around line 45-105) to properly store custom frames:

```typescript
  const handleSaveTemplate = async () => {
    if (!allFramesSelected) return;

    const name = prompt('Enter a name for this template:');
    if (!name || !name.trim()) {
      return;
    }

    try {
      // Build frame data for template
      const frameData = selectedFrames.map((f) => {
        if (!f) return null;

        const frameUrl = f[0];
        const frameName = f[1];

        // Check if this is a custom frame (dataUrl starts with data:)
        const isCustom = frameUrl.startsWith('data:');

        // Find matching frame in allFrames
        const matchingFrame = allFrames.find((af) => af.url === frameUrl);

        return {
          id: matchingFrame?.id || `frame_${Date.now()}`,
          name: frameName,
          url: frameUrl,
          source: isCustom ? 'user-upload' : 'built-in',
          dataUrl: isCustom ? frameUrl : undefined // Store dataUrl for custom frames
        };
      });

      const template = {
        id: `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: name.trim(),
        frames: frameData.filter(Boolean),
        created: new Date().toISOString()
      };

      // Save to localStorage with custom frame data
      const STORAGE_KEY = 'photobooth_templates';
      const stored = localStorage.getItem(STORAGE_KEY);
      const templates = stored ? JSON.parse(stored) : [];
      templates.push(template);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(templates));

      alert('Template saved successfully!');
    } catch (error: any) {
      console.error('Failed to save template:', error);
      alert('Failed to save template');
    }
  };
```

**Step 2: Commit**

```bash
git add web/src/pages/FrameSelectionPage.tsx
git commit -m "feat: save custom frame data in templates"
```

---

## Task 12: Update Template Loading for Custom Frames

**Files:**
- Check: `web/src/pages/TemplateManagerPage.tsx`

**Step 1: Read TemplateManagerPage**

Run: Read the file to understand template loading logic
Expected: See how templates are loaded and applied

**Step 2: Update template loading if needed**

If template loading needs updates to handle custom frames, modify the template loading logic to:
1. Check if frame has `source: 'user-upload'`
2. Load from `dataUrl` if custom, otherwise use URL
3. Recreate custom frames in state from stored data

**Step 3: Commit if changes made**

```bash
git add web/src/pages/TemplateManagerPage.tsx
git commit -m "feat: load templates with custom frame data"
```

---

## Task 13: Final Verification and Cleanup

**Files:** Multiple

**Step 1: Run TypeScript check**

Run: `cd web && npx tsc --noEmit`
Expected: No type errors

**Step 2: Check for console errors**

Run: `cd web && npm run build`
Expected: Build completes successfully

**Step 3: Review all new files**

Verify:
- `web/src/types/index.ts` - Has CustomFrame, DisplayFrame types
- `web/src/utils/imageProcessor.ts` - Image processing utilities
- `web/src/hooks/useCustomFrames.ts` - Custom frames hook
- `web/src/components/FrameUploadButton.tsx` - Upload button
- `web/src/components/FrameNameModal.tsx` - Name prompt modal
- `web/src/components/StorageUsageIndicator.tsx` - Storage indicator
- `web/src/components/CustomFrameCard.tsx` - Custom frame card
- `web/src/pages/FrameSelectionPage.tsx` - Updated with upload functionality
- `web/src/index.css` - Has spinner animation

**Step 4: Create summary of changes**

Run: `git diff --stat HEAD~13`
Expected: Summary of all files changed

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete frame upload feature implementation"
```

---

## Testing Summary

After completing all tasks, verify:

- [x] Users can upload PNG, JPEG, WebP, SVG files
- [x] Name modal appears for each uploaded file
- [x] Custom frames appear in picker with "CUSTOM" badge
- [x] Custom frames can be deleted
- [x] Storage usage indicator shows when frames exist
- [x] Custom frames persist across browser refresh
- [x] Custom frames work with template save/load
- [x] Validation errors show for invalid files
- [x] File size limit enforced (5MB)
- [x] Spinner shows during upload

---

## Deployment Notes

- No backend changes required
- Deploy to Vercel as usual
- Feature works entirely client-side
- Custom frames are per-browser (not shared across users)
- Clearing browser data deletes custom frames (expected behavior)
