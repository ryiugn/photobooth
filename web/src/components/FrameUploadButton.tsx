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
        className="btn"
        style={{
          backgroundColor: '#E3F2FD',
          color: 'var(--color-text-dark)',
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
