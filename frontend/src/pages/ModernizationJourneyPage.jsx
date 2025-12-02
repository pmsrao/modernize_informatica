import React, { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { Box, CssBaseline, Typography, Paper, Button, Chip, Card, CardContent, IconButton, Grid, Tabs, Tab, Alert, AlertTitle, Divider } from '@mui/material';
import { CheckCircle as CheckCircleIcon, ArrowBack as ArrowBackIcon, ArrowForward as ArrowForwardIcon, ChevronLeft as ChevronLeftIcon, ChevronRight as ChevronRightIcon, Timeline as TimelineIcon, Code as CodeIcon, Warning as WarningIcon, Error as ErrorIcon, Info as InfoIcon, Lightbulb as LightbulbIcon } from '@mui/icons-material';
import RepositoryViewPage from './RepositoryViewPage.jsx';
import GraphExplorerPage from './GraphExplorerPage.jsx';
import LineagePage from './LineagePage.jsx';
import apiClient from '../services/api.js';
import SidebarNavigation from '../components/SidebarNavigation.jsx';
import TopHeader from '../components/TopHeader.jsx';
import DragDropUploadZone from '../components/DragDropUploadZone.jsx';
import CodeViewer from '../components/CodeViewer.jsx';
import { theme } from '../theme.js';

/**
 * Modernization Journey Page
 * 
 * Provides a step-by-step guided journey through the modernization process:
 * 1. Upload files from folder
 * 2. Visualize mapping files (repo view)
 * 3. Parse and Enhance with AI (creates canonical model)
 * 4. Visualize Canonical Model
 * 5. Navigate to Lineage
 * 6. Generate Target Code
 * 7. Enhance/Fix with AI
 */
export default function ModernizationJourneyPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [parsedMappings, setParsedMappings] = useState([]);
  const [selectedMapping, setSelectedMapping] = useState(null);
  const [canonicalModel, setCanonicalModel] = useState(null);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [generatedCodeFiles, setGeneratedCodeFiles] = useState([]); // Store all generated code files
  const [selectedCodeFile, setSelectedCodeFile] = useState(null);
  const [activeCodeTab, setActiveCodeTab] = useState('pyspark');
  const [selectedGeneratedFile, setSelectedGeneratedFile] = useState(null); // { mapping, type }
  const [codeReviewResults, setCodeReviewResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [workflowFiles, setWorkflowFiles] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // Listen for navigation events from other pages
  useEffect(() => {
    const handleNavigate = (event) => {
      if (event.detail && event.detail.step) {
        setCurrentStep(event.detail.step);
      }
    };
    window.addEventListener('navigateToStep', handleNavigate);
    return () => window.removeEventListener('navigateToStep', handleNavigate);
  }, []);

  useEffect(() => {
    loadFiles();
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const result = await apiClient.getGraphStatistics();
      if (result.success) {
        setStatistics(result.statistics);
      }
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  };

  const loadFiles = async () => {
    try {
      const result = await apiClient.listAllFiles();
      if (result.success) {
        setFiles(result.files || []);
        // Store workflow files for lineage navigation
        setWorkflowFiles(result.files?.filter(f => f.file_type === 'workflow') || []);
      }
    } catch (err) {
      console.error('Error loading files:', err);
    }
  };

  const handleDirectoryUpload = async (event) => {
    const selectedFiles = Array.from(event.target.files);
    if (selectedFiles.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        if (file.name.endsWith('.xml')) {
          formData.append('files', file);
        }
      });

      const result = await apiClient.uploadDirectory(formData);
      
      if (result.success) {
        await loadFiles();
        setCurrentStep(2); // Move to next step
      }
    } catch (err) {
      setError(err.message || 'Directory upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleParseAndEnhance = async (fileId) => {
    setLoading(true);
    setError(null);

    try {
      // Determine file type
      const fileInfo = await apiClient.getFileInfo(fileId);
      const fileType = fileInfo.file_type;

      let result;
      if (fileType === 'mapping') {
        result = await apiClient.parseMapping(fileId, true); // enhance_model = true
      } else if (fileType === 'workflow') {
        result = await apiClient.parseWorkflow(fileId);
      } else if (fileType === 'session') {
        result = await apiClient.parseSession(fileId);
      } else if (fileType === 'worklet') {
        result = await apiClient.parseWorklet(fileId);
      }

      if (result && result.success) {
        // Reload mappings list
        const mappingsResult = await apiClient.listMappings();
        if (mappingsResult.success) {
          setParsedMappings(mappingsResult.mappings || []);
        }
        // Reload files to refresh the list
        await loadFiles();
        
        // For mappings, automatically show canonical model if available
        if (fileType === 'mapping' && result.mapping_name) {
          setSelectedMapping(result.mapping_name);
          setCurrentStep(4); // Move to canonical model visualization
        } else {
          // For other types, show success message
          setCurrentStep(3); // Show parse success step
        }
        return result; // Return result for bulk operations
      } else {
        throw new Error(result?.message || result?.errors?.join(', ') || 'Parse failed');
      }
    } catch (err) {
      setError(err.message || 'Parse failed');
    } finally {
      setLoading(false);
    }
  };

  const handleViewCanonicalModel = async (mappingName) => {
    setSelectedMapping(mappingName);
    setCurrentStep(4);
  };

  const handleViewLineage = async () => {
    // Get workflow files
    const workflowFiles = files.filter(f => f.file_type === 'workflow');
    
    if (workflowFiles.length === 0) {
      alert('No workflow files found. Please upload workflow XML files to view lineage.');
      return;
    }
    
    if (workflowFiles.length === 1) {
      // Navigate to lineage view with the single workflow
      window.location.href = `#/lineage?fileId=${workflowFiles[0].file_id}`;
    } else {
      // Multiple workflows - let user choose
      const workflowNames = workflowFiles.map(f => f.filename).join('\n');
      const choice = prompt(`Multiple workflow files found:\n\n${workflowNames}\n\nEnter the filename to view lineage for:`, workflowFiles[0].filename);
      if (choice) {
        const selectedFile = workflowFiles.find(f => f.filename === choice || f.filename.includes(choice));
        if (selectedFile) {
          window.location.href = `#/lineage?fileId=${selectedFile.file_id}`;
        } else {
          alert('Workflow file not found. Please try again.');
        }
      }
    }
  };

  const handleGenerateCode = async (mappingName, codeType = 'pyspark') => {
    setLoading(true);
    setError(null);

    try {
      let result;
      if (codeType === 'pyspark') {
        result = await apiClient.generatePySpark(mappingName);
      } else if (codeType === 'dlt') {
        result = await apiClient.generateDLT(mappingName);
      } else if (codeType === 'sql') {
        result = await apiClient.generateSQL(mappingName);
      }

      if (result.success) {
        const code = result.code || result.result;
        const codeFile = {
          mapping: mappingName,
          type: codeType,
          code: code,
          language: result.language || codeType,
          timestamp: new Date().toISOString()
        };
        
        // Add or update in the list
        setGeneratedCodeFiles(prev => {
          const filtered = prev.filter(f => !(f.mapping === mappingName && f.type === codeType));
          return [...filtered, codeFile];
        });
        
        setGeneratedCode(code);
        setSelectedCodeFile(codeFile);
        setSelectedMapping(mappingName);
        setSelectedGeneratedFile({ mapping: mappingName, type: codeType });
        setActiveCodeTab(codeType);
        setCurrentStep(6);
      }
    } catch (err) {
      setError(err.message || 'Code generation failed');
    } finally {
      setLoading(false);
    }
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'mapping': '📋',
      'workflow': '🔄',
      'session': '⚙️',
      'worklet': '📦',
      'unknown': '📄'
    };
    return icons[type] || icons.unknown;
  };

  const getFileTypeColor = (type) => {
    const colors = {
      'mapping': '#4A90E2',
      'workflow': '#50C878',
      'session': '#FFA500',
      'worklet': '#9B59B6',
      'unknown': '#95A5A6'
    };
    return colors[type] || colors.unknown;
  };

  // Step 1: Upload Files - Enhanced to match design
  const renderUploadStep = () => (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Top Action Bar - Similar to Repository View */}
      <Box sx={{ 
        padding: '12px 20px', 
        background: 'white', 
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        justifyContent: 'flex-end',
        flexWrap: 'wrap'
      }}>
        <Button
          variant="contained"
          onClick={() => setCurrentStep(2)}
          sx={{
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 600,
            backgroundColor: '#4A90E2',
            '&:hover': {
              backgroundColor: '#2E5C8A',
            },
          }}
        >
          Repository View
        </Button>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, overflow: 'auto', padding: '40px', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        <DragDropUploadZone
          onFilesSelected={async (selectedFiles) => {
            if (selectedFiles.length === 0) return;

            setLoading(true);
            setError(null);

            try {
              const formData = new FormData();
              selectedFiles.forEach(file => {
                if (file.name.endsWith('.xml')) {
                  formData.append('files', file);
                }
              });

              const result = await apiClient.uploadDirectory(formData);
              
              if (result.success) {
                await loadFiles();
              }
            } catch (err) {
              setError(err.message || 'Directory upload failed');
            } finally {
              setLoading(false);
            }
          }}
          disabled={loading}
        />
        
        {/* Also support folder upload for directory structure */}
        <Box sx={{ marginTop: '24px', textAlign: 'center' }}>
          <input
            type="file"
            multiple
            directory=""
            webkitdirectory=""
            onChange={handleDirectoryUpload}
            style={{ display: 'none' }}
            id="directory-upload"
          />
          <Button
            component="label"
            htmlFor="directory-upload"
            variant="outlined"
            sx={{
              padding: '10px 24px',
              fontSize: '14px',
              borderColor: '#4A90E2',
              color: '#4A90E2',
              '&:hover': {
                borderColor: '#2E5C8A',
                backgroundColor: 'rgba(74, 144, 226, 0.04)',
              },
            }}
          >
            📁 Select Folder to Upload
          </Button>
          <Typography
            variant="body2"
            sx={{
              marginTop: '12px',
              color: '#757575',
              fontSize: '13px',
            }}
          >
            Select a folder containing Informatica XML files (workflows, worklets, sessions, mappings)
          </Typography>
        </Box>

        {files.length > 0 && (
          <Box sx={{ marginTop: '40px' }}>
            <Typography
              variant="h4"
              sx={{
                fontSize: '18px',
                fontWeight: 600,
                marginBottom: '16px',
                color: '#212121',
              }}
            >
              Uploaded Files ({files.length})
            </Typography>
            <Paper
              sx={{
                border: '1px solid #E0E0E0',
                borderRadius: '6px',
                maxHeight: '300px',
                overflow: 'auto',
              }}
            >
              {files.map(file => (
                <Box
                  key={file.file_id}
                  sx={{
                    padding: '12px 16px',
                    borderBottom: '1px solid #F5F5F5',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    '&:last-child': {
                      borderBottom: 'none',
                    },
                  }}
                >
                  <Typography sx={{ fontSize: '20px' }}>
                    {getFileTypeIcon(file.file_type)}
                  </Typography>
                  <Typography
                    sx={{
                      flex: 1,
                      fontSize: '14px',
                      color: '#212121',
                    }}
                  >
                    {file.filename}
                  </Typography>
                  <Box
                    sx={{
                      padding: '4px 8px',
                      background: getFileTypeColor(file.file_type),
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}
                  >
                    {file.file_type.toUpperCase()}
                  </Box>
                </Box>
              ))}
            </Paper>
          </Box>
        )}
      </Box>
    </Box>
  );

  // Step 2: Repository View
  const renderRepositoryView = () => {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <RepositoryViewPage
            onBackClick={() => setCurrentStep(1)}
            files={files}
            onParseAndEnhance={handleParseAndEnhance}
            onFileAction={async (file) => {
              // Handle file action - navigate to appropriate view based on file type
              try {
                if (file.file_type === 'mapping') {
                  // For mappings, check if it's already parsed, if not parse it first
                  const mappingsResult = await apiClient.listMappings();
                  const mappingName = file.filename.replace('.xml', '').replace('mapping_', 'M_');
                  const existingMapping = mappingsResult.mappings?.find(m => m.name === mappingName);
                  
                  if (existingMapping) {
                    handleViewCanonicalModel(mappingName);
                  } else {
                    // Parse first, then view
                    await handleParseAndEnhance(file.file_id);
                    // After parsing, the mapping should be available
                    setTimeout(() => {
                      handleViewCanonicalModel(mappingName);
                    }, 1000);
                  }
                } else if (file.file_type === 'workflow') {
                  // For workflows, navigate to lineage view
                  window.location.href = `#/lineage?fileId=${file.file_id}`;
                } else if (file.file_type === 'session') {
                  // For sessions, show file details and allow parsing
                  const fileInfo = await apiClient.getFileInfo(file.file_id);
                  const details = `File: ${file.filename}\nType: ${file.file_type}\nSize: ${(file.size / 1024).toFixed(2)} KB\n\nWould you like to parse this session?`;
                  if (confirm(details)) {
                    await handleParseAndEnhance(file.file_id);
                  }
                } else {
                  // For other types, show file info
                  const fileInfo = await apiClient.getFileInfo(file.file_id);
                  alert(`File: ${file.filename}\nType: ${file.file_type}\nSize: ${(file.size / 1024).toFixed(2)} KB\nID: ${file.file_id}`);
                }
              } catch (err) {
                setError(err.message || 'Failed to process file action');
              }
            }}
          />
        </Box>
        {parsedMappings.length > 0 && (
          <Box sx={{ padding: '16px 20px', background: '#E8F5E9', borderTop: '1px solid #C8E6C9' }}>
            <Typography variant="h6" sx={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#212121' }}>
              ✅ Parsed Mappings ({parsedMappings.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
              {parsedMappings.map(m => (
                <Chip
                  key={m.name}
                  label={m.name}
                  onClick={() => handleViewCanonicalModel(m.name)}
                  sx={{
                    backgroundColor: '#4A90E2',
                    color: 'white',
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: '#2E5C8A',
                    },
                  }}
                />
              ))}
            </Box>
            <Typography variant="body2" sx={{ color: '#666', fontSize: '13px' }}>
              Click on a mapping to view its canonical model and proceed to code generation
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  // Step 3: Parse & Enhance Success - Enhanced to match design
  const renderParseSuccess = () => {
    return (
      <Box sx={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
        <Card
          sx={{
            padding: '40px',
            textAlign: 'center',
            background: 'linear-gradient(135deg, #E8F5E9 0%, #FFFFFF 100%)',
            border: '2px solid #4CAF50',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}
        >
          <CheckCircleIcon
            sx={{
              fontSize: '80px',
              color: '#4CAF50',
              marginBottom: '20px',
            }}
          />
          <Typography
            variant="h3"
            sx={{
              fontSize: '24px',
              fontWeight: 700,
              color: '#212121',
              marginBottom: '12px',
            }}
          >
            Parse & Enhance Complete!
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#757575',
              marginBottom: '30px',
              fontSize: '14px',
            }}
          >
            The file has been parsed and the canonical model has been created and enhanced with AI.
          </Typography>

          {parsedMappings.length > 0 && (
            <Box sx={{ marginBottom: '30px' }}>
              <Typography
                variant="h4"
                sx={{
                  fontSize: '18px',
                  fontWeight: 600,
                  color: '#212121',
                  marginBottom: '20px',
                }}
              >
                Available Mappings ({parsedMappings.length})
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '10px',
                  justifyContent: 'center',
                }}
              >
                {parsedMappings.map(m => (
                  <Chip
                    key={m.name}
                    label={m.name}
                    onClick={() => handleViewCanonicalModel(m.name)}
                    sx={{
                      padding: '10px 20px',
                      height: 'auto',
                      backgroundColor: '#4A90E2',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: '#2E5C8A',
                        transform: 'scale(1.05)',
                      },
                      transition: 'all 0.2s',
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '30px' }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => setCurrentStep(2)}
              sx={{
                padding: '12px 24px',
                fontSize: '16px',
                borderColor: '#757575',
                color: '#757575',
                '&:hover': {
                  borderColor: '#424242',
                  backgroundColor: 'rgba(117, 117, 117, 0.04)',
                },
              }}
            >
              Back to Repository
            </Button>
            {parsedMappings.length > 0 && (
              <Button
                variant="contained"
                endIcon={<ArrowForwardIcon />}
                onClick={() => handleViewCanonicalModel(parsedMappings[0].name)}
                sx={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: 600,
                  backgroundColor: '#4A90E2',
                  '&:hover': {
                    backgroundColor: '#2E5C8A',
                  },
                }}
              >
                View Canonical Model
              </Button>
            )}
          </Box>
        </Card>
      </Box>
    );
  };
  
  // Step 4: Canonical Model Visualization - Enhanced to match design
  const renderCanonicalModelView = () => {
    if (!selectedMapping) {
      // If no mapping selected, show message
      return (
        <Box sx={{ padding: '40px', textAlign: 'center' }}>
          <Typography variant="h4" sx={{ marginBottom: '20px', color: '#757575' }}>
            No mapping selected
          </Typography>
          <Button
            variant="contained"
            onClick={() => setCurrentStep(2)}
            sx={{
              backgroundColor: '#4A90E2',
              '&:hover': { backgroundColor: '#2E5C8A' },
            }}
          >
            Go to Repository to Select a Mapping
          </Button>
        </Box>
      );
    }

    // Get current mapping index for navigation
    const currentIndex = parsedMappings.findIndex(m => m.name === selectedMapping);
    const canGoPrev = currentIndex > 0;
    const canGoNext = currentIndex < parsedMappings.length - 1;

    const handlePrevMapping = () => {
      if (canGoPrev) {
        handleViewCanonicalModel(parsedMappings[currentIndex - 1].name);
      }
    };

    const handleNextMapping = () => {
      if (canGoNext) {
        handleViewCanonicalModel(parsedMappings[currentIndex + 1].name);
      }
    };

    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Single Action Bar - Similar to Repository View */}
        <Box sx={{ 
          padding: '12px 20px', 
          background: 'white', 
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap'
        }}>
          {/* Left side: Mapping Selector */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <Typography variant="body2" sx={{ fontSize: '13px', color: '#666', marginRight: '4px' }}>
              Mapping:
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <IconButton
                onClick={handlePrevMapping}
                disabled={!canGoPrev}
                size="small"
                sx={{
                  color: canGoPrev ? '#4A90E2' : '#BDBDBD',
                  padding: '4px',
                  '&:hover': {
                    backgroundColor: canGoPrev ? 'rgba(74, 144, 226, 0.1)' : 'transparent',
                  },
                }}
              >
                <ChevronLeftIcon fontSize="small" />
              </IconButton>
              <Typography
                variant="body1"
                sx={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#4A90E2',
                  minWidth: '180px',
                  textAlign: 'center',
                }}
              >
                {selectedMapping}
              </Typography>
              <IconButton
                onClick={handleNextMapping}
                disabled={!canGoNext}
                size="small"
                sx={{
                  color: canGoNext ? '#4A90E2' : '#BDBDBD',
                  padding: '4px',
                  '&:hover': {
                    backgroundColor: canGoNext ? 'rgba(74, 144, 226, 0.1)' : 'transparent',
                  },
                }}
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            </Box>
            <Typography variant="caption" sx={{ color: '#757575', fontSize: '12px' }}>
              {currentIndex + 1} of {parsedMappings.length}
            </Typography>
          </Box>

          {/* Right side: Action Buttons */}
          <Box sx={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              onClick={async () => {
                if (workflowFiles.length === 0) {
                  alert('No workflow files found. Please upload a workflow file to view lineage.\n\nLineage shows workflow-level dependencies (Workflow → Worklet → Session → Mapping).');
                  return;
                }
                
                let selectedWorkflow = null;
                if (workflowFiles.length === 1) {
                  selectedWorkflow = workflowFiles[0];
                } else {
                  const workflowList = workflowFiles.map((wf, idx) => `${idx + 1}. ${wf.filename} (ID: ${wf.file_id})`).join('\n');
                  const choice = prompt(`Multiple workflows found. Please enter the workflow number (1-${workflowFiles.length}) or file ID:\n\n${workflowList}\n\nOr click Cancel to use the first one.`);
                  if (choice === null || choice === '') {
                    selectedWorkflow = workflowFiles[0];
                  } else {
                    const choiceNum = parseInt(choice);
                    if (!isNaN(choiceNum) && choiceNum >= 1 && choiceNum <= workflowFiles.length) {
                      selectedWorkflow = workflowFiles[choiceNum - 1];
                    } else {
                      selectedWorkflow = workflowFiles.find(wf => wf.file_id === choice || wf.filename === choice);
                    }
                    if (!selectedWorkflow) {
                      alert('Invalid selection. Using first workflow.');
                      selectedWorkflow = workflowFiles[0];
                    }
                  }
                }
                
                if (selectedWorkflow) {
                  // Store file ID for LineagePage to use
                  localStorage.setItem('lastUploadedFileId', selectedWorkflow.file_id);
                  // Navigate to Step 5 (Lineage)
                  setCurrentStep(5);
                }
              }}
              style={{
                padding: '8px 16px',
                background: '#50C878',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap'
              }}
            >
              <span>📊</span>
              <span>View Lineage</span>
            </button>
            <button
              onClick={() => handleGenerateCode(selectedMapping, 'pyspark')}
              style={{
                padding: '8px 16px',
                background: '#4A90E2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap'
              }}
            >
              <span>💻</span>
              <span>Generate Code</span>
            </button>
          </Box>
        </Box>

        {/* Main Content Area - Scrollable */}
        <Box sx={{ flex: 1, overflow: 'auto', padding: '20px' }}>

          {/* Statistics Panel */}
          {statistics && (
            <Grid container spacing={2} sx={{ marginBottom: '20px' }}>
              <Grid item xs={4}>
                <Card
                  sx={{
                    padding: '16px',
                    textAlign: 'center',
                    backgroundColor: '#E3F2FD',
                    border: '1px solid #4A90E2',
                  }}
                >
                  <Typography variant="h6" sx={{ fontSize: '24px', fontWeight: 700, color: '#4A90E2' }}>
                    {statistics.total_mappings || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#757575', fontSize: '13px' }}>
                    Total Mappings
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={4}>
                <Card
                  sx={{
                    padding: '16px',
                    textAlign: 'center',
                    backgroundColor: '#FFF3E0',
                    border: '1px solid #FFA500',
                  }}
                >
                  <Typography variant="h6" sx={{ fontSize: '24px', fontWeight: 700, color: '#FFA500' }}>
                    {statistics.total_transformations || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#757575', fontSize: '13px' }}>
                    Total Transformations
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={4}>
                <Card
                  sx={{
                    padding: '16px',
                    textAlign: 'center',
                    backgroundColor: '#E8F5E9',
                    border: '1px solid #50C878',
                  }}
                >
                  <Typography variant="h6" sx={{ fontSize: '24px', fontWeight: 700, color: '#50C878' }}>
                    {statistics.total_tables || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#757575', fontSize: '13px' }}>
                    Total Tables
                  </Typography>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Graph Explorer */}
          <Box
            sx={{
              flex: 1,
              border: '1px solid #E0E0E0',
              borderRadius: '8px',
              background: 'white',
              overflow: 'hidden',
              position: 'relative',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              minHeight: '500px',
            }}
          >
            <GraphExplorerPage initialMapping={selectedMapping} />
          </Box>
        </Box>
      </Box>
    );
  };

  // Step 5: Lineage (handled by separate page)
  
  // Step 6: Generated Code - Enhanced with file list and tabs
  const renderCodeGeneration = () => {
    // Group generated files by mapping
    const filesByMapping = {};
    generatedCodeFiles.forEach(file => {
      if (!filesByMapping[file.mapping]) {
        filesByMapping[file.mapping] = [];
      }
      filesByMapping[file.mapping].push(file);
    });

    // Get code for current tab
    const getCodeForTab = (tabType) => {
      if (!selectedGeneratedFile) return null;
      const file = generatedCodeFiles.find(
        f => f.mapping === selectedGeneratedFile.mapping && f.type === tabType
      );
      return file ? file.code : null;
    };

    const handleFileSelect = (mapping, type) => {
      setSelectedGeneratedFile({ mapping, type });
      setSelectedMapping(mapping);
      setActiveCodeTab(type);
      const file = generatedCodeFiles.find(f => f.mapping === mapping && f.type === type);
      if (file) {
        setGeneratedCode(file.code);
        setSelectedCodeFile(file);
      }
    };

    const handleTabChange = async (event, newValue) => {
      setActiveCodeTab(newValue);
      if (selectedGeneratedFile) {
        // Check if code exists for this tab
        const existingCode = getCodeForTab(newValue);
        if (!existingCode) {
          // Generate code for the selected tab
          await handleGenerateCode(selectedGeneratedFile.mapping, newValue);
        } else {
          // Just switch to existing code
          const file = generatedCodeFiles.find(
            f => f.mapping === selectedGeneratedFile.mapping && f.type === newValue
          );
          if (file) {
            setSelectedCodeFile(file);
            setGeneratedCode(file.code);
          }
        }
      }
    };

    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ 
          padding: '12px 20px', 
          background: 'white', 
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h4" sx={{ fontSize: '20px', fontWeight: 600, color: '#212121' }}>
            Generated Code
          </Typography>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => {
              setSelectedGeneratedFile(null);
              setSelectedMapping(null);
              setCurrentStep(4);
            }}
            sx={{
              borderColor: '#757575',
              color: '#757575',
              '&:hover': {
                borderColor: '#424242',
                backgroundColor: 'rgba(117, 117, 117, 0.04)',
              },
            }}
          >
            Back
          </Button>
        </Box>

        {/* Main Content */}
        <Box sx={{ flex: 1, overflow: 'auto', padding: '20px' }}>
          {Object.keys(filesByMapping).length === 0 ? (
            <Card
              sx={{
                padding: '40px',
                textAlign: 'center',
                background: '#FFF3E0',
                border: '2px solid #FFA500',
                borderRadius: '8px',
                maxWidth: '600px',
                margin: '40px auto',
              }}
            >
              <Typography variant="h5" sx={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#212121' }}>
                📋 No Generated Code Files
              </Typography>
              <Typography variant="body2" sx={{ marginBottom: '20px', color: '#757575' }}>
                Generate code from the Canonical Model view to see files here.
              </Typography>
              <Button
                variant="contained"
                onClick={() => setCurrentStep(4)}
                sx={{
                  backgroundColor: '#4A90E2',
                  '&:hover': { backgroundColor: '#2E5C8A' },
                }}
              >
                Go to Canonical Model
              </Button>
            </Card>
          ) : (
            <Box sx={{ display: 'flex', gap: '20px', height: '100%' }}>
              {/* File List Sidebar */}
              <Box sx={{ 
                width: '300px', 
                flexShrink: 0,
                border: '1px solid #E0E0E0',
                borderRadius: '8px',
                background: 'white',
                padding: '16px',
                maxHeight: 'calc(100vh - 200px)',
                overflow: 'auto'
              }}>
                <Typography variant="h6" sx={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: '#212121' }}>
                  Generated Files ({generatedCodeFiles.length})
                </Typography>
                {Object.entries(filesByMapping).map(([mapping, files]) => (
                  <Box key={mapping} sx={{ marginBottom: '20px' }}>
                    <Typography variant="subtitle2" sx={{ fontSize: '13px', fontWeight: 600, color: '#757575', marginBottom: '8px' }}>
                      {mapping}
                    </Typography>
                    {files.map(file => {
                      const isSelected = selectedGeneratedFile?.mapping === mapping && selectedGeneratedFile?.type === file.type;
                      const typeLabels = { pyspark: 'PySpark', dlt: 'DLT', sql: 'SQL' };
                      return (
                        <Box
                          key={`${mapping}-${file.type}`}
                          onClick={() => handleFileSelect(mapping, file.type)}
                          sx={{
                            padding: '10px 12px',
                            marginBottom: '6px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            backgroundColor: isSelected ? '#E3F2FD' : '#F5F5F5',
                            border: isSelected ? '2px solid #4A90E2' : '1px solid #E0E0E0',
                            '&:hover': {
                              backgroundColor: isSelected ? '#BBDEFB' : '#EEEEEE',
                            },
                            transition: 'all 0.2s',
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <CodeIcon sx={{ fontSize: '18px', color: isSelected ? '#4A90E2' : '#757575' }} />
                            <Typography sx={{ 
                              fontSize: '14px', 
                              fontWeight: isSelected ? 600 : 400,
                              color: isSelected ? '#4A90E2' : '#212121'
                            }}>
                              {typeLabels[file.type] || file.type}
                            </Typography>
                          </Box>
                        </Box>
                      );
                    })}
                  </Box>
                ))}
              </Box>

              {/* Code Viewer Area */}
              <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                {selectedGeneratedFile ? (
                  <>
                    {/* Tabs */}
                    <Paper sx={{ marginBottom: '20px' }}>
                      <Tabs
                        value={activeCodeTab}
                        onChange={handleTabChange}
                        sx={{
                          borderBottom: '1px solid #E0E0E0',
                          '& .MuiTab-root': {
                            textTransform: 'none',
                            fontSize: '14px',
                            fontWeight: 600,
                            minHeight: '48px',
                          },
                          '& .Mui-selected': {
                            color: '#4A90E2',
                          },
                        }}
                        indicatorColor="primary"
                        textColor="primary"
                      >
                        <Tab
                          label="PySpark"
                          value="pyspark"
                          sx={{
                            color: activeCodeTab === 'pyspark' ? '#4A90E2' : '#757575',
                          }}
                        />
                        <Tab
                          label="DLT"
                          value="dlt"
                          sx={{
                            color: activeCodeTab === 'dlt' ? '#9B59B6' : '#757575',
                          }}
                        />
                        <Tab
                          label="SQL"
                          value="sql"
                          sx={{
                            color: activeCodeTab === 'sql' ? '#50C878' : '#757575',
                          }}
                        />
                      </Tabs>
                    </Paper>

                    {/* Code Viewer */}
                    {generatedCode ? (
                      <>
                        <CodeViewer
                          code={generatedCode}
                          language={activeCodeTab === 'pyspark' ? 'python' : activeCodeTab === 'sql' ? 'sql' : 'python'}
                          filename={`${selectedGeneratedFile.mapping}.${activeCodeTab === 'pyspark' ? 'py' : activeCodeTab === 'sql' ? 'sql' : 'py'}`}
                        />
                        {/* Action Button */}
                        <Box sx={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
                          <Button
                            variant="contained"
                            endIcon={<ArrowForwardIcon />}
                            onClick={() => setCurrentStep(7)}
                            sx={{
                              backgroundColor: '#FFA500',
                              '&:hover': { backgroundColor: '#CC7700' },
                              padding: '12px 24px',
                              fontSize: '16px',
                              fontWeight: 600,
                            }}
                          >
                            Enhance/Fix with AI
                          </Button>
                        </Box>
                      </>
                    ) : (
                      <Card
                        sx={{
                          padding: '40px',
                          textAlign: 'center',
                          background: '#F5F5F5',
                          border: '1px dashed #BDBDBD',
                        }}
                      >
                        <Typography variant="body1" sx={{ color: '#757575' }}>
                          Click on a tab above to generate {activeCodeTab.toUpperCase()} code for {selectedGeneratedFile.mapping}
                        </Typography>
                      </Card>
                    )}
                  </>
                ) : (
                  <Card
                    sx={{
                      padding: '40px',
                      textAlign: 'center',
                      background: '#F5F5F5',
                      border: '1px dashed #BDBDBD',
                      borderRadius: '8px',
                    }}
                  >
                    <Typography variant="body1" sx={{ color: '#757575' }}>
                      Select a file from the list to view its code
                    </Typography>
                  </Card>
                )}
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    );
  };

  // Step 7: AI Enhancement - Enhanced with better UI
  const renderAIEnhancement = () => {
    const getSeverityIcon = (severity) => {
      switch (severity?.toUpperCase()) {
        case 'HIGH':
          return <ErrorIcon sx={{ color: '#C62828' }} />;
        case 'MEDIUM':
          return <WarningIcon sx={{ color: '#F57C00' }} />;
        case 'LOW':
          return <InfoIcon sx={{ color: '#7B1FA2' }} />;
        default:
          return <InfoIcon sx={{ color: '#757575' }} />;
      }
    };

    const getSeverityColor = (severity) => {
      switch (severity?.toUpperCase()) {
        case 'HIGH':
          return '#C62828';
        case 'MEDIUM':
          return '#F57C00';
        case 'LOW':
          return '#7B1FA2';
        default:
          return '#757575';
      }
    };

    const getSeverityBgColor = (severity) => {
      switch (severity?.toUpperCase()) {
        case 'HIGH':
          return '#FFEBEE';
        case 'MEDIUM':
          return '#FFF3E0';
        case 'LOW':
          return '#F3E5F5';
        default:
          return '#F5F5F5';
      }
    };

    return (
      <Box sx={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <Box sx={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" sx={{ fontSize: '20px', fontWeight: 600, color: '#212121' }}>
            AI Enhancement & Code Review
          </Typography>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => setCurrentStep(6)}
            sx={{
              borderColor: '#757575',
              color: '#757575',
              '&:hover': {
                borderColor: '#424242',
                backgroundColor: 'rgba(117, 117, 117, 0.04)',
              },
            }}
          >
            Back
          </Button>
        </Box>

        {/* Main Content Card */}
        <Card
          sx={{
            padding: '30px',
            background: '#E3F2FD',
            border: '2px solid #4A90E2',
            borderRadius: '8px',
          }}
        >
          <Typography variant="h5" sx={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#212121' }}>
            AI Code Review & Enhancement
          </Typography>
          <Typography variant="body2" sx={{ color: '#757575', marginBottom: '24px', fontSize: '14px' }}>
            The AI agents will review the generated code and suggest improvements, 
            fix issues, and optimize for Databricks best practices.
          </Typography>

          {!codeReviewResults && (
            <Box sx={{ marginTop: '20px' }}>
              <Button
                variant="contained"
                onClick={async () => {
                  if (!generatedCode) {
                    alert('Please generate code first before reviewing.');
                    return;
                  }
                  setLoading(true);
                  try {
                    const result = await apiClient.reviewCode(generatedCode);
                    if (result.success) {
                      setError(null);
                      const reviewResults = result.review || result.result || {};
                      setCodeReviewResults(reviewResults);
                    }
                  } catch (err) {
                    setError(err.message);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={!generatedCode || loading}
                sx={{
                  backgroundColor: (!generatedCode || loading) ? '#BDBDBD' : '#4A90E2',
                  '&:hover': {
                    backgroundColor: (!generatedCode || loading) ? '#BDBDBD' : '#2E5C8A',
                  },
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: 600,
                }}
              >
                {loading ? '⏳ Reviewing...' : '🔍 Review Code with AI'}
              </Button>
            </Box>
          )}

          {codeReviewResults && (
            <Paper
              sx={{
                marginTop: '20px',
                padding: '20px',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #E0E0E0',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <Typography variant="h6" sx={{ fontSize: '16px', fontWeight: 600, color: '#212121' }}>
                  Review Results
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setCodeReviewResults(null)}
                  sx={{
                    borderColor: '#757575',
                    color: '#757575',
                    fontSize: '12px',
                  }}
                >
                  Clear
                </Button>
              </Box>

              {codeReviewResults.issues && codeReviewResults.issues.length > 0 ? (
                <Box>
                  <Alert severity="error" sx={{ marginBottom: '20px' }}>
                    <AlertTitle sx={{ fontWeight: 600 }}>
                      Found {codeReviewResults.issues.length} issue(s)
                    </AlertTitle>
                  </Alert>
                  <Box sx={{ maxHeight: '500px', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {codeReviewResults.issues.map((issue, idx) => (
                      <Alert
                        key={idx}
                        severity={issue.severity === 'HIGH' ? 'error' : issue.severity === 'MEDIUM' ? 'warning' : 'info'}
                        icon={getSeverityIcon(issue.severity)}
                        sx={{
                          backgroundColor: getSeverityBgColor(issue.severity),
                          borderLeft: `4px solid ${getSeverityColor(issue.severity)}`,
                          '& .MuiAlert-icon': {
                            color: getSeverityColor(issue.severity),
                          },
                        }}
                      >
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '14px' }}>
                              {issue.category || issue.type || 'Issue'}
                            </Typography>
                            <Chip
                              label={issue.severity || 'UNKNOWN'}
                              size="small"
                              sx={{
                                backgroundColor: getSeverityColor(issue.severity),
                                color: 'white',
                                fontSize: '11px',
                                fontWeight: 600,
                                height: '20px',
                              }}
                            />
                          </Box>
                          <Typography variant="body2" sx={{ marginBottom: '8px', color: '#424242', fontSize: '14px' }}>
                            {issue.issue || issue.message || issue.description || 'No description available'}
                          </Typography>
                          {(issue.location || issue.line) && (
                            <Typography variant="caption" sx={{ color: '#757575', fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                              📍 Location: {issue.location || issue.line}
                            </Typography>
                          )}
                          {(issue.recommendation || issue.suggestion) && (
                            <Box
                              sx={{
                                marginTop: '8px',
                                padding: '12px',
                                background: '#E8F5E9',
                                borderRadius: '6px',
                                border: '1px solid #4CAF50',
                              }}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <LightbulbIcon sx={{ fontSize: '18px', color: '#4CAF50' }} />
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '13px', color: '#2E7D32' }}>
                                  Recommendation:
                                </Typography>
                              </Box>
                              <Typography variant="body2" sx={{ color: '#424242', fontSize: '13px' }}>
                                {issue.recommendation || issue.suggestion}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </Alert>
                    ))}
                  </Box>
                </Box>
              ) : (
                <Alert severity="success" sx={{ textAlign: 'center' }}>
                  <CheckCircleIcon sx={{ fontSize: '48px', marginBottom: '10px' }} />
                  <AlertTitle sx={{ fontWeight: 600, fontSize: '16px' }}>
                    No issues found! Code looks good.
                  </AlertTitle>
                </Alert>
              )}
            </Paper>
          )}
        </Card>
      </Box>
    );
  };

  // Step descriptions
  const stepDescriptions = {
    1: { title: 'Upload Files', desc: 'Upload Informatica XML files from a folder to begin the modernization journey' },
    2: { title: 'Repository View', desc: 'Visualize and manage your uploaded Informatica files' },
    3: { title: 'Parse & Enhance', desc: 'Parse files and enhance with AI to create the canonical model' },
    4: { title: 'Canonical Model', desc: 'Visualize the technology-neutral canonical model representation' },
    5: { title: 'Lineage', desc: 'View data lineage and workflow dependencies' },
    6: { title: 'Generated Code', desc: 'View and navigate generated PySpark, DLT, or SQL code files' },
    7: { title: 'AI Enhance', desc: 'Review and enhance generated code with AI agents' }
  };

  // Progress indicator - Enhanced to match design
  const renderProgress = () => {
    const currentStepInfo = stepDescriptions[currentStep];

    return (
      <Box
        sx={{
          background: '#FFFFFF',
          borderBottom: '2px solid #E0E0E0',
          padding: '16px 24px',
        }}
      >
        {/* Step Title and Progress Bar */}
        <Box sx={{ marginBottom: '12px' }}>
          <Typography
            variant="h2"
            sx={{
              fontSize: '20px',
              fontWeight: 600,
              color: '#212121',
              marginBottom: '8px',
            }}
          >
            Step {currentStep} of 6: {currentStepInfo.title}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontSize: '13px',
              color: '#757575',
              marginBottom: '12px',
            }}
          >
            {currentStepInfo.desc}
          </Typography>
          
          {/* Progress Bar */}
          <Box
            sx={{
              width: '100%',
              height: '8px',
              backgroundColor: '#E0E0E0',
              borderRadius: '4px',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <Box
              sx={{
                width: `${(currentStep / 6) * 100}%`,
                height: '100%',
                backgroundColor: '#4A90E2',
                transition: 'width 0.3s ease',
              }}
            />
            <Typography
              variant="caption"
              sx={{
                position: 'absolute',
                top: '12px',
                left: 0,
                fontSize: '11px',
                color: '#4A90E2',
                fontWeight: 500,
              }}
            >
              {currentStep}/6
            </Typography>
          </Box>
        </Box>
      </Box>
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        {/* Sidebar Navigation */}
        <SidebarNavigation 
          currentStep={currentStep} 
          onStepChange={setCurrentStep}
        />

        {/* Main Content Area */}
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            marginLeft: '240px', // Sidebar width
            height: '100vh',
            overflow: 'hidden',
            backgroundColor: '#FAFAFA',
          }}
        >
          {/* Top Header */}
          <TopHeader 
            onUploadClick={() => setCurrentStep(1)}
            notificationCount={0}
          />

          {/* Progress Indicator */}
          <Box sx={{ marginTop: '64px' }}> {/* Account for header height */}
            {renderProgress()}
          </Box>

          {/* Main Content */}
          <Box
            sx={{
              flex: 1,
              overflow: 'auto',
              padding: '20px',
            }}
          >
            {error && (
              <Box
                sx={{
                  padding: '15px',
                  background: '#ffebee',
                  color: '#c62828',
                  marginBottom: '20px',
                  borderRadius: '6px',
                  border: '1px solid #ef5350',
                }}
              >
                {error}
              </Box>
            )}

            {loading && (
              <Box
                sx={{
                  padding: '20px',
                  textAlign: 'center',
                  color: '#666',
                }}
              >
                Loading...
              </Box>
            )}

            {!loading && (
              <>
                {currentStep === 1 && renderUploadStep()}
                {currentStep === 2 && renderRepositoryView()}
                {currentStep === 3 && renderParseSuccess()}
                {currentStep === 4 && renderCanonicalModelView()}
                {currentStep === 5 && (
                  <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    {/* Header */}
                    <Box sx={{ 
                      padding: '12px 20px', 
                      background: 'white', 
                      borderBottom: '1px solid #e0e0e0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <Typography variant="h4" sx={{ fontSize: '20px', fontWeight: 600, color: '#212121' }}>
                        Lineage View
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<ArrowBackIcon />}
                        onClick={() => setCurrentStep(4)}
                        sx={{
                          borderColor: '#757575',
                          color: '#757575',
                          '&:hover': {
                            borderColor: '#424242',
                            backgroundColor: 'rgba(117, 117, 117, 0.04)',
                          },
                        }}
                      >
                        Back to Canonical Model
                      </Button>
                    </Box>
                    {/* Lineage Content */}
                    <Box sx={{ flex: 1, overflow: 'auto' }}>
                      <LineagePage />
                    </Box>
                  </Box>
                )}
                {currentStep === 6 && renderCodeGeneration()}
                {currentStep === 7 && renderAIEnhancement()}
              </>
            )}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

