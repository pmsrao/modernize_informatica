import { createTheme } from '@mui/material/styles';

/**
 * Theme configuration matching the design screenshots
 * - Dark blue sidebar (#1E3A5F)
 * - Light blue header (#E3F2FD)
 * - Primary blue (#4A90E2)
 */
export const theme = createTheme({
  palette: {
    primary: {
      main: '#4A90E2',
      light: '#E3F2FD',
      dark: '#2E5C8A',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#9B59B6',
      light: '#E1BEE7',
      dark: '#6C3483',
    },
    success: {
      main: '#50C878',
      light: '#C8E6C9',
      dark: '#2E7D4E',
    },
    warning: {
      main: '#FFA500',
      light: '#FFE0B2',
      dark: '#CC7700',
    },
    error: {
      main: '#E74C3C',
      light: '#FFCDD2',
      dark: '#C62828',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    },
    sidebar: {
      main: '#1E3A5F',
      light: '#4A90E2',
      contrastText: '#FFFFFF',
    },
    header: {
      main: '#E3F2FD',
      contrastText: '#212121',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif',
    h1: {
      fontSize: '32px',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '24px',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '20px',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '18px',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '14px',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '12px',
      lineHeight: 1.5,
    },
    button: {
      fontSize: '14px',
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          padding: '10px 20px',
          fontWeight: 500,
        },
        contained: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          '&:hover': {
            boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

