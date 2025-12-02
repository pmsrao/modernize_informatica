import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Select,
  FormControl,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
} from '@mui/icons-material';

/**
 * Top Header Component
 * 
 * Light blue header bar with logo, tenant selector, notifications, and profile.
 * Matches the design from screenshot 2.
 */
export default function TopHeader({ 
  tenant = 'apple.inc',
  onTenantChange,
  onUploadClick,
  notificationCount = 0,
}) {
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [tenantValue, setTenantValue] = React.useState(tenant);

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleTenantChange = (event) => {
    setTenantValue(event.target.value);
    if (onTenantChange) {
      onTenantChange(event.target.value);
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        top: 0,
        left: 240, // Account for sidebar width
        width: 'calc(100% - 240px)',
        backgroundColor: '#E3F2FD',
        color: '#212121',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        zIndex: 1100,
      }}
    >
      <Toolbar
        sx={{
          minHeight: '64px !important',
          padding: '0 24px',
          justifyContent: 'space-between',
        }}
      >
        {/* Left: Logo/Brand */}
        <Typography
          variant="h6"
          component="div"
          sx={{
            fontWeight: 700,
            fontSize: '20px',
            color: '#4A90E2',
            flexGrow: 0,
          }}
        >
          BiCXO
        </Typography>

        {/* Center: Tenant/Project Selector */}
        <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
          <FormControl
            variant="outlined"
            size="small"
            sx={{
              minWidth: 200,
              backgroundColor: 'white',
              borderRadius: '4px',
            }}
          >
            <Select
              value={tenantValue}
              onChange={handleTenantChange}
              displayEmpty
              sx={{
                height: '36px',
                fontSize: '14px',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#BDBDBD',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#4A90E2',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#4A90E2',
                },
              }}
            >
              <MenuItem value="apple.inc">apple.inc</MenuItem>
              <MenuItem value="tenant2">Tenant 2</MenuItem>
              <MenuItem value="tenant3">Tenant 3</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Right: Actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Upload Icon */}
          <IconButton
            color="inherit"
            onClick={onUploadClick}
            sx={{
              color: '#4A90E2',
              '&:hover': {
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
              },
            }}
            title="Upload Files"
          >
            <UploadIcon />
          </IconButton>

          {/* Notifications */}
          <IconButton
            color="inherit"
            sx={{
              color: '#4A90E2',
              '&:hover': {
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
              },
            }}
            title="Notifications"
          >
            <Badge badgeContent={notificationCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* Profile */}
          <IconButton
            onClick={handleProfileMenuOpen}
            sx={{
              color: '#4A90E2',
              padding: 0,
              '&:hover': {
                backgroundColor: 'transparent',
              },
            }}
            title="Profile"
          >
            <Avatar
              sx={{
                width: 36,
                height: 36,
                backgroundColor: '#4A90E2',
                fontSize: '16px',
              }}
            >
              <AccountIcon />
            </Avatar>
          </IconButton>

          {/* Profile Menu */}
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem onClick={handleMenuClose}>Profile</MenuItem>
            <MenuItem onClick={handleMenuClose}>Settings</MenuItem>
            <MenuItem onClick={handleMenuClose}>Logout</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

