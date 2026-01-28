import React, { useRef } from 'react';

interface FrameUploadButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export const FrameUploadButton: React.FC<FrameUploadButtonProps> = ({
  onFilesSelected,
  disabled = false,
  isLoading = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      // Convert FileList to array and pass to callback
      const filesArray = Array.from(files);
      onFilesSelected(filesArray);

      // Reset input value to allow selecting the same file again
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled || isLoading}
        style={{
          backgroundColor: 'var(--color-primary)',
          color: '#333333',
          padding: '12px 24px',
          fontSize: '14px',
          fontWeight: 'bold',
          textTransform: 'uppercase',
          border: 'none',
          borderRadius: '8px',
          cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
          opacity: disabled || isLoading ? 0.6 : 1,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'opacity 0.2s ease',
        }}
      >
        {isLoading ? (
          <>
            <span style={{ animation: 'spin 1s linear infinite' }}>↻</span>
            UPLOADING...
          </>
        ) : (
          '+ UPLOAD CUSTOM FRAME'
        )}
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/svg+xml"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileChange}
        disabled={disabled || isLoading}
      />

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};
