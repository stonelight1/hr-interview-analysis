import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============== 旧接口兼容 ==============
export const analysisApi = {
  create(data) {
    return api.post('/analysis/create', data)
  },

  getById(id) {
    return api.get(`/analysis/${id}`)
  },

  list(params) {
    return api.get('/analysis/list', { params })
  },

  delete(id) {
    return api.delete(`/analysis/${id}`)
  }
}

// ============== 岗位接口 ==============
export const jobsApi = {
  create(data) {
    return api.post('/jobs', data)
  },

  list(params) {
    return api.get('/jobs', { params })
  },

  getById(id) {
    return api.get(`/jobs/${id}`)
  },

  update(id, data) {
    return api.put(`/jobs/${id}`, data)
  },

  updateStatus(id, data) {
    return api.put(`/jobs/${id}/status`, data)
  },

  delete(id) {
    return api.delete(`/jobs/${id}`)
  }
}

// ============== 候选人接口 ==============
export const candidatesApi = {
  create(data) {
    return api.post('/candidates', data)
  },

  list(params) {
    return api.get('/candidates', { params })
  },

  getById(id) {
    return api.get(`/candidates/${id}`)
  },

  update(id, data) {
    return api.put(`/candidates/${id}`, data)
  },

  updateStatus(id, data) {
    return api.put(`/candidates/${id}/status`, data)
  },

  delete(id) {
    return api.delete(`/candidates/${id}`)
  }
}

// ============== 简历筛选接口 ==============
export const screeningApi = {
  trigger(candidateId, data = { force: false, request_id: null }) {
    return api.post(`/candidates/${candidateId}/resume-screening`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/resume-screening/latest`)
  }
}

// ============== 初试记录接口 ==============
export const firstInterviewRecordApi = {
  create(candidateId, data) {
    return api.post(`/candidates/${candidateId}/first-interview-record`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/first-interview-record/latest`)
  },

  list(candidateId, params) {
    return api.get(`/candidates/${candidateId}/first-interview-record`, { params })
  }
}

// ============== 初试分析接口 ==============
export const firstInterviewAnalysisApi = {
  trigger(candidateId, data = { interview_record_id: null, force: false, request_id: null }) {
    return api.post(`/candidates/${candidateId}/first-interview-analysis`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/first-interview-analysis/latest`)
  }
}

// ============== 状态日志接口 ==============
export const statusLogsApi = {
  list(candidateId) {
    return api.get(`/candidates/${candidateId}/status-logs`)
  }
}

// ============== 阶段报告接口 ==============
export const stageReportApi = {
  getById(reportId) {
    return api.get(`/stage-reports/${reportId}`)
  }
}

export default api
