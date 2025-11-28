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
  async parseMapping(fileId) {
    return this.request('/api/v1/parse/mapping', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
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

  async generateDLT(workflowId, canonicalModel = null, fileId = null) {
    const body = {};
    if (workflowId) body.workflow_id = workflowId;
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

