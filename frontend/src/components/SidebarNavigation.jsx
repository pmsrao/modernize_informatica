import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Folder as RepositoryIcon,
  Settings as ParseIcon,
  AccountTree as CanonicalIcon,
  Timeline as LineageIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

/**
 * Sidebar Navigation Component
 * 
 * Dark blue sidebar with vertical navigation menu matching the design screenshots.
 * Supports navigation between different steps/views in the modernization journey.
 */
export default function SidebarNavigation({ currentStep, onStepChange }) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      id: 1,
      label: 'Upload Files',
      icon: <UploadIcon />,
      step: 1,
      path: '/modern/',
    },
    {
      id: 2,
      label: 'Repository',
      icon: <RepositoryIcon />,
      step: 2,
      path: '/modern/',
    },
    {
      id: 3,
      label: 'Parse & AI Enhance',
      icon: <ParseIcon />,
      step: 3,
      path: '/modern/',
    },
    {
      id: 4,
      label: 'Canonical Model',
      icon: <CanonicalIcon />,
      step: 4,
      path: '/modern/',
    },
    {
      id: 5,
      label: 'Lineage',
      icon: <LineageIcon />,
      step: 5,
      path: '/modern/',
    },
    {
      id: 6,
      label: 'Generated Code',
      icon: <CodeIcon />,
      step: 6,
      path: '/modern/',
    },
  ];

  const handleItemClick = (item) => {
    if (onStepChange) {
      onStepChange(item.step);
    }
    // Also update URL if needed
    if (item.path) {
      navigate(item.path);
    }
  };

  return (
    <Box
      sx={{
        width: 240,
        height: '100vh',
        backgroundColor: '#1E3A5F',
        color: '#FFFFFF',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 1000,
        boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
      }}
    >
      {/* Application Title */}
      <Box
        sx={{
          padding: '20px 16px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            fontSize: '16px',
            color: '#FFFFFF',
            lineHeight: 1.2,
          }}
        >
          INFORMATICA
          <br />
          MODERNIZATION
          <br />
          ACCELERATOR
        </Typography>
      </Box>

      {/* Navigation Menu */}
      <List
        sx={{
          flex: 1,
          padding: '8px 0',
          overflowY: 'auto',
        }}
      >
        {menuItems.map((item) => {
          const isActive = currentStep === item.step;
          
          return (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                onClick={() => handleItemClick(item)}
                sx={{
                  minHeight: 56,
                  padding: '12px 16px',
                  backgroundColor: isActive ? '#4A90E2' : 'transparent',
                  color: '#FFFFFF',
                  '&:hover': {
                    backgroundColor: isActive ? '#4A90E2' : 'rgba(255,255,255,0.1)',
                  },
                  borderLeft: isActive ? '4px solid #FFFFFF' : '4px solid transparent',
                  transition: 'all 0.2s',
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: '#FFFFFF',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '14px',
                    fontWeight: isActive ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Optional: Footer or additional info */}
      <Box
        sx={{
          padding: '16px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          fontSize: '12px',
          color: 'rgba(255,255,255,0.7)',
        }}
      >
        <Typography variant="body2" sx={{ fontSize: '11px' }}>
          Step {currentStep} of 6
        </Typography>
      </Box>
    </Box>
  );
}

