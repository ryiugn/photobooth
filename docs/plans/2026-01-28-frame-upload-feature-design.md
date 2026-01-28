# Frame Upload Feature Design

**Date**: 2026-01-28
**Author**: Claude
**Status**: Design

## Overview

Add a feature to the photobooth web application that allows users to upload custom frames/templates from their device. Uploaded frames are stored client-side in localStorage and seamlessly integrate with the existing frame selection system.

## Requirements

### Functional Requirements
- Users can upload PNG, JPEG, WebP, and SVG image files
- Users provide a custom display name for each uploaded frame
- Uploaded frames appear in the frame selection gallery immediately
- Custom frames can be deleted by users
- Custom frames can be saved in templates alongside built-in frames
- Frames persist across browser sessions via localStorage

### Non-Functional Requirements
- Max file size: 5MB per image
- Max image dimensions: 1920px (auto-resize if larger)
- Min recommended dimensions: 640x480px (warn if smaller)
- Client-side storage using localStorage (no backend required)
- Works on all modern browsers (Chrome, Firefox, Safari, Edge)

## Architecture

### Data Model

```typescript
interface CustomFrame {
  id: string;              // UUID for unique identification
  name: string;            // User-provided display name
  dataUrl: string;         // Base64-encoded image data
  type: string;            // 'image/png', 'image/webp', etc.
  createdAt: string;       // ISO timestamp
  source: 'user-upload';   // Distinguishes from built-in frames
}

interface Template {
  id: string;
  name: string;
  frames: Array<{
    id: string;
    source: 'built-in' | 'user-upload';
    dataUrl?: string;      // Stored for custom frames in templates
  }>;
  createdAt: string;
}
```

### Storage Strategy

| Key | Type | Description |
|-----|------|-------------|
| `photobooth_custom_frames` | Array | List of user-uploaded frames |
| `photobooth_templates` | Array | Existing template storage (unchanged) |

## User Flow

```
1. User lands on Frame Selection Page
   ↓
2. Clicks "Upload Custom Frame" button
   ↓
3. File picker dialog opens
   ↓
4. User selects one or more image files
   ↓
5. For each file, modal appears prompting for display name
   ↓
6. User enters name and clicks "Save" (or cancels)
   ↓
7. File is validated and processed
   ↓
8. Frame saved to localStorage
   ↓
9. Frame gallery refreshes, new frames appear
```

## UI Components

### FrameUploadButton
- Pink accent color (#FFC0CB), rounded corners
- Positioned above frame gallery
- Triggers hidden `<input type="file">` element
- Shows loading spinner during upload

### FrameNameModal
- Preview thumbnail of uploaded image
- Text input for display name
- "Save" and "Cancel" buttons
- Shows validation errors if any

### CustomFrameCard
- Same visual style as built-in frame cards
- Additional "X" button for deletion
- Displays user-provided name
- Shows "Custom" badge or indicator

### StorageUsageIndicator
- Appears when custom frames exist
- Shows "X MB / 5 MB used"
- Warns when approaching limit

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `web/src/hooks/useCustomFrames.ts` | Custom frame management hook |
| `web/src/components/FrameUploadButton.tsx` | Upload button component |
| `web/src/components/FrameNameModal.tsx` | Name prompt modal |
| `web/src/utils/imageProcessor.ts` | Image validation/compression |
| `web/src/types/frame.ts` | TypeScript type definitions |

### Modified Files

| File | Changes |
|------|---------|
| `web/src/pages/FrameSelectionPage.tsx` | Add upload UI, merge frame sources |
| `web/src/services/frameCompositor.ts` | Handle base64 data URLs |

### Frame Loading Logic

```typescript
function useAllFrames() {
  const { builtInFrames } = useBuiltInFrames(); // From API
  const { customFrames } = useCustomFrames();   // From localStorage

  return useMemo(() => {
    return [...builtInFrames, ...customFrames];
  }, [builtInFrames, customFrames]);
}
```

### Frame Application

```typescript
async function applyFrame(photo: ImageData, frame: Frame | CustomFrame) {
  const frameImg = new Image();

  if (frame.source === 'user-upload') {
    frameImg.src = frame.dataUrl; // Base64 from localStorage
  } else {
    frameImg.src = `/api/v1/frames/${frame.id}`; // API URL
  }

  await frameImg.decode();
  // Existing compositing logic continues...
}
```

## Validation & Error Handling

| Error | Message | Action |
|-------|---------|--------|
| Invalid file type | "Please select PNG, JPEG, WebP, or SVG files" | Retry upload |
| File too large | "Image must be under 5MB" | Retry upload |
| Image too small | "Image may appear blurry (less than 640x480)" | Allow with warning |
| Storage quota exceeded | "Storage full. Delete some custom frames first" | Show deletion UI |
| Corrupt image | "Could not read image file" | Retry upload |

## Testing Checklist

- [ ] Upload single PNG file
- [ ] Upload multiple files at once
- [ ] Upload JPEG, WebP, SVG formats
- [ ] Cancel name prompt modal
- [ ] Enter duplicate names
- [ ] Upload file > 5MB
- [ ] Upload file < 640x480px
- [ ] Attempt non-image file upload
- [ ] Fill localStorage quota
- [ ] Delete custom frame
- [ ] Save template with custom frame
- [ ] Load template with custom frame
- [ ] Browser refresh (persistence)
- [ ] Clear browser data

## Limitations

1. **Per-browser storage**: Custom frames are stored per device/browser
2. **No cloud sync**: Frames are lost if browser data is cleared
3. **Storage limits**: ~5-10MB depending on browser
4. **No sharing**: Cannot share custom frames with other users

## Future Enhancements

- Server-side upload with cloud storage (S3, Cloudinary)
- Public frame gallery for sharing custom frames
- Frame editing tools (crop, rotate, filters)
- Drag-and-drop upload zone
- Import/export custom frames as JSON backup
