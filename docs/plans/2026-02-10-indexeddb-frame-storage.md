# IndexedDB Frame Storage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace localStorage with IndexedDB for custom frame storage to increase upload capacity from ~5MB to ~100MB while preserving image quality and resolution.

**Architecture:**
1. Create a new IndexedDB wrapper utility (`indexedDBStorage.ts`) that provides a simple async API
2. Keep existing `imageProcessor.ts` validation/processing functions (no changes)
3. Update `useCustomFrames.ts` hook to use IndexedDB instead of localStorage
4. Add migration logic to transfer existing frames from localStorage to IndexedDB
5. Add localStorage fallback for browsers that don't support IndexedDB

**Tech Stack:** TypeScript, IndexedDB API, React hooks

**Key Design Decisions:**
- **Database name:** `PhotoboothFramesDB`
- **Store name:** `customFrames`
- **Key path:** `id` (frame ID)
- **Fallback:** Gracefully degrade to localStorage if IndexedDB fails
- **Migration:** One-time transfer from localStorage on first load
- **Error handling:** Log errors but don't block the app

---

## Task 1: Create IndexedDB Wrapper Utility

**Files:**
- Create: `web/src/utils/indexedDBStorage.ts`

**Step 1: Write the IndexedDB wrapper**

```typescript
/**
 * IndexedDB wrapper for storing custom frames
 * Provides a simple async API with built-in error handling and localStorage fallback
 */

import { CustomFrame } from '../types';

const DB_NAME = 'PhotoboothFramesDB';
const STORE_NAME = 'customFrames';
const DB_VERSION = 1;

/**
 * Result type for database operations
 */
export interface DBResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Storage usage information
 */
export interface StorageUsage {
  used: number;      // Bytes used
  total: number;     // Total quota (estimated)
  percentage: number; // Percentage used
}

/**
 * IndexedDB Storage class
 * Handles all IndexedDB operations with fallback to localStorage
 */
class IndexedDBStorage {
  private db: IDBDatabase | null = null;
  private isInitialized = false;
  private useFallback = false;
  private fallbackKey = 'photobooth_custom_frames_fallback';

  /**
   * Initialize the IndexedDB database
   */
  async init(): Promise<DBResult<void>> {
    // Check if already initialized
    if (this.isInitialized) {
      return { success: true };
    }

    // Check if IndexedDB is supported
    if (typeof window === 'undefined' || !window.indexedDB) {
      console.warn('IndexedDB not supported, using localStorage fallback');
      this.useFallback = true;
      this.isInitialized = true;
      return { success: true };
    }

    return new Promise((resolve) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB, using localStorage fallback');
        this.useFallback = true;
        this.isInitialized = true;
        resolve({ success: true });
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isInitialized = true;
        resolve({ success: true });
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };
    });
  }

  /**
   * Get all frames from storage
   */
  async getAllFrames(): Promise<DBResult<CustomFrame[]>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.getFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve({ success: true, data: request.result as CustomFrame[] });
      };

      request.onerror = () => {
        console.error('Failed to get frames from IndexedDB, trying fallback');
        resolve(this.getFallback());
      };
    });
  }

  /**
   * Add a single frame to storage
   */
  async addFrame(frame: CustomFrame): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.addFallback(frame);
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.add(frame);

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to add frame to IndexedDB, trying fallback');
        resolve(this.addFallback(frame));
      };
    });
  }

  /**
   * Delete a frame by ID
   */
  async deleteFrame(frameId: string): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.deleteFallback(frameId);
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(frameId);

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to delete frame from IndexedDB, trying fallback');
        resolve(this.deleteFallback(frameId));
      };
    });
  }

  /**
   * Get storage usage information
   * For IndexedDB, this is an estimate based on frame data sizes
   */
  async getStorageUsage(): Promise<StorageUsage> {
    const result = await this.getAllFrames();
    const frames = result.data || [];

    let used = 0;
    for (const frame of frames) {
      // Estimate size based on dataUrl length
      used += frame.dataUrl.length * 2; // UTF-16
    }

    // IndexedDB has much larger limits - estimate 100MB per origin
    const total = 100 * 1024 * 1024;
    const percentage = (used / total) * 100;

    return { used, total, percentage };
  }

  /**
   * Clear all frames from storage
   */
  async clearAllFrames(): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.clearFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to clear IndexedDB, trying fallback');
        resolve(this.clearFallback());
      };
    });
  }

  // Fallback methods using localStorage

  private getFallback(): DBResult<CustomFrame[]> {
    try {
      const stored = localStorage.getItem(this.fallbackKey);
      if (stored) {
        return { success: true, data: JSON.parse(stored) };
      }
      return { success: true, data: [] };
    } catch (error) {
      console.error('Fallback localStorage read failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private addFallback(frame: CustomFrame): DBResult<void> {
    try {
      const result = this.getFallback();
      const frames = result.data || [];
      frames.push(frame);
      localStorage.setItem(this.fallbackKey, JSON.stringify(frames));
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage write failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private deleteFallback(frameId: string): DBResult<void> {
    try {
      const result = this.getFallback();
      const frames = (result.data || []).filter((f) => f.id !== frameId);
      localStorage.setItem(this.fallbackKey, JSON.stringify(frames));
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage delete failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private clearFallback(): DBResult<void> {
    try {
      localStorage.removeItem(this.fallbackKey);
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage clear failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  /**
   * Check if using fallback storage
   */
  isUsingFallback(): boolean {
    return this.useFallback;
  }
}

// Singleton instance
const storage = new IndexedDBStorage();

// Export API functions
export const indexedDBStorage = {
  init: () => storage.init(),
  getAllFrames: () => storage.getAllFrames(),
  addFrame: (frame: CustomFrame) => storage.addFrame(frame),
  deleteFrame: (frameId: string) => storage.deleteFrame(frameId),
  getStorageUsage: () => storage.getStorageUsage(),
  clearAllFrames: () => storage.clearAllFrames(),
  isUsingFallback: () => storage.isUsingFallback(),
};
```

**Step 2: No test needed yet** - This is a new utility file. Tests will be added after integration.

**Step 3: Commit**

```bash
git add web/src/utils/indexedDBStorage.ts
git commit -m "feat: add IndexedDB wrapper utility for frame storage"
```

---

## Task 2: Add Migration Function from localStorage

**Files:**
- Modify: `web/src/utils/indexedDBStorage.ts`

**Step 1: Add migration function to IndexedDBStorage class**

Add this method to the `IndexedDBStorage` class after the `isUsingFallback()` method:

```typescript
  /**
   * Migrate frames from localStorage to IndexedDB
   * This should be called once on app initialization
   */
  async migrateFromLocalStorage(): Promise<DBResult<{ migrated: number; skipped: number }>> {
    await this.init();

    // Skip if using fallback or already migrated
    if (this.useFallback || !this.db) {
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    // Check if already migrated
    const migrationFlag = localStorage.getItem('photobooth_frames_migrated');
    if (migrationFlag === 'true') {
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    try {
      // Read from old localStorage key
      const oldData = localStorage.getItem('photobooth_custom_frames');
      if (!oldData) {
        // Mark as migrated even if no data
        localStorage.setItem('photobooth_frames_migrated', 'true');
        return { success: true, data: { migrated: 0, skipped: 0 } };
      }

      const oldFrames: CustomFrame[] = JSON.parse(oldData);
      let migrated = 0;
      let skipped = 0;

      // Get existing frames to avoid duplicates
      const existingResult = await this.getAllFrames();
      const existingIds = new Set((existingResult.data || []).map((f) => f.id));

      // Add each frame to IndexedDB
      for (const frame of oldFrames) {
        if (existingIds.has(frame.id)) {
          skipped++;
          continue;
        }

        const addResult = await this.addFrame(frame);
        if (addResult.success) {
          migrated++;
        } else {
          skipped++;
        }
      }

      // Mark migration as complete
      localStorage.setItem('photobooth_frames_migrated', 'true');

      // Optionally clear old localStorage data after successful migration
      if (migrated > 0) {
        try {
          localStorage.removeItem('photobooth_custom_frames');
        } catch (e) {
          console.warn('Could not clear old localStorage data:', e);
        }
      }

      return { success: true, data: { migrated, skipped } };
    } catch (error) {
      console.error('Migration failed:', error);
      return { success: false, error: 'Migration failed' };
    }
  }
```

**Step 2: Export the migration function**

Add to the `indexedDBStorage` export object:

```typescript
export const indexedDBStorage = {
  init: () => storage.init(),
  getAllFrames: () => storage.getAllFrames(),
  addFrame: (frame: CustomFrame) => storage.addFrame(frame),
  deleteFrame: (frameId: string) => storage.deleteFrame(frameId),
  getStorageUsage: () => storage.getStorageUsage(),
  clearAllFrames: () => storage.clearAllFrames(),
  isUsingFallback: () => storage.isUsingFallback(),
  migrateFromLocalStorage: () => storage.migrateFromLocalStorage(),
};
```

**Step 3: Commit**

```bash
git add web/src/utils/indexedDBStorage.ts
git commit -m "feat: add localStorage to IndexedDB migration function"
```

---

## Task 3: Update imageProcessor.ts Storage Quota

**Files:**
- Modify: `web/src/utils/imageProcessor.ts:38`

**Step 1: Update STORAGE_QUOTA constant**

Change line 38 from:
```typescript
const STORAGE_QUOTA = 5 * 1024 * 1024;
```

To:
```typescript
// Increased quota for IndexedDB (100MB)
// Note: This constant is now used for display purposes only
// Actual storage is handled by IndexedDB which has much larger limits
const STORAGE_QUOTA = 100 * 1024 * 1024;
```

**Step 2: Update quota exceeded threshold**

Change line 214 from:
```typescript
return usage.percentage >= 95;
```

To:
```typescript
// Warn at 90% to give users time to act
return usage.percentage >= 90;
```

**Step 3: Update warning threshold**

Change line 77 from:
```typescript
if (file.size > MAX_FILE_SIZE * 0.8) {
```

To:
```typescript
// Warning at 80% of max file size
if (file.size > MAX_FILE_SIZE * 0.8) {
```

**Step 4: Commit**

```bash
git add web/src/utils/imageProcessor.ts
git commit -m "feat: increase storage quota to 100MB for IndexedDB"
```

---

## Task 4: Update useCustomFrames Hook to Use IndexedDB

**Files:**
- Modify: `web/src/hooks/useCustomFrames.ts`

**Step 1: Replace imports**

Replace lines 6-13:
```typescript
import { useState, useEffect } from 'react';
import { CustomFrame } from '../types';
import {
  validateImageFile,
  processImageFile,
  isStorageQuotaExceeded,
  getStorageUsage as getImageStorageUsage
} from '../utils/imageProcessor';
```

With:
```typescript
import { useState, useEffect, useCallback } from 'react';
import { CustomFrame } from '../types';
import {
  validateImageFile,
  processImageFile,
  isStorageQuotaExceeded
} from '../utils/imageProcessor';
import { indexedDBStorage } from '../utils/indexedDBStorage';
```

**Step 2: Remove old STORAGE_KEY constant**

Delete lines 15-18 (the old STORAGE_KEY constant and formatMB function).

**Step 3: Update the hook initialization**

Replace the entire `useCustomFrames` function implementation (lines 87-226) with:

```typescript
export function useCustomFrames(): UseCustomFramesReturn {
  const [customFrames, setCustomFrames] = useState<CustomFrame[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Format bytes to megabytes with 2 decimal places
   */
  const formatMB = useCallback((bytes: number): string => {
    return (bytes / (1024 * 1024)).toFixed(2);
  }, []);

  /**
   * Load frames from IndexedDB on mount and run migration
   */
  useEffect(() => {
    const loadFrames = async () => {
      try {
        // Initialize IndexedDB and run migration
        await indexedDBStorage.init();

        // Run migration from localStorage
        const migrationResult = await indexedDBStorage.migrateFromLocalStorage();
        if (migrationResult.data && migrationResult.data.migrated > 0) {
          console.log(`Migrated ${migrationResult.data.migrated} frames from localStorage`);
        }

        // Load all frames
        const result = await indexedDBStorage.getAllFrames();
        if (result.success && result.data) {
          // Sort by creation date (newest first)
          const sorted = result.data.sort(
            (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
          setCustomFrames(sorted);
        }
      } catch (error) {
        console.error('Failed to load custom frames:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadFrames();
  }, []);

  /**
   * Add a new custom frame
   *
   * @param file - The image file to upload
   * @param name - Display name for the frame
   * @returns Promise resolving to the created CustomFrame object
   * @throws Error if validation fails or storage quota exceeded
   */
  const addCustomFrame = async (file: File, name: string): Promise<CustomFrame> => {
    // Start upload progress
    setUploadProgress(10);

    // Validate the file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      setUploadProgress(0);
      throw new Error(validation.error || 'Invalid file');
    }

    // Check storage quota
    const usage = await indexedDBStorage.getStorageUsage();
    if (usage.percentage >= 90) {
      setUploadProgress(0);
      throw new Error('Storage quota exceeded. Please delete some frames to make space.');
    }

    setUploadProgress(50);

    // Process the image file
    const processed = await processImageFile(file);

    setUploadProgress(90);

    // Create custom frame object with unique ID
    const newFrame: CustomFrame = {
      id: `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      dataUrl: processed.dataUrl,
      type: file.type,
      createdAt: new Date().toISOString(),
      source: 'user-upload'
    };

    // Save to IndexedDB
    const result = await indexedDBStorage.addFrame(newFrame);
    if (!result.success) {
      setUploadProgress(0);
      throw new Error(result.error || 'Failed to save frame');
    }

    // Update state
    setCustomFrames((prev) => {
      const updated = [...prev, newFrame];
      return updated.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
    });

    setUploadProgress(100);

    // Reset progress after a short delay
    setTimeout(() => {
      setUploadProgress(0);
    }, 500);

    return newFrame;
  };

  /**
   * Delete a custom frame by ID
   *
   * @param id - The ID of the frame to delete
   */
  const deleteCustomFrame = async (id: string): Promise<void> => {
    const result = await indexedDBStorage.deleteFrame(id);
    if (result.success) {
      setCustomFrames((prev) => prev.filter((frame) => frame.id !== id));
    } else {
      console.error('Failed to delete frame:', result.error);
    }
  };

  /**
   * Get current storage usage information
   *
   * Calculates the current IndexedDB usage and returns formatted strings
   *
   * @returns StorageUsageInfo with used, total, and percentage as formatted strings
   */
  const getStorageUsage = useCallback(async (): Promise<StorageUsageInfo> => {
    const usage = await indexedDBStorage.getStorageUsage();
    return {
      used: `${formatMB(usage.used)} MB`,
      total: `${formatMB(usage.total)} MB`,
      percentage: `${usage.percentage.toFixed(2)} %`
    };
  }, [formatMB]);

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

**Step 4: Update StorageUsageInfo interface**

Change line 30-34 to make getStorageUsage async:

```typescript
export interface StorageUsageInfo {
  used: string;      // Formatted as "X.XX MB"
  total: string;     // Formatted as "X.XX MB"
  percentage: string; // Formatted as "X.XX %"
}
```

**Step 5: Update UseCustomFramesReturn interface**

Change line 51 to make getStorageUsage async:

```typescript
  /** Get current storage usage information (async) */
  getStorageUsage: () => Promise<StorageUsageInfo>;
```

**Step 6: Commit**

```bash
git add web/src/hooks/useCustomFrames.ts
git commit -m "feat: migrate useCustomFrames hook to IndexedDB storage"
```

---

## Task 5: Update Components Using getStorageUsage

**Files:**
- Find and update components that call `getStorageUsage()`

**Step 1: Find all usages of getStorageUsage**

```bash
cd web/src && grep -r "getStorageUsage" --include="*.tsx" --include="*.ts"
```

**Step 2: Update each usage to handle async**

For each component that uses `getStorageUsage`, update the call to use `await` or `.then()`:

Example pattern (before):
```tsx
const { used, total, percentage } = getStorageUsage();
```

Example pattern (after):
```tsx
const [storageInfo, setStorageInfo] = useState({ used: '0 MB', total: '100 MB', percentage: '0 %' });

useEffect(() => {
  const loadStorageInfo = async () => {
    const info = await getStorageUsage();
    setStorageInfo(info);
  };
  loadStorageInfo();
}, [getStorageUsage]);
```

**Step 3: Commit**

```bash
git add web/src/
git commit -m "fix: update components to handle async getStorageUsage"
```

---

## Task 6: Add Error Handling and User Notifications

**Files:**
- Create: `web/src/utils/storageErrors.ts`

**Step 1: Create error handler utility**

```typescript
/**
 * Storage error handling utilities
 */

export class StorageError extends Error {
  constructor(
    message: string,
    public code: 'QUOTA_EXCEEDED' | 'NOT_SUPPORTED' | 'MIGRATION_FAILED' | 'UNKNOWN'
  ) {
    super(message);
    this.name = 'StorageError';
  }
}

/**
 * Parse IndexedDB error and return user-friendly message
 */
export function getStorageErrorMessage(error: unknown): string {
  if (error instanceof StorageError) {
    switch (error.code) {
      case 'QUOTA_EXCEEDED':
        return 'Storage full. Please delete some frames to continue.';
      case 'NOT_SUPPORTED':
        return 'Your browser does not support frame storage. Please try a different browser.';
      case 'MIGRATION_FAILED':
        return 'Could not import your existing frames. Please re-upload them.';
      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    if (error.name === 'QuotaExceededError') {
      return 'Storage full. Please delete some frames to continue.';
    }
    return error.message;
  }

  return 'An unexpected error occurred while storing frames.';
}

/**
 * Check if IndexedDB is available
 */
export function isIndexedDBAvailable(): boolean {
  return typeof window !== 'undefined' && 'indexedDB' in window;
}

/**
 * Log storage diagnostics
 */
export function logStorageDiagnostics() {
  console.group('Storage Diagnostics');

  console.log('IndexedDB available:', isIndexedDBAvailable());

  // Check localStorage usage
  try {
    let localStorageUsed = 0;
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        localStorageUsed += localStorage[key].length + key.length;
      }
    }
    console.log('LocalStorage used:', (localStorageUsed / 1024).toFixed(2), 'KB');
  } catch (e) {
    console.log('LocalStorage not accessible');
  }

  console.groupEnd();
}
```

**Step 2: Commit**

```bash
git add web/src/utils/storageErrors.ts
git commit -m "feat: add storage error handling utilities"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add IndexedDB documentation section**

Add after the "Technology Stack" section:

```markdown
## Frame Storage

Custom frames are stored using IndexedDB with the following specifications:
- **Database name:** `PhotoboothFramesDB`
- **Store name:** `customFrames`
- **Storage capacity:** ~100MB per browser origin
- **Fallback:** localStorage for unsupported browsers
- **Migration:** Automatic migration from localStorage to IndexedDB on first load

### Storage Limits

| Browser | IndexedDB Limit | Fallback |
|---------|----------------|----------|
| Chrome/Edge | ~100-500MB | localStorage (~10MB) |
| Firefox | ~100-500MB | localStorage (~5MB) |
| Safari | ~100-500MB | localStorage (~5MB) |

### Frame Specifications

- **Allowed formats:** PNG, JPEG, WebP, SVG
- **Max file size:** 5MB per frame
- **Resolution:** Up to 1920px (maintains original quality)
- **Quality:** No compression applied
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add IndexedDB storage documentation"
```

---

## Task 8: Testing Checklist

**Step 1: Manual testing requirements**

Create a test plan document with these tests to run:

```markdown
# IndexedDB Frame Storage - Testing Checklist

## Basic Functionality
- [ ] Upload a single custom frame
- [ ] Upload multiple frames in sequence
- [ ] Delete a custom frame
- [ ] Refresh page - frames persist
- [ ] Check storage usage display

## Migration
- [ ] On first load with existing localStorage frames, migration runs
- [ ] Existing frames appear in IndexedDB after migration
- [ ] localStorage is cleared after successful migration
- [ ] Migration flag is set to prevent re-migration

## Error Handling
- [ ] Try to upload when storage is full (>90%)
- [ ] Test with browser that doesn't support IndexedDB
- [ ] Test with localStorage disabled
- [ ] Try to upload invalid file type
- [ ] Try to upload file >5MB

## Fallback
- [ ] Verify fallback to localStorage works
- [ ] Check that fallback mode is logged
- [ ] Verify frames persist in fallback mode

## Performance
- [ ] Upload 10 frames and check capture speed
- [ ] Verify no delay during capture with many frames
- [ ] Check memory usage in DevTools

## Cross-Browser
- [ ] Test on Chrome
- [ ] Test on Firefox
- [ ] Test on Safari (if available)
- [ ] Test on mobile browser (if available)
```

**Step 2: Commit**

```bash
git add docs/
git commit -m "docs: add IndexedDB testing checklist"
```

---

## Task 9: Add Frame Preloading Optimization

**Purpose:** Ensure frames are loaded into browser cache before capture starts, eliminating any potential loading delay during capture.

**Files:**
- Modify: `web/src/pages/CameraPage.tsx`

**Step 1: Add frame preloading effect**

After the existing `useEffect` hooks in CameraPage.tsx, add:

```typescript
  /**
   * Preload frames to ensure fast capture
   * Loads all selected frames into browser cache before capture starts
   */
  useEffect(() => {
    const preloadFrames = async () => {
      const frameUrls = selectedFrames
        .map((f) => f?.[0])
        .filter((url): url is string => !!url);

      console.log('[Camera] Preloading frames:', frameUrls);

      // Preload each frame
      const loadPromises = frameUrls.map((url) => {
        return new Promise<void>((resolve) => {
          const img = new Image();
          img.onload = () => {
            console.log('[Camera] Preloaded frame:', url);
            resolve();
          };
          img.onerror = () => {
            console.warn('[Camera] Failed to preload frame:', url);
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
  }, [selectedFrames]);
```

**Step 2: Commit**

```bash
git add web/src/pages/CameraPage.tsx
git commit -m "perf: preload frames before capture to ensure instant capture speed"
```

---

## CRITICAL ISSUES FOUND - MUST FIX BEFORE EXECUTION

### Issue 1: imageProcessor.ts Functions Now Broken (CRITICAL)
**Problem:** `getStorageUsage()` and `isStorageQuotaExceeded()` in `imageProcessor.ts` still read from localStorage, but frames are now in IndexedDB.

**Fix:** Task 3 needs to be updated to deprecate these functions properly.

### Issue 2: Duplicate Frame ID Not Handled (MEDIUM)
**Problem:** `addFrame()` in IndexedDB wrapper doesn't check for duplicate IDs before adding. This causes constraint errors.

**Fix:** Add duplicate check or use `put()` instead of `add()`.

### Issue 3: Transaction Error Handling Missing (MEDIUM)
**Problem:** Transactions don't handle `transaction.onerror`, only `request.onerror`.

**Fix:** Add transaction error listeners.

### Issue 4: Migration Data Loss Risk (HIGH)
**Problem:** If migration fails partway through, localStorage is cleared and some frames may be lost.

**Fix:** Only clear localStorage after ALL frames are successfully migrated.

### Issue 5: getStorageUsage Removed But Still Used (CRITICAL)
**Problem:** The plan removes `getStorageUsage` import but `isStorageQuotaExceeded()` still calls it internally.

**Fix:** Update Task 4 to not use `isStorageQuotaExceeded` from imageProcessor, or update imageProcessor.

### Issue 6: Preload Effect Missing Dependency (LOW)
**Problem:** Preload effect uses `selectedFrames` but doesn't handle the case where `selectedFrames` changes during capture.

**Fix:** Add proper dependency array and cleanup.

### Issue 7: Migration Race Condition (MEDIUM)
**Problem:** Multiple app instances could run migration simultaneously.

**Fix:** Add a migration lock.

### Issue 8: Fallback Mode Storage Key Mismatch (MEDIUM)
**Problem:** Fallback uses `photobooth_custom_frames_fallback` but old data is in `photobooth_custom_frames`.

**Fix:** Update fallback to check both keys during migration.

### Issue 9: Frame Preloading for Custom Frames (LOW)
**Problem:** Custom frames with data URLs might not cache properly in browser.

**Fix:** Verify preloading works with data URLs, not just HTTP URLs.

### Issue 10: TypeScript Strict Mode Issues (LOW)
**Problem:** Some async functions don't have proper error handling types.

**Fix:** Add proper try-catch blocks.

### Issue 11: Browser Quota Estimates May Be Wrong (LOW)
**Problem:** 100MB estimate may not match actual browser limits.

**Fix:** Add dynamic quota detection if possible.

### Issue 12: Cleanup Utility Missing (MEDIUM)
**Problem:** No way to clear IndexedDB if it gets corrupted.

**Fix:** Add a cleanup/reset function.

---

## UPDATED TASKS WITH FIXES

### Updated Task 1: Create IndexedDB Wrapper Utility (FIXED)

**Changes:**
- Add transaction error handling
- Use `put()` instead of `add()` to handle duplicates gracefully
- Add cleanup function

**Replace the `addFrame` method with:**
```typescript
  async addFrame(frame: CustomFrame): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.addFallback(frame);
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      // Add transaction error handler
      transaction.onerror = () => {
        console.error('Transaction failed, trying fallback');
        resolve(this.addFallback(frame));
      };

      transaction.oncomplete = () => {
        // Transaction succeeded
      };

      const store = transaction.objectStore(STORE_NAME);
      // Use put() instead of add() to handle duplicates gracefully (replaces if exists)
      const request = store.put(frame);

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to add frame to IndexedDB, trying fallback');
        resolve(this.addFallback(frame));
      };
    });
  }
```

**Add a cleanup method:**
```typescript
  /**
   * Reset/clear all storage (for debugging or recovery)
   */
  async resetStorage(): Promise<DBResult<void>> {
    await this.init();

    // Clear migration flag
    localStorage.removeItem('photobooth_frames_migrated');

    if (this.useFallback || !this.db) {
      return this.clearFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      transaction.onerror = () => {
        console.error('Failed to reset IndexedDB');
        resolve({ success: false, error: 'Reset failed' });
      };

      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        resolve({ success: false, error: 'Reset failed' });
      };
    });
  }
```

**Update export to include resetStorage:**
```typescript
export const indexedDBStorage = {
  init: () => storage.init(),
  getAllFrames: () => storage.getAllFrames(),
  addFrame: (frame: CustomFrame) => storage.addFrame(frame),
  deleteFrame: (frameId: string) => storage.deleteFrame(frameId),
  getStorageUsage: () => storage.getStorageUsage(),
  clearAllFrames: () => storage.clearAllFrames(),
  isUsingFallback: () => storage.isUsingFallback(),
  migrateFromLocalStorage: () => storage.migrateFromLocalStorage(),
  resetStorage: () => storage.resetStorage(),
};
```

### Updated Task 2: Migration with Safety (FIXED)

**Replace the migration function with safer version:**
```typescript
  /**
   * Migrate frames from localStorage to IndexedDB
   * This should be called once on app initialization
   */
  async migrateFromLocalStorage(): Promise<DBResult<{ migrated: number; skipped: number }>> {
    await this.init();

    // Skip if using fallback or already migrated
    if (this.useFallback || !this.db) {
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    // Check if already migrated (use both flag and presence of IndexedDB data)
    const migrationFlag = localStorage.getItem('photobooth_frames_migrated');
    const existingFrames = await this.getAllFrames();

    // Consider migrated if flag is set OR we already have frames in IndexedDB
    if (migrationFlag === 'true' || (existingFrames.data && existingFrames.data.length > 0)) {
      // Update flag if not set but we have data
      if (migrationFlag !== 'true') {
        localStorage.setItem('photobooth_frames_migrated', 'true');
      }
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    try {
      // Read from old localStorage key
      const oldData = localStorage.getItem('photobooth_custom_frames');
      if (!oldData) {
        // Mark as migrated even if no data
        localStorage.setItem('photobooth_frames_migrated', 'true');
        return { success: true, data: { migrated: 0, skipped: 0 } };
      }

      const oldFrames: CustomFrame[] = JSON.parse(oldData);
      let migrated = 0;
      let skipped = 0;

      // Get existing frames to avoid duplicates
      const existingIds = new Set((existingFrames.data || []).map((f) => f.id));

      // Add each frame to IndexedDB
      for (const frame of oldFrames) {
        if (existingIds.has(frame.id)) {
          skipped++;
          continue;
        }

        const addResult = await this.addFrame(frame);
        if (addResult.success) {
          migrated++;
        } else {
          skipped++;
        }
      }

      // ONLY clear localStorage after ALL frames are successfully migrated
      if (migrated === oldFrames.length) {
        // All frames migrated successfully, safe to clear
        try {
          localStorage.removeItem('photobooth_custom_frames');
          console.log('[Migration] Cleared old localStorage data after successful migration');
        } catch (e) {
          console.warn('[Migration] Could not clear old localStorage data:', e);
        }
      } else if (migrated > 0) {
        // Partial migration - log warning but don't clear
        console.warn(`[Migration] Partial migration: ${migrated}/${oldFrames.length} frames. Old data preserved.`);
      }

      // Mark migration as complete
      localStorage.setItem('photobooth_frames_migrated', 'true');

      return { success: true, data: { migrated, skipped } };
    } catch (error) {
      console.error('[Migration] Failed:', error);
      // Don't set migration flag on error - allow retry
      return { success: false, error: 'Migration failed' };
    }
  }
```

### Updated Task 3: Properly Deprecate imageProcessor Functions

**Replace Task 3 with:**

**Step 1: Add deprecation notice to imageProcessor.ts**

Add BEFORE the `getStorageUsage()` function:

```typescript
/**
 * @deprecated This function is deprecated. Use indexedDBStorage.getStorageUsage() instead.
 * This function is kept for backward compatibility but always returns zero usage.
 * Custom frames are now stored in IndexedDB, not localStorage.
 */
export function getStorageUsage(): { used: number; total: number; percentage: number } {
  // Return zero usage since frames are now in IndexedDB
  console.warn('[imageProcessor] getStorageUsage() is deprecated. Use indexedDBStorage.getStorageUsage() instead.');
  return {
    used: 0,
    total: STORAGE_QUOTA,
    percentage: 0
  };
}

/**
 * @deprecated This function is deprecated. Storage quota is now handled by IndexedDB.
 * Always returns false (quota not exceeded).
 */
export function isStorageQuotaExceeded(): boolean {
  console.warn('[imageProcessor] isStorageQuotaExceeded() is deprecated. Quota is handled by IndexedDB.');
  return false;
}
```

### Updated Task 4: Fixed Hook Implementation

**The hook implementation is correct, but ensure to remove the deprecated import:**

In Step 1, ensure the import is:
```typescript
import { useState, useEffect, useCallback } from 'react';
import { CustomFrame } from '../types';
import {
  validateImageFile,
  processImageFile
  // REMOVED: isStorageQuotaExceeded, getStorageUsage as getImageStorageUsage
} from '../utils/imageProcessor';
import { indexedDBStorage } from '../utils/indexedDBStorage';
```

### Updated Task 9: Fixed Preloading

**Replace the preload effect with:**
```typescript
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
```

### New Task 11: Add Recovery Utility

**Files:**
- Create: `web/src/utils/storageRecovery.ts`

```typescript
/**
 * Storage recovery utilities for debugging and fixing storage issues
 */

import { indexedDBStorage } from './indexedDBStorage';

/**
 * Diagnose storage issues and provide recovery options
 */
export async function diagnoseStorage() {
  console.group('Storage Diagnostics');

  // Check IndexedDB
  try {
    const framesResult = await indexedDBStorage.getAllFrames();
    console.log('IndexedDB frames:', framesResult.data?.length || 0);
    console.log('Using fallback:', indexedDBStorage.isUsingFallback());
  } catch (e) {
    console.error('IndexedDB error:', e);
  }

  // Check localStorage
  try {
    const oldData = localStorage.getItem('photobooth_custom_frames');
    console.log('Old localStorage data exists:', !!oldData);
    console.log('Migration flag:', localStorage.getItem('photobooth_frames_migrated'));
  } catch (e) {
    console.error('LocalStorage error:', e);
  }

  console.groupEnd();
}

/**
 * Force re-migration from localStorage to IndexedDB
 */
export async function forceRemigration() {
  console.warn('[Recovery] Forcing re-migration...');

  // Clear migration flag
  localStorage.removeItem('photobooth_frames_migrated');

  // Clear IndexedDB
  await indexedDBStorage.clearAllFrames();

  // Trigger migration
  const result = await indexedDBStorage.migrateFromLocalStorage();
  console.log('[Recovery] Re-migration result:', result);

  return result;
}

/**
 * Export all frames for backup
 */
export async function exportFrames() {
  const result = await indexedDBStorage.getAllFrames();
  if (result.data) {
    const dataStr = JSON.stringify(result.data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `photobooth-frames-backup-${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
}

/**
 * Import frames from backup
 */
export async function importFrames(file: File) {
  const text = await file.text();
  const frames = JSON.parse(text) as CustomFrame[];

  let imported = 0;
  for (const frame of frames) {
    const result = await indexedDBStorage.addFrame(frame);
    if (result.success) imported++;
  }

  console.log(`[Recovery] Imported ${imported}/${frames.length} frames`);
  return { imported, total: frames.length };
}
```

**Commit:**
```bash
git add web/src/utils/storageRecovery.ts
git commit -m "feat: add storage recovery utilities for debugging"
```

---

## Task 12: Final Review and Cleanup

**Step 1: Run type checking**

```bash
cd web && npm run type-check
# or
cd web && npx tsc --noEmit
```

**Step 2: Run linter**

```bash
cd web && npm run lint
# or
cd web && npx eslint src/
```

**Step 3: Build the project**

```bash
cd web && npm run build
```

**Step 4: Final commit**

```bash
git add web/
git commit -m "chore: final cleanup and type safety for IndexedDB implementation"
```

---

## Rollback Plan

If issues arise after deployment:

1. **Revert commits:** `git revert <commit-hash>` for each IndexedDB commit
2. **Clear IndexedDB data:** Users will need to clear site data or use DevTools
3. **Restore from backup:** localStorage data should still exist if migration didn't complete

## Success Criteria

- [ ] Custom frames persist across page refreshes
- [ ] Can upload at least 20 frames (vs previous 2-3)
- [ ] Capture speed remains fast (<1 second)
- [ ] No errors in browser console
- [ ] Migration from localStorage works seamlessly
- [ ] Fallback to localStorage works if IndexedDB unavailable
- [ ] All existing tests pass
- [ ] TypeScript compilation succeeds
