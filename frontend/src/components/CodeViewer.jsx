import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Box, Paper, IconButton, Tooltip } from '@mui/material';
import { ContentCopy as CopyIcon, Check as CheckIcon } from '@mui/icons-material';

/**
 * Code Viewer Component
 * 
 * Displays code with syntax highlighting and copy functionality.
 */
export default function CodeViewer({ code, language = 'python', filename = null }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Paper
      sx={{
        border: '1px solid #E0E0E0',
        borderRadius: '8px',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {filename && (
        <Box
          sx={{
            padding: '8px 16px',
            background: '#F5F5F5',
            borderBottom: '1px solid #E0E0E0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Box sx={{ fontSize: '13px', fontWeight: 600, color: '#212121' }}>
            {filename}
          </Box>
          <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
            <IconButton
              size="small"
              onClick={handleCopy}
              sx={{
                color: copied ? '#4CAF50' : '#757575',
                '&:hover': {
                  backgroundColor: 'rgba(0,0,0,0.04)',
                },
              }}
            >
              {copied ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Box>
      )}
      <Box
        sx={{
          maxHeight: '600px',
          overflow: 'auto',
          '& pre': {
            margin: 0,
            padding: '16px',
            fontSize: '13px',
            lineHeight: 1.6,
          },
        }}
      >
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '16px',
            background: '#1E1E1E',
          }}
        >
          {code || '// No code available'}
        </SyntaxHighlighter>
      </Box>
    </Paper>
  );
}

