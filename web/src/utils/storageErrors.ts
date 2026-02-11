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
