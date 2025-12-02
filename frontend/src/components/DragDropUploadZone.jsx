import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Button,
  Paper,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';

/**
 * Drag and Drop Upload Zone Component
 * 
 * Matches the design from screenshot 2:
 * - Large dashed border upload zone
 * - Cloud icon with up arrow
 * - "Drag & Drop Files Here" text
 * - "or browse to upload XML files" instruction
 * - "Browse Files" button
 */
export default function DragDropUploadZone({ onFilesSelected, disabled = false }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFilesSelected(acceptedFiles);
    }
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    noClick: true, // Don't open file dialog on click, use button instead
    noKeyboard: true,
    disabled,
    accept: {
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
    },
  });

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        {...getRootProps()}
        sx={{
          border: '2px dashed #4A90E2',
          borderRadius: '8px',
          padding: '60px 40px',
          textAlign: 'center',
          backgroundColor: isDragActive ? '#E3F2FD' : '#FFFFFF',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
          '&:hover': {
            backgroundColor: disabled ? '#FFFFFF' : '#F5F5F5',
            borderColor: disabled ? '#4A90E2' : '#2E5C8A',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <CloudUploadIcon
          sx={{
            fontSize: '64px',
            color: '#4A90E2',
            marginBottom: '20px',
          }}
        />
        
        <Typography
          variant="h6"
          sx={{
            fontSize: '18px',
            fontWeight: 600,
            color: '#212121',
            marginBottom: '8px',
          }}
        >
          Drag & Drop Files Here
        </Typography>
        
        <Typography
          variant="body2"
          sx={{
            fontSize: '14px',
            color: '#757575',
            marginBottom: '24px',
          }}
        >
          or browse to upload XML files
        </Typography>
        
        <Button
          variant="contained"
          onClick={(e) => {
            e.stopPropagation();
            if (!disabled) {
              open();
            }
          }}
          disabled={disabled}
          sx={{
            padding: '12px 32px',
            fontSize: '16px',
            fontWeight: 600,
            backgroundColor: '#4A90E2',
            '&:hover': {
              backgroundColor: '#2E5C8A',
            },
          }}
        >
          Browse Files
        </Button>
      </Paper>
    </Box>
  );
}

