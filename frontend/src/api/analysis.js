import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const hrApiKey = import.meta.env.VITE_HR_API_KEY
if (hrApiKey) {
  api.defaults.headers.common['X-API-Key'] = hrApiKey
}

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

// ============== 候选人评估报告接口 ==============
export const reportApi = {
  listCandidates(params) {
    return api.get('/report/candidates', { params })
  },

  getCandidateContext(candidateId) {
    return api.get(`/report/candidates/${candidateId}/context`)
  },

  generate(data) {
    return api.post('/reports/generate', data)
  },

  list(params) {
    return api.get('/reports', { params })
  },

  getById(reportId) {
    return api.get(`/reports/${reportId}`)
  },

  regenerate(reportId) {
    return api.post(`/reports/${reportId}/regenerate`)
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
  },

  getJobTypes() {
    return api.get('/job-types')
  },

  parseJD(data) {
    return api.post('/jobs/parse-jd', data)
  }
}

// ============== 岗位库接口 ==============
export const jobPositionsApi = {
  list(params) {
    return api.get('/job-positions', { params })
  },

  getById(id) {
    return api.get(`/job-positions/${id}`)
  },

  create(data) {
    return api.post('/job-positions', data)
  },

  update(id, data) {
    return api.put(`/job-positions/${id}`, data)
  },

  archive(id) {
    return api.patch(`/job-positions/${id}/archive`)
  },

  copy(id) {
    return api.post(`/job-positions/${id}/copy`)
  },

  parseJD(data) {
    return api.post('/job-positions/parse-jd', data)
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
  },

  parseResume(data) {
    return api.post('/candidates/parse-resume', data)
  }
}

// ============== 简历筛选接口 ==============
export const screeningApi = {
  trigger(candidateId, data = { force: false, request_id: null }) {
    return api.post(`/candidates/${candidateId}/resume-screening`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/resume-screening/latest`)
  },

  parseJd(data) {
    return api.post('/screening/jd/parse', data)
  },

  parseJdFile(formData) {
    return api.post('/screening/jd/parse-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  createTask(data) {
    return api.post('/screening/tasks', data)
  },

  listTasks(params) {
    return api.get('/screening/tasks', { params })
  },

  uploadResumes(taskId, formData) {
    return api.post(`/screening/tasks/${taskId}/resumes`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  startTask(taskId) {
    return api.post(`/screening/tasks/${taskId}/start`)
  },

  processNextResume(taskId, params = {}) {
    return api.post(`/screening/tasks/${taskId}/process-next`, null, {
      params,
      timeout: 300000
    })
  },

  reprocessResume(taskId, resumeFileId, params = {}) {
    return api.post(`/screening/tasks/${taskId}/resume-files/${resumeFileId}/reprocess`, null, {
      params,
      timeout: 300000
    })
  },

  getTaskProgress(taskId) {
    return api.get(`/screening/tasks/${taskId}/progress`)
  },

  getTaskResults(taskId, params) {
    return api.get(`/screening/tasks/${taskId}/results`, { params })
  },

  getResultDetail(resultId) {
    return api.get(`/screening/results/${resultId}`)
  },

  updateResultStatus(resultId, data) {
    return api.put(`/screening/results/${resultId}/status`, data)
  }
}

// ============== 简历解析记录接口 ==============
export const resumeFilesApi = {
  list(params) {
    return api.get('/resume-files', { params })
  },

  getById(id) {
    return api.get(`/resume-files/${id}`)
  },

  reparse(id, params = { force_screen: true }) {
    return api.post(`/resume-files/${id}/reparse`, null, {
      params,
      timeout: 300000
    })
  }
}

// ============== 系统设置接口 ==============
export const settingsApi = {
  listJobTypes(params) {
    return api.get('/settings/job-types', { params })
  },

  createJobType(data) {
    return api.post('/settings/job-types', data)
  },

  updateJobType(id, data) {
    return api.put(`/settings/job-types/${id}`, data)
  },

  archiveJobType(id) {
    return api.patch(`/settings/job-types/${id}/archive`)
  },

  listAiPrompts(params) {
    return api.get('/settings/ai-prompts', { params })
  },

  createAiPrompt(data) {
    return api.post('/settings/ai-prompts', data)
  },

  updateAiPrompt(id, data) {
    return api.put(`/settings/ai-prompts/${id}`, data)
  },

  copyAiPrompt(id) {
    return api.post(`/settings/ai-prompts/${id}/copy`)
  },

  activateAiPrompt(id) {
    return api.post(`/settings/ai-prompts/${id}/activate`)
  },

  archiveAiPrompt(id) {
    return api.patch(`/settings/ai-prompts/${id}/archive`)
  },

  resetAiPrompt(promptKey) {
    return api.post(`/settings/ai-prompts/${promptKey}/reset`)
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

// ============== 复试记录接口 ==============
export const secondInterviewRecordApi = {
  create(candidateId, data) {
    return api.post(`/candidates/${candidateId}/second-interview-record`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/second-interview-record/latest`)
  },

  list(candidateId, params) {
    return api.get(`/candidates/${candidateId}/second-interview-record`, { params })
  }
}

// ============== 复试分析接口 ==============
export const secondInterviewAnalysisApi = {
  trigger(candidateId, data = { interview_record_id: null, force: false, request_id: null }) {
    return api.post(`/candidates/${candidateId}/second-interview-analysis`, data)
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/second-interview-analysis/latest`)
  }
}

// ============== 开放式面试轮次接口 ==============
export const interviewRoundsApi = {
  list(candidateId) {
    return api.get(`/candidates/${candidateId}/interview-rounds`)
  },

  batchList(candidateIds) {
    return api.post('/interview-rounds/batch-query', { candidate_ids: candidateIds })
  },

  create(candidateId, data) {
    return api.post(`/candidates/${candidateId}/interview-rounds`, data)
  },

  update(candidateId, roundId, data) {
    return api.put(`/candidates/${candidateId}/interview-rounds/${roundId}`, data)
  },

  submitRecord(candidateId, roundId, data) {
    return api.post(`/candidates/${candidateId}/interview-rounds/${roundId}/record`, data)
  },

  decide(candidateId, roundId, data) {
    return api.post(`/candidates/${candidateId}/interview-rounds/${roundId}/decision`, data)
  },

  cancel(candidateId, roundId) {
    return api.post(`/candidates/${candidateId}/interview-rounds/${roundId}/cancel`)
  },

  regenerateQuestions(candidateId, roundId, params = { based_on_previous: true }) {
    return api.post(`/candidates/${candidateId}/interview-rounds/${roundId}/questions`, null, { params })
  },

  reopen(candidateId) {
    return api.post(`/candidates/${candidateId}/interview-rounds/reopen`)
  }
}

// ============== 候选人面试问题接口 ==============
export const interviewQuestionsApi = {
  list(candidateId, params) {
    return api.get(`/candidates/${candidateId}/interview-questions`, { params })
  },

  getLatest(candidateId) {
    return api.get(`/candidates/${candidateId}/interview-questions/latest`)
  },

  generate(candidateId, data = { requestId: null }) {
    return api.post(`/candidates/${candidateId}/interview-questions/generate`, data)
  },

  getById(reportId) {
    return api.get(`/interview-questions/${reportId}`)
  },

  stats(params) {
    return api.get('/interview-questions/stats', { params })
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
