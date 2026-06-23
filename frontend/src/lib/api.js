const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getToken() {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('colorpro_token');
    }
    return null;
  }

  setToken(token) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('colorpro_token', token);
    }
  }

  clearToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('colorpro_token');
    }
  }

  async request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
          detail: response.statusText
      }));
      throw new Error(error.detail || error.error || JSON.stringify(error));
  }
    if (response.status === 204) return null;

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/pdf')) {
      return response.blob();
    }

    return response.json();
  }

  // Auth
  async login(username, password) {
    const data = await this.request('/token/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(data.token);
    return data;
  }

  async getMe() {
    return this.request('/me/');
  }

  // Batches
  async getBatches() {
    return this.request('/batches/');
  }

  async getBatch(id) {
    return this.request(`/batches/${id}/`);
  }

  async createBatch(name, description = '') {
    return this.request('/batches/', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async deleteBatch(id) {
    return this.request(`/batches/${id}/`, { method: 'DELETE' });
  }

  async getBatchRolls(batchId) {
    return this.request(`/batches/${batchId}/rolls/`);
  }

  // Rolls
  async createRoll(batchId, rollNumber, order = 0) {
    return this.request('/rolls/', {
      method: 'POST',
      body: JSON.stringify({ batch: batchId, roll_number: rollNumber, order }),
    });
  }

  async bulkCreateRolls(batchId, rollNumbers) {
    return this.request('/rolls/bulk/', {
      method: 'POST',
      body: JSON.stringify({ batch_id: batchId, roll_numbers: rollNumbers }),
    });
  }

  // Scans
  async uploadScan(rollId, payload) {
    return this.request('/scans/upload/', {
      method: 'POST',
      body: JSON.stringify({ roll_id: rollId, ...payload }),
    });
  }

  // Comparison
  async runComparison(batchId, method = 'CIEDE2000') {
    return this.request('/compare/', {
      method: 'POST',
      body: JSON.stringify({ batch_id: batchId, method }),
    });
  }

  async getComparisonResults(batchId) {
    return this.request(`/compare/${batchId}/`);
  }

  async runQualityGate(batchId) {
    return this.request(`/compare/${batchId}/gate/`, { method: 'POST' });
  }

  async runClustering(batchId) {
    return this.request(`/compare/${batchId}/cluster/`, { method: 'POST' });
  }

  async runAdvancedClustering(batchId, params) {
    return this.request(`/compare/${batchId}/cluster/advanced/`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getShadeGroups(batchId) {
    return this.request(`/compare/${batchId}/groups/`);
  }

  // Device Status
  async getDeviceStatus() {
    return this.request('/device/status/');
  }

  async simulateScans(batchId) {
    return this.request(`/device/simulate/${batchId}/`, { method: 'POST' });
  }

  // Target Assignments
  async setClientTarget(batchId, payload) {
    return this.request(`/batches/${batchId}/client-shade/`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
  }

  async setTargetRoll(batchId, rollId) {
    return this.request(`/batches/${batchId}/target-roll/`, {
      method: 'PATCH',
      body: JSON.stringify({ roll_id: rollId })
    });
  }

  // Reports
  async generateReport(batchId) {
    return this.request(`/reports/generate/${batchId}/`, { method: 'POST' });
  }

  async getReport(reportId) {
    return this.request(`/reports/${reportId}/`);
  }

  async downloadReportPdf(reportId) {
    return this.request(`/reports/${reportId}/pdf/`);
  }

  async verifyReport(reportId, status, notes = '') {
    return this.request(`/reports/${reportId}/verify/`, {
      method: 'PATCH',
      body: JSON.stringify({ status, verification_notes: notes }),
    });
  }

  async getReportsForBatch(batchId) {
    return this.request(`/reports/?batch_id=${batchId}`);
  }
}

const api = new ApiClient();
export default api;
