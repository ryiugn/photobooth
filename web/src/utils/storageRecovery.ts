/**
 * Storage recovery utilities for debugging and fixing storage issues
 */

import { indexedDBStorage } from './indexedDBStorage';
import type { CustomFrame } from '../types';

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
