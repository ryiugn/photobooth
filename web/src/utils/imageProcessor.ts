/**
 * Image processor utility for validation, processing, and storage management
 * Handles image file operations for custom frame uploads
 */

/**
 * Result of processing an image file
 */
export interface ProcessedImageResult {
  dataUrl: string;
  width: number;
  height: number;
  size: number;
}

/**
 * Result of validating an image file
 */
export interface ValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
}

/**
 * Allowed MIME types for image uploads
 */
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'];

/**
 * Maximum file size in bytes (5MB)
 */
const MAX_FILE_SIZE = 5 * 1024 * 1024;

/**
 * Storage quota for custom frames (5MB)
 */
const STORAGE_QUOTA = 5 * 1024 * 1024;

/**
 * Storage key for custom frames
 */
const STORAGE_KEY = 'photobooth_custom_frames';

/**
 * Validates an image file against type and size constraints
 * @param file - The file to validate
 * @returns ValidationResult indicating if the file is valid and any errors/warnings
 */
export function validateImageFile(file: File): ValidationResult {
  // Check if file type is allowed
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `Invalid file type: ${file.type}. Allowed types: PNG, JPEG, WebP, SVG`
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      valid: false,
      error: `File too large: ${sizeMB}MB. Maximum size is 5MB`
    };
  }

  // Check for empty file
  if (file.size === 0) {
    return {
      valid: false,
      error: 'File is empty'
    };
  }

  // Warning for large files
  if (file.size > MAX_FILE_SIZE * 0.8) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      valid: true,
      warning: `File is large (${sizeMB}MB). Consider optimizing for better performance.`
    };
  }

  return {
    valid: true
  };
}

/**
 * Processes an image file by reading it and optionally resizing it
 * @param file - The image file to process
 * @param maxSize - Maximum dimension (width or height) for resizing. Default is 1920px
 * @returns Promise resolving to ProcessedImageResult with data URL and dimensions
 */
export function processImageFile(file: File, maxSize: number = 1920): Promise<ProcessedImageResult> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      try {
        const dataUrl = event.target?.result as string;

        // Create an image to get dimensions
        const img = new Image();

        img.onload = () => {
          let width = img.width;
          let height = img.height;
          let processedDataUrl = dataUrl;

          // Resize if image exceeds maxSize
          if (width > maxSize || height > maxSize) {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            if (!ctx) {
              reject(new Error('Failed to get canvas context'));
              return;
            }

            // Calculate new dimensions maintaining aspect ratio
            if (width > height) {
              if (width > maxSize) {
                height = (height * maxSize) / width;
                width = maxSize;
              }
            } else {
              if (height > maxSize) {
                width = (width * maxSize) / height;
                height = maxSize;
              }
            }

            canvas.width = width;
            canvas.height = height;

            // Draw resized image
            ctx.drawImage(img, 0, 0, width, height);

            // Convert back to data URL
            processedDataUrl = canvas.toDataURL(file.type);
          }

          // Calculate size of base64 string (approximately)
          const base64Length = processedDataUrl.length - (processedDataUrl.indexOf(',') + 1);
          const padding = (processedDataUrl.charAt(processedDataUrl.length - 2) === '=') ? 2 :
                         (processedDataUrl.charAt(processedDataUrl.length - 1) === '=') ? 1 : 0;
          const size = (base64Length * 0.75) - padding;

          resolve({
            dataUrl: processedDataUrl,
            width: Math.round(width),
            height: Math.round(height),
            size: Math.round(size)
          });
        };

        img.onerror = () => {
          reject(new Error('Failed to load image'));
        };

        img.src = dataUrl;
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsDataURL(file);
  });
}

/**
 * Calculates the current storage usage for custom frames
 * @returns Object with used bytes, total quota, and percentage used
 */
export function getStorageUsage(): { used: number; total: number; percentage: number } {
  try {
    const storedData = localStorage.getItem(STORAGE_KEY);
    let used = 0;

    if (storedData) {
      // Calculate size of stored data string (UTF-16 uses 2 bytes per character)
      used = storedData.length * 2;
    }

    const percentage = (used / STORAGE_QUOTA) * 100;

    return {
      used,
      total: STORAGE_QUOTA,
      percentage: Math.round(percentage * 100) / 100 // Round to 2 decimal places
    };
  } catch (error) {
    // If localStorage is not accessible, return zero usage
    return {
      used: 0,
      total: STORAGE_QUOTA,
      percentage: 0
    };
  }
}

/**
 * Checks if the storage quota is approaching or exceeded
 * @returns true if storage usage is >= 95% of quota
 */
export function isStorageQuotaExceeded(): boolean {
  const usage = getStorageUsage();
  return usage.percentage >= 95;
}
