import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, TextField, List, ListItem, ListItemButton, ListItemText, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TableSortLabel, InputAdornment, Collapse, IconButton, ListItemSecondaryAction } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';
import SearchIcon from '@mui/icons-material/Search';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import FolderIcon from '@mui/icons-material/Folder';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [logContent, setLogContent] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [filter, setFilter] = useState('');
  const [orderBy, setOrderBy] = useState('time');
  const [order, setOrder] = useState('asc');
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [watchedFiles, setWatchedFiles] = useState([]);
  const [newFile, setNewFile] = useState('');

  useEffect(() => {
    fetchWatchedFiles();
  }, []);

  const fetchWatchedFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/files');
      setWatchedFiles(response.data.files);
    } catch (error) {
      console.error('Error fetching watched files:', error);
    }
  };

  const handleAddFile = async () => {
    if (!newFile.trim()) return;
    
    try {
      await axios.post('http://localhost:5000/api/files', { 
        file: newFile.trim() 
      });
      setNewFile('');
      await fetchWatchedFiles();
    } catch (error) {
      console.error('Error adding file:', error);
    }
  };

  const handleRemoveFile = async (filePath) => {
    try {
      await axios.get(`http://localhost:5000/api/files/delete/${encodeURIComponent(filePath)}`);
      await fetchWatchedFiles();
    } catch (error) {
      console.error('Error removing file:', error);
    }
  };


  const handleFileSelect = async (file) => {
    setSelectedFile(file);
    await refreshFileContent(file);
  };

  const refreshFileContent = async (file) => {
    try {
      const encodedPath = file.startsWith('/') 
        ? '/' + file.slice(1).split('/').map(segment => encodeURIComponent(segment)).join('/')
        : file.split('/').map(segment => encodeURIComponent(segment)).join('/');
      
      const response = await axios.get(`http://localhost:5000/api/logs${encodedPath}`);
      setLogContent(response.data.lines);
      
      console.log('Fetching analytics...');
      const analyticsResponse = await axios.get(`http://localhost:5000/api/analytics${encodedPath}`);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching file content:', error);
      if (error.response) {
        console.error('Backend error response:', error.response.data);
      }
    }
  };

  const handleRefresh = async () => {
    if (selectedFile) {
      await refreshFileContent(selectedFile);
    }
  };

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const getSortedAndFilteredLogs = () => {
    if (!logContent || !Array.isArray(logContent)) {
      console.warn('logContent is not an array or is undefined');
      return [];
    }

    const filtered = logContent.filter(line => {
      console.debug('Processing line:', line);
      if (!Array.isArray(line) || line.length < 3) {
        console.warn('Line is not a valid array:', line);
        return false;
      }
      const [time, level, message] = line;
      const matches = (
        time.toLowerCase().includes(filter.toLowerCase()) ||
        level.toLowerCase().includes(filter.toLowerCase()) ||
        message.toLowerCase().includes(filter.toLowerCase())
      );
      return matches;
    });

    console.debug('Filtered results:', filtered);
    return filtered.sort((a, b) => {
      const aValue = a[orderBy === 'time' ? 0 : orderBy === 'level' ? 1 : 2];
      const bValue = b[orderBy === 'time' ? 0 : orderBy === 'level' ? 1 : 2];
      
      if (order === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  };

  return (
    <Box sx={{ flexGrow: 1, p: 2 }}>
      <Grid container spacing={2}>
        {/* Left Panel - Log Files List */}
        <Grid item xs={leftPanelOpen ? 2 : 0.5}>
          <Paper sx={{ p: 2, height: '100vh', position: 'relative' }}>
            <IconButton 
              onClick={() => setLeftPanelOpen(!leftPanelOpen)}
              sx={{ position: 'absolute', right: 0, top: 0 }}
            >
              {leftPanelOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
            <Collapse in={leftPanelOpen} orientation="horizontal">
              <Box>
                <Typography variant="h6" gutterBottom>
                  <FolderIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Log Files
                </Typography>
                <Box sx={{ display: 'flex', mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Add File to Watch"
                    variant="outlined"
                    value={newFile}
                    onChange={(e) => setNewFile(e.target.value)}
                    size="small"
                  />
                  <IconButton 
                    color="primary" 
                    onClick={handleAddFile}
                    sx={{ ml: 1 }}
                  >
                    <AddIcon />
                  </IconButton>
                </Box>
                <List>
                  {watchedFiles.map((filePath, index) => (
                    <ListItem 
                      key={index}
                      sx={{
                        backgroundColor: selectedFile === filePath ? 'action.selected' : 'inherit'
                      }}
                    >
                      <ListItemText 
                        primary={filePath.split('/').pop()} 
                        secondary={filePath}
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          onClick={() => handleRemoveFile(filePath)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                  Available Log Files
                </Typography>
                <List>
                  {watchedFiles.map((file, index) => (
                    <ListItemButton 
                      key={index}
                      sx={{
                        backgroundColor: selectedFile === file ? 'action.selected' : 'inherit'
                      }}
                      onClick={() => handleFileSelect(file)}
                    >
                      <ListItemText 
                                    primary={file.split('/').pop()}
                                    secondary={file}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Box>
            </Collapse>
          </Paper>
        </Grid>

        {/* Main Panel - Log Content */}
        <Grid item xs={12 - (leftPanelOpen ? 2 : 0.5) - (rightPanelOpen ? 3 : 0.5)}>
          <Paper sx={{ p: 2, height: '100vh', overflow: 'auto' }}>
            <Box sx={{ display: 'flex', mb: 2 }}>
              <TextField
                fullWidth
                label="Filter Logs"
                variant="outlined"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
              <IconButton 
                color="primary" 
                onClick={handleRefresh}
                sx={{ ml: 1 }}
                disabled={!selectedFile}
              >
                <RefreshIcon />
              </IconButton>
            </Box>
            <TableContainer sx={{ maxHeight: 'calc(100vh - 120px)' }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell width="200px">
                      <TableSortLabel
                        active={orderBy === 'time'}
                        direction={orderBy === 'time' ? order : 'asc'}
                        onClick={() => handleRequestSort('time')}
                      >
                        Time
                      </TableSortLabel>
                    </TableCell>
                    <TableCell width="100px">
                      <TableSortLabel
                        active={orderBy === 'level'}
                        direction={orderBy === 'level' ? order : 'asc'}
                        onClick={() => handleRequestSort('level')}
                      >
                        Level
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'message'}
                        direction={orderBy === 'message' ? order : 'asc'}
                        onClick={() => handleRequestSort('message')}
                      >
                        Message
                      </TableSortLabel>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {getSortedAndFilteredLogs().length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} align="center">
                        {logContent === undefined ? 'Loading...' : 'No logs found'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    getSortedAndFilteredLogs().map((line, index) => (
                      <TableRow key={index} hover>
                        <TableCell 
                          sx={{ 
                            fontFamily: 'monospace',
                            width: '200px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}
                        >
                          {line[0]}
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontFamily: 'monospace',
                            width: '100px',
                            color: line[1].includes('ERROR') ? 'error.main' : 
                                  line[1].includes('WARN') ? 'warning.main' : 
                                  line[1].includes('INFO') ? 'info.main' : 
                                  line[1].includes('DEBUG') ? 'success.main' : 'text.primary'
                          }}
                        >
                          {line[1]}
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontFamily: 'monospace',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}
                        >
                          {line[2]}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Right Panel - Analytics */}
        <Grid item xs={rightPanelOpen ? 3 : 0.5}>
          <Paper sx={{ p: 2, height: '100vh', position: 'relative' }}>
            <IconButton 
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              sx={{ position: 'absolute', left: 0, top: 0 }}
            >
              {rightPanelOpen ? <ChevronRightIcon /> : <ChevronLeftIcon />}
            </IconButton>
            <Collapse in={rightPanelOpen} orientation="horizontal">
              <Box>
                <Typography variant="h6" gutterBottom>
                  <AnalyticsIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Analytics
                </Typography>
                {analytics && (
                  <>
                    <Typography variant="subtitle1" gutterBottom>
                      Log Level Distribution
                    </Typography>
                    <BarChart
                      width={300}
                      height={200}
                      data={Object.entries(analytics.levels).map(([level, count]) => ({
                        level,
                        count
                      }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="level" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" fill="#8884d8" />
                    </BarChart>
                    {analytics.plot && (
                      <img 
                        src={`data:image/png;base64,${analytics.plot}`} 
                        alt="Log Level Distribution" 
                        style={{ width: '100%', marginTop: '1rem' }}
                      />
                    )}
                  </>
                )}
              </Box>
            </Collapse>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default App; 