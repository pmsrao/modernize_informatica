/**
 * API Client for Informatica Modernization Accelerator
 * Handles all API communication with the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail || data.message || 'API request failed',
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        error.message || 'Network error',
        0,
        null
      );
    }
  }

  // File Upload
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/v1/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        error.detail || 'File upload failed',
        response.status,
        error
      );
    }

    return await response.json();
  }

  async getFileInfo(fileId) {
    return this.request(`/api/v1/files/${fileId}`);
  }

  // Parsing Endpoints
  async parseMapping(fileId, enhanceModel = false) {
    return this.request('/api/v1/parse/mapping', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId, enhance_model: enhanceModel }),
    });
  }

  async parseWorkflow(fileId) {
    return this.request('/api/v1/parse/workflow', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  }

  async parseSession(fileId) {
    return this.request('/api/v1/parse/session', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  }

  async parseWorklet(fileId) {
    return this.request('/api/v1/parse/worklet', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  }

  // Generation Endpoints
  async generatePySpark(mappingId, canonicalModel = null, fileId = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;
    if (fileId) body.file_id = fileId;

    return this.request('/api/v1/generate/pyspark', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async generateDLT(mappingIdOrWorkflowId, canonicalModel = null, fileId = null) {
    const body = {};
    // Try to determine if it's a mapping_id or workflow_id
    // For now, support both - if it starts with M_ assume mapping, else workflow
    if (mappingIdOrWorkflowId) {
      if (mappingIdOrWorkflowId.startsWith('M_')) {
        body.mapping_id = mappingIdOrWorkflowId;
      } else {
        body.workflow_id = mappingIdOrWorkflowId;
      }
    }
    if (canonicalModel) body.canonical_model = canonicalModel;
    if (fileId) body.file_id = fileId;

    return this.request('/api/v1/generate/dlt', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async generateSQL(mappingId, canonicalModel = null, fileId = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;
    if (fileId) body.file_id = fileId;

    return this.request('/api/v1/generate/sql', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async generateSpec(mappingId, canonicalModel = null, fileId = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;
    if (fileId) body.file_id = fileId;

    return this.request('/api/v1/generate/spec', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // AI Analysis Endpoints
  async analyzeSummary(mappingId, canonicalModel = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;

    return this.request('/api/v1/analyze/summary', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async analyzeRisks(mappingId, canonicalModel = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;

    return this.request('/api/v1/analyze/risks', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async analyzeSuggestions(mappingId, canonicalModel = null) {
    const body = {};
    if (mappingId) body.mapping_id = mappingId;
    if (canonicalModel) body.canonical_model = canonicalModel;

    return this.request('/api/v1/analyze/suggestions', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async explainExpression(expression, context = null) {
    return this.request('/api/v1/analyze/explain', {
      method: 'POST',
      body: JSON.stringify({
        expression,
        context,
      }),
    });
  }

  async reviewCode(code, canonicalModel = null) {
    const body = {
      code: code
    };
    if (canonicalModel) body.canonical_model = canonicalModel;

    return this.request('/api/v1/review/code', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // DAG Endpoints
  async buildDAG(workflowId, workflowData = null, fileId = null) {
    const body = {};
    if (workflowId) body.workflow_id = workflowId;
    if (workflowData) body.workflow_data = workflowData;
    if (fileId) body.file_id = fileId;

    return this.request('/api/v1/dag/build', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async getDAG(dagId) {
    return this.request(`/api/v1/dag/${dagId}`);
  }

  async visualizeDAG(workflowId, workflowData = null, fileId = null, format = 'json', includeMetadata = false) {
    const body = {};
    if (workflowId) body.workflow_id = workflowId;
    if (workflowData) body.workflow_data = workflowData;
    if (fileId) body.file_id = fileId;

    const response = await fetch(`${this.baseURL}/api/v1/dag/visualize?format=${format}&include_metadata=${includeMetadata}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        error.detail || 'DAG visualization failed',
        response.status,
        error
      );
    }

    if (format === 'json') {
      return await response.json();
    }
    return await response.text();
  }

  // Health Check
  async healthCheck() {
    return this.request('/health');
  }

  // Graph Query Endpoints
  async listMappings() {
    return this.request('/api/v1/graph/mappings');
  }

  async getMappingStructure(mappingName) {
    return this.request(`/api/v1/graph/mappings/${mappingName}/structure`);
  }

  async getMappingDependencies(mappingName) {
    return this.request(`/api/v1/graph/mappings/${mappingName}/dependencies`);
  }

  async getMappingImpact(mappingName) {
    return this.request(`/api/v1/graph/mappings/${mappingName}/impact`);
  }

  async getGraphStatistics() {
    return this.request('/api/v1/graph/statistics');
  }

  async getCanonicalOverview() {
    try {
      return await this.request('/api/v1/graph/canonical/overview');
    } catch (error) {
      console.error('Error getting canonical overview:', error);
      return { success: false, overview: null, message: error.message };
    }
  }

  async getSourceOverview() {
    try {
      return await this.request('/api/v1/graph/source/overview');
    } catch (error) {
      console.error('Error getting source overview:', error);
      return { success: false, overview: null, message: error.message };
    }
  }

  async getCodeOverview() {
    try {
      return await this.request('/api/v1/graph/code/overview');
    } catch (error) {
      console.error('Error getting code overview:', error);
      return { success: false, overview: null, message: error.message };
    }
  }

  // Pipeline Endpoints (generic platform-agnostic terminology)
  async listPipelines() {
    try {
      return await this.request('/api/v1/graph/pipelines');
    } catch (error) {
      console.error('Error listing pipelines:', error);
      return { success: false, pipelines: [], message: error.message };
    }
  }

  async getPipelineStructure(pipelineName) {
    try {
      return await this.request(`/api/v1/graph/pipelines/${encodeURIComponent(pipelineName)}`);
    } catch (error) {
      console.error('Error getting pipeline structure:', error);
      return { success: false, pipeline: null, message: error.message };
    }
  }


  // Component Endpoints
  async getAllComponents(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.type) params.append('type', filters.type);
      if (filters.complexity) params.append('complexity', filters.complexity);
      if (filters.has_code !== undefined) params.append('has_code', filters.has_code);
      if (filters.sort_by) params.append('sort_by', filters.sort_by);
      if (filters.order) params.append('order', filters.order);
      if (filters.page) params.append('page', filters.page);
      if (filters.page_size) params.append('page_size', filters.page_size);
      
      const queryString = params.toString();
      const endpoint = queryString ? `/api/v1/graph/components?${queryString}` : '/api/v1/graph/components';
      return await this.request(endpoint);
    } catch (error) {
      console.error('Error getting all components:', error);
      return { 
        success: false, 
        pipelines: [], 
        tasks: [], 
        sub_pipelines: [], 
        transformations: [], 
        reusable_transformations: [], 
        counts: {} 
      };
    }
  }

  async getFileMetadata(componentType, componentName) {
    try {
      return await this.request(`/api/v1/graph/files/${componentType}/${encodeURIComponent(componentName)}`);
    } catch (error) {
      console.error('Error getting file metadata:', error);
      return { success: false, file_metadata: null, message: error.message };
    }
  }

  // Source Repository Endpoints
  async getSourceRepository() {
    try {
      return await this.request('/api/v1/graph/source/repository');
    } catch (error) {
      console.error('Error getting source repository:', error);
      return { success: false, repository: {}, message: error.message };
    }
  }

  async getSourceFile(filePath) {
    try {
      return await this.request(`/api/v1/graph/source/file/${encodeURIComponent(filePath)}`);
    } catch (error) {
      console.error('Error getting source file:', error);
      return { success: false, content: '', message: error.message };
    }
  }

  // Code Endpoints
  async getMappingCode(mappingName) {
    try {
      return await this.request(`/api/v1/graph/code/${encodeURIComponent(mappingName)}`);
    } catch (error) {
      console.error('Error getting mapping code:', error);
      return { success: false, code_files: [], message: error.message };
    }
  }

  async getCodeFile(filePath) {
    try {
      // Encode the file path for URL
      const encodedPath = encodeURIComponent(filePath);
      return await this.request(`/api/v1/graph/code/file/${encodedPath}`);
    } catch (error) {
      console.error('Error getting code file:', error);
      return { success: false, code: null, message: error.message };
    }
  }

  async getCodeRepository() {
    try {
      return await this.request('/api/v1/graph/code/repository');
    } catch (error) {
      console.error('Error getting code repository:', error);
      return { success: false, repository: {}, message: error.message };
    }
  }

  // Assessment Endpoints
  async getAssessmentProfile() {
    try {
      return await this.request('/api/v1/assessment/profile');
    } catch (error) {
      console.error('Error fetching assessment profile:', error);
      throw error;
    }
  }

  async getAssessmentAnalysis() {
    try {
      return await this.request('/api/v1/assessment/analyze');
    } catch (error) {
      console.error('Error fetching assessment analysis:', error);
      throw error;
    }
  }

  async getMigrationWaves(maxWaveSize = 10) {
    try {
      return await this.request(`/api/v1/assessment/waves?max_wave_size=${maxWaveSize}`);
    } catch (error) {
      console.error('Error fetching migration waves:', error);
      throw error;
    }
  }

  async getAssessmentReport(format = 'json') {
    try {
      return await this.request(`/api/v1/assessment/report?format=${format}`);
    } catch (error) {
      console.error('Error fetching assessment report:', error);
      throw error;
    }
  }

  async findMappingsUsingTable(tableName, database = null) {
    const params = database ? `?database=${database}` : '';
    return this.request(`/api/v1/graph/mappings/using-table/${tableName}${params}`);
  }

  async traceLineage(sourceTable, targetTable, database = null) {
    const params = new URLSearchParams({ source_table: sourceTable, target_table: targetTable });
    if (database) params.append('database', database);
    return this.request(`/api/v1/graph/lineage/trace?${params.toString()}`);
  }

  async getMigrationOrder() {
    return this.request('/api/v1/graph/migration/order');
  }

  async getMigrationReadiness() {
    return this.request('/api/v1/graph/migration/readiness');
  }

  async findPattern(patternType, patternValue) {
    return this.request(`/api/v1/graph/patterns/${patternType}?pattern_value=${encodeURIComponent(patternValue)}`);
  }

  // Directory Upload and File Management
  async uploadDirectory(formData) {
    const response = await fetch(`${this.baseURL}/api/v1/upload/directory`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        error.detail || 'Directory upload failed',
        response.status,
        error
      );
    }

    return await response.json();
  }

  async listAllFiles(fileType = null) {
    const params = fileType ? `?file_type=${fileType}` : '';
    return this.request(`/api/v1/files${params}`);
  }

  async getHierarchy(fileIds = null) {
    const params = fileIds ? `?file_ids=${fileIds.join(',')}` : '';
    return this.request(`/api/v1/hierarchy${params}`);
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;

