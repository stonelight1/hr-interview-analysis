<template>
  <div class="analysis-new">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">生成候选人评估报告</h2>
        <p class="page-subtitle">从候选人库中选择候选人，基于岗位、简历和面试记录生成 AI 评估报告。</p>
      </div>
      <div class="header-actions">
        <el-button plain @click="goToList">查看历史报告</el-button>
      </div>
    </div>

    <div class="analysis-layout">
      <main class="main-panel">
        <section class="page-card workspace-card">
          <el-steps :active="currentStep" finish-status="success" align-center class="form-steps">
            <el-step title="选择候选人" />
            <el-step title="确认资料" />
            <el-step title="生成报告" />
          </el-steps>

          <template v-if="!selectedCandidate">
            <div class="toolbar">
              <el-input
                v-model="filters.keyword"
                class="keyword-input"
                placeholder="搜索候选人姓名、手机号、邮箱"
                clearable
                @clear="handleSearch"
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="filters.jobPositionId" placeholder="全部岗位" clearable class="filter-select" @change="handleSearch">
                <el-option v-for="job in jobOptions" :key="job.id" :label="job.job_name" :value="job.id" />
              </el-select>
              <el-select v-model="filters.status" placeholder="全部状态" clearable class="filter-select" @change="handleSearch">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-select v-model="filters.sortBy" class="sort-select" @change="handleSearch">
                <el-option label="最近面试时间" value="recentInterview" />
                <el-option label="最近上传简历" value="recentResume" />
              </el-select>
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button :loading="candidateLoading" @click="fetchCandidates">
                <el-icon v-if="!candidateLoading"><Refresh /></el-icon>
                刷新
              </el-button>
            </div>

            <el-alert
              v-if="candidateError"
              type="error"
              :closable="false"
              show-icon
              class="inline-alert"
            >
              <template #title>
                候选人列表加载失败
                <el-button text type="primary" @click="fetchCandidates">重试</el-button>
              </template>
            </el-alert>

            <div v-loading="candidateLoading" class="candidate-area">
              <el-empty v-if="!candidateError && candidates.length === 0" description="暂无候选人">
                <div class="empty-actions">
                  <el-button @click="goCandidateLibrary">去候选人库</el-button>
                  <el-button type="primary" @click="goCandidateNew">上传简历创建候选人</el-button>
                </div>
              </el-empty>

              <div v-else class="candidate-grid">
                <article v-for="candidate in candidates" :key="candidate.id" class="candidate-card">
                  <div class="candidate-card-head">
                    <div>
                      <h3>{{ candidate.candidate_name }}</h3>
                      <p>应聘岗位：{{ candidate.job_name || '未绑定岗位' }}</p>
                    </div>
                    <el-tag :type="candidate.has_report ? 'success' : 'info'" effect="light">
                      已有报告：{{ candidate.has_report ? '是' : '否' }}
                    </el-tag>
                  </div>
                  <div class="candidate-meta">
                    <span>{{ candidate.phone_masked || '手机号未记录' }}</span>
                    <span>{{ candidate.email_masked || '邮箱未记录' }}</span>
                  </div>
                  <div class="candidate-facts">
                    <div>
                      <span>最近简历</span>
                      <strong>{{ formatRelativeTime(candidate.latest_resume_time) }}</strong>
                    </div>
                    <div>
                      <span>最近面试</span>
                      <strong>{{ formatRelativeTime(candidate.latest_interview_time) }}</strong>
                    </div>
                    <div>
                      <span>当前状态</span>
                      <strong>{{ candidate.current_status_label }}</strong>
                    </div>
                  </div>
                  <div class="candidate-actions">
                    <el-button v-if="candidate.latest_report_id" plain @click="viewReport(candidate.latest_report_id)">
                      查看报告
                    </el-button>
                    <el-button v-if="candidate.latest_report_id" plain type="warning" @click="regenerateFromCard(candidate)">
                      重新生成
                    </el-button>
                    <el-button type="primary" @click="selectCandidate(candidate)">
                      选择候选人
                    </el-button>
                  </div>
                </article>
              </div>
            </div>

            <div class="pagination-wrapper" v-if="pagination.total > 0">
              <el-pagination
                v-model:current-page="pagination.page"
                v-model:page-size="pagination.pageSize"
                :page-sizes="[8, 12, 20]"
                :total="pagination.total"
                layout="total, sizes, prev, pager, next"
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
              />
            </div>
          </template>

          <template v-else>
            <div class="selected-header">
              <div>
                <p class="section-kicker">已选择候选人</p>
                <h3>{{ selectedCandidate.candidate_name }}</h3>
                <span>{{ selectedCandidate.job_name || '未绑定岗位' }} · {{ selectedCandidate.current_status_label }}</span>
              </div>
              <el-button plain @click="clearSelection">重新选择</el-button>
            </div>

            <div v-loading="contextLoading" class="context-area">
              <template v-if="context">
                <el-alert v-if="context.job_positions.length === 0" type="warning" :closable="false" show-icon class="inline-alert">
                  <template #title>该候选人尚未绑定应聘岗位，请选择一个岗位后再生成报告。</template>
                  <div class="alert-actions">
                    <el-button size="small" @click="goCandidateDetail">选择历史岗位</el-button>
                    <el-button size="small" type="primary" @click="goJobNew">新建岗位 JD</el-button>
                  </div>
                </el-alert>

                <section class="context-section" v-if="context.job_positions.length">
                  <div class="section-title">
                    <el-icon><Briefcase /></el-icon>
                    <div>
                      <h4>确认岗位</h4>
                      <p>请选择本次报告对应岗位。</p>
                    </div>
                  </div>
                  <el-radio-group v-model="selection.jobPositionId" class="option-grid" @change="handleJobChange">
                    <label v-for="job in context.job_positions" :key="job.id" class="option-card">
                      <el-radio :label="job.id">
                        <strong>{{ job.job_name }}</strong>
                        <span>{{ job.job_type || '未填写岗位类型' }}｜JD v{{ job.version || 1 }}</span>
                        <em v-if="job.screening_score != null">初筛 {{ job.screening_score }} 分｜{{ job.screening_suggestion || '暂无结论' }}</em>
                        <em v-else>历史初筛：无</em>
                      </el-radio>
                    </label>
                  </el-radio-group>
                </section>

                <el-alert v-if="context.resumes.length === 0" type="warning" :closable="false" show-icon class="inline-alert">
                  <template #title>该候选人暂无简历，请先上传简历。</template>
                  <div class="alert-actions">
                    <el-button size="small" type="primary" @click="goCandidateDetail">上传简历</el-button>
                  </div>
                </el-alert>

                <section class="context-section" v-if="context.resumes.length">
                  <div class="section-title">
                    <el-icon><Document /></el-icon>
                    <div>
                      <h4>确认简历</h4>
                      <p>系统已自动带出候选人简历，不需要重复粘贴。</p>
                    </div>
                  </div>
                  <el-radio-group v-model="selection.resumeId" class="option-grid" @change="handleResumeChange">
                    <label v-for="resume in context.resumes" :key="resume.id" class="option-card resume-card">
                      <el-radio :label="resume.id">
                        <strong>简历 v{{ resume.version || 1 }}</strong>
                        <span>{{ formatTime(resume.updated_at || resume.uploaded_at) }} 更新</span>
                        <div class="resume-summary">
                          <span>姓名：{{ resume.summary?.name || selectedCandidate.candidate_name }}</span>
                          <span>工作年限：{{ resume.summary?.work_years || '未提取' }}</span>
                          <span>学历：{{ resume.summary?.education || '未提取' }}</span>
                          <span>最近公司：{{ resume.summary?.latest_company || '未提取' }}</span>
                          <span>最近岗位：{{ resume.summary?.latest_position || '未提取' }}</span>
                        </div>
                        <p v-if="resume.summary?.core_experience">{{ resume.summary.core_experience }}</p>
                        <div v-if="normalizeSkills(resume.summary?.skills).length" class="skill-tags">
                          <el-tag v-for="skill in normalizeSkills(resume.summary.skills).slice(0, 6)" :key="skill" size="small" effect="plain">
                            {{ skill }}
                          </el-tag>
                        </div>
                      </el-radio>
                    </label>
                  </el-radio-group>
                </section>

                <el-alert v-if="context.interview_records.length === 0" type="warning" :closable="false" show-icon class="inline-alert">
                  <template #title>该候选人暂无面试记录，请先补充面试记录。</template>
                  <div class="alert-actions">
                    <el-button size="small" @click="goCandidateDetailInterview">粘贴面试记录</el-button>
                    <el-button size="small" @click="goCandidateDetailInterview">上传面试记录文件</el-button>
                    <el-button size="small" type="primary" @click="goInterviewManagement">去面试管理新增记录</el-button>
                  </div>
                </el-alert>

                <section class="context-section" v-if="context.interview_records.length">
                  <div class="section-title">
                    <el-icon><User /></el-icon>
                    <div>
                      <h4>选择面试记录</h4>
                      <p>可勾选一条或多条面试记录用于生成报告。</p>
                    </div>
                  </div>
                  <el-checkbox-group v-model="selection.interviewRecordIds" class="record-list">
                    <label v-for="record in context.interview_records" :key="record.record_key" class="record-card">
                      <el-checkbox :label="record.record_key">
                        <div class="record-main">
                          <strong>{{ record.round_name || record.round_type || '面试记录' }}</strong>
                          <span>{{ formatTime(record.interview_time) }}｜{{ record.interviewer || '未记录面试官' }}｜{{ record.record_source || '文字记录' }}</span>
                        </div>
                        <el-tag v-if="record.has_report" size="small" effect="light" type="success">已生成报告</el-tag>
                      </el-checkbox>
                    </label>
                  </el-checkbox-group>
                </section>

                <section class="context-section" v-if="context.reports.length">
                  <div class="section-title">
                    <el-icon><View /></el-icon>
                    <div>
                      <h4>历史报告</h4>
                      <p>同一资料组合会优先复用已有报告。</p>
                    </div>
                  </div>
                  <div class="history-list">
                    <div v-for="report in context.reports.slice(0, 4)" :key="report.id" class="history-row">
                      <div>
                        <strong>v{{ report.report_version }}｜{{ report.job_name || '评估报告' }}</strong>
                        <span>{{ formatTime(report.created_at) }}｜{{ report.is_current ? '当前版本' : '历史版本' }}</span>
                      </div>
                      <div class="history-actions">
                        <el-button text type="primary" @click="viewReport(report.id)">查看报告</el-button>
                        <el-button text type="warning" @click="regenerateReport(report.id)">重新生成</el-button>
                      </div>
                    </div>
                  </div>
                </section>
              </template>
            </div>
          </template>
        </section>
      </main>

      <aside class="side-panel">
        <section class="page-card assist-card">
          <h3>资料完整度</h3>
          <div class="completion-list">
            <div v-for="item in completionItems" :key="item.key" class="completion-item">
              <div>
                <span>{{ item.label }}</span>
                <em>{{ item.detail }}</em>
              </div>
              <el-tag :type="item.type" size="small" effect="light">{{ item.status }}</el-tag>
            </div>
          </div>

          <el-alert v-if="existingMatchingReport" type="success" :closable="false" show-icon class="reuse-alert">
            <template #title>已存在报告，可直接查看</template>
          </el-alert>

          <div class="side-actions">
            <el-button
              type="primary"
              size="large"
              :disabled="!canGenerate"
              :loading="generating"
              @click="handleGenerate(false)"
            >
              <el-icon v-if="!generating"><MagicStick /></el-icon>
              生成 AI 评估报告
            </el-button>
            <el-button v-if="existingMatchingReport" plain type="warning" :loading="generating" @click="handleGenerate(true)">
              重新生成报告
            </el-button>
          </div>
        </section>
      </aside>
    </div>

    <AiProcessingOverlay
      :visible="aiOverlayVisible"
      :title="aiOverlayTitle"
      :stages="aiOverlayStages"
      :progress="aiOverlayProgress"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Refresh, Document, MagicStick, User, Briefcase, View
} from '@element-plus/icons-vue'
import { jobsApi, reportApi } from '../api/analysis.js'
import AiProcessingOverlay from '../components/AiProcessingOverlay.vue'

const router = useRouter()

const candidateLoading = ref(false)
const contextLoading = ref(false)
const generating = ref(false)
const candidateError = ref(false)
const candidates = ref([])
const jobOptions = ref([])
const selectedCandidate = ref(null)
const context = ref(null)

const aiOverlayVisible = ref(false)
const aiOverlayTitle = ref('')
const aiOverlayStages = ref([])
const aiOverlayProgress = ref(0)

const filters = reactive({
  keyword: '',
  jobPositionId: '',
  status: '',
  sortBy: 'recentInterview'
})

const pagination = reactive({
  page: 1,
  pageSize: 8,
  total: 0
})

const selection = reactive({
  jobPositionId: null,
  jobPositionVersion: null,
  resumeId: null,
  resumeVersion: 1,
  interviewRecordIds: []
})

const statusOptions = [
  { label: '待面试', value: 'INTERVIEW_WAITING' },
  { label: '面试待进行', value: 'INTERVIEW_SCHEDULED' },
  { label: '已面试待决策', value: 'INTERVIEW_DECISION_PENDING' },
  { label: '待复试', value: 'ON_HOLD' },
  { label: '已淘汰', value: 'REJECTED' },
  { label: '通过并结束', value: 'FINAL_PASSED' }
]

const currentStep = computed(() => {
  if (!selectedCandidate.value) return 0
  if (canGenerate.value) return 2
  return 1
})

const selectedJob = computed(() => {
  return context.value?.job_positions?.find(item => item.id === selection.jobPositionId) || null
})

const selectedResume = computed(() => {
  return context.value?.resumes?.find(item => item.id === selection.resumeId) || null
})

const selectedRecords = computed(() => {
  const selected = new Set(selection.interviewRecordIds)
  return (context.value?.interview_records || []).filter(item => selected.has(item.record_key))
})

const canGenerate = computed(() => {
  return !!selectedCandidate.value
    && !!selection.jobPositionId
    && !!selection.resumeId
    && selection.interviewRecordIds.length > 0
})

const existingMatchingReport = computed(() => {
  if (!context.value || !canGenerate.value) return null
  const selectedRecordSet = new Set(selection.interviewRecordIds)
  const selectedRecordHashes = new Map(selectedRecords.value.map(item => [item.record_key, item.record_hash]))
  return (context.value.reports || []).find((report) => {
    const snapshot = parseJson(report.input_snapshot_json)
    const source = snapshot?.report_key_source || {}
    const reportRecords = source.interview_records || []
    if (source.candidate_id !== selectedCandidate.value?.id) return false
    if (source.job_position_id !== selection.jobPositionId) return false
    if ((source.job_position_version || 1) !== (selection.jobPositionVersion || selectedJob.value?.version || 1)) return false
    if (source.resume_id !== selection.resumeId) return false
    if ((source.resume_version || 1) !== (selection.resumeVersion || 1)) return false
    if (source.resume_text_hash && selectedResume.value?.resume_text_hash && source.resume_text_hash !== selectedResume.value.resume_text_hash) return false
    if (reportRecords.length !== selectedRecordSet.size) return false
    return reportRecords.every(item => (
      selectedRecordSet.has(item.record_key)
      && (!item.record_hash || !selectedRecordHashes.get(item.record_key) || item.record_hash === selectedRecordHashes.get(item.record_key))
    ))
  }) || null
})

const completionItems = computed(() => [
  {
    key: 'candidate',
    label: '候选人',
    detail: selectedCandidate.value?.candidate_name || '未选择',
    status: selectedCandidate.value ? '已选择' : '缺失',
    type: selectedCandidate.value ? 'success' : 'danger'
  },
  {
    key: 'job',
    label: '岗位',
    detail: selectedJob.value?.job_name || '未绑定',
    status: selectedJob.value ? '已确认' : '缺失',
    type: selectedJob.value ? 'success' : 'danger'
  },
  {
    key: 'jd',
    label: 'JD 版本',
    detail: selectedJob.value ? `v${selectedJob.value.version || 1}` : '未确认',
    status: selectedJob.value ? '已确认' : '缺失',
    type: selectedJob.value ? 'success' : 'danger'
  },
  {
    key: 'resume',
    label: '简历',
    detail: selectedResume.value ? `v${selectedResume.value.version || 1}` : '未上传',
    status: selectedResume.value ? '已选择' : '缺失',
    type: selectedResume.value ? 'success' : 'danger'
  },
  {
    key: 'records',
    label: '面试记录',
    detail: selectedRecords.value.length ? `${selectedRecords.value.length} 条记录` : '未补充',
    status: selectedRecords.value.length ? '已选择' : '缺失',
    type: selectedRecords.value.length ? 'success' : 'danger'
  },
  {
    key: 'screening',
    label: '历史初筛',
    detail: selectedJob.value?.screening_score != null ? `${selectedJob.value.screening_score} 分` : '无',
    status: selectedJob.value?.screening_score != null ? '有' : '可选',
    type: selectedJob.value?.screening_score != null ? 'success' : 'info'
  }
])

const parseJson = (value) => {
  if (!value) return null
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch (error) {
    return null
  }
}

const normalizeSkills = (skills) => {
  if (!skills) return []
  if (Array.isArray(skills)) return skills.map(item => String(item)).filter(Boolean)
  return String(skills).split(/[、,，\s]+/).filter(Boolean)
}

const formatTime = (timeStr) => {
  if (!timeStr) return '未记录'
  const date = new Date(timeStr)
  if (Number.isNaN(date.getTime())) return '未记录'
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const formatRelativeTime = (timeStr) => {
  if (!timeStr) return '暂无'
  const date = new Date(timeStr)
  if (Number.isNaN(date.getTime())) return '暂无'
  const now = new Date()
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffDays = Math.round((startToday - startDate) / 86400000)
  const hhmm = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  if (diffDays === 0) return `今天 ${hhmm}`
  if (diffDays === 1) return `昨天 ${hhmm}`
  return formatTime(timeStr)
}

const fetchJobs = async () => {
  try {
    const response = await jobsApi.list({ page: 1, page_size: 100 })
    jobOptions.value = response.data.items || []
  } catch (error) {
    jobOptions.value = []
  }
}

const buildCandidateParams = () => {
  const params = {
    page: pagination.page,
    pageSize: pagination.pageSize,
    sortBy: filters.sortBy
  }
  if (filters.keyword) params.keyword = filters.keyword
  if (filters.jobPositionId) params.jobPositionId = filters.jobPositionId
  if (filters.status) params.status = filters.status
  return params
}

const fetchCandidates = async () => {
  candidateLoading.value = true
  candidateError.value = false
  try {
    const response = await reportApi.listCandidates(buildCandidateParams())
    candidates.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    candidates.value = []
    pagination.total = 0
    candidateError.value = true
  } finally {
    candidateLoading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchCandidates()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchCandidates()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchCandidates()
}

const selectCandidate = async (candidate) => {
  selectedCandidate.value = candidate
  await fetchContext(candidate.id)
}

const clearSelection = () => {
  selectedCandidate.value = null
  context.value = null
  selection.jobPositionId = null
  selection.jobPositionVersion = null
  selection.resumeId = null
  selection.resumeVersion = 1
  selection.interviewRecordIds = []
}

const fetchContext = async (candidateId) => {
  contextLoading.value = true
  context.value = null
  try {
    const response = await reportApi.getCandidateContext(candidateId)
    context.value = response.data
    const defaults = response.data.defaults || {}
    selection.jobPositionId = defaults.jobPositionId || response.data.job_positions?.[0]?.id || null
    selection.jobPositionVersion = defaults.jobPositionVersion || response.data.job_positions?.[0]?.version || 1
    selection.resumeId = defaults.resumeId || response.data.resumes?.[0]?.id || null
    selection.resumeVersion = defaults.resumeVersion || response.data.resumes?.[0]?.version || 1
    selection.interviewRecordIds = defaults.interviewRecordIds || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取候选人资料失败')
    clearSelection()
  } finally {
    contextLoading.value = false
  }
}

const handleJobChange = () => {
  selection.jobPositionVersion = selectedJob.value?.version || 1
}

const handleResumeChange = () => {
  selection.resumeVersion = selectedResume.value?.version || 1
}

const buildGeneratePayload = (forceRegenerate = false) => ({
  candidateId: selectedCandidate.value.id,
  jobPositionId: selection.jobPositionId,
  jobPositionVersion: selection.jobPositionVersion || selectedJob.value?.version || 1,
  resumeId: selection.resumeId,
  resumeVersion: selection.resumeVersion || 1,
  interviewRecordIds: [...selection.interviewRecordIds],
  forceRegenerate
})

const handleGenerate = async (forceRegenerate = false) => {
  if (!canGenerate.value) {
    ElMessage.warning('请先选择候选人、岗位、简历和面试记录')
    return
  }
  if (forceRegenerate) {
    try {
      await ElMessageBox.confirm('重新生成会消耗 AI 次数，并生成新的报告版本，是否继续？', '确认重新生成', {
        confirmButtonText: '继续生成',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch (error) {
      return
    }
  }

  generating.value = true
  aiOverlayTitle.value = forceRegenerate ? '正在重新生成评估报告' : '正在生成 AI 评估报告'
  aiOverlayStages.value = ['读取候选人资料', '解析岗位 JD', '分析简历匹配', '评估面试记录', '生成综合报告']
  aiOverlayProgress.value = 15
  aiOverlayVisible.value = true

  setTimeout(() => { aiOverlayProgress.value = 35 }, 800)
  setTimeout(() => { aiOverlayProgress.value = 55 }, 2000)
  setTimeout(() => { aiOverlayProgress.value = 75 }, 4000)

  try {
    const response = await reportApi.generate(buildGeneratePayload(forceRegenerate))
    aiOverlayProgress.value = 100
    setTimeout(() => {
      aiOverlayVisible.value = false
      ElMessage.success(response.data.reused ? '已复用已有报告' : 'AI 评估报告已生成')
      router.push(`/analysis/${response.data.id}?source=stage-report`)
    }, 600)
  } catch (error) {
    aiOverlayVisible.value = false
    ElMessage.error(error.response?.data?.detail || 'AI 评估报告生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

const regenerateReport = async (reportId) => {
  try {
    await ElMessageBox.confirm('重新生成会消耗 AI 次数，并生成新的报告版本，是否继续？', '确认重新生成', {
      confirmButtonText: '继续生成',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (error) {
    return
  }

  generating.value = true
  aiOverlayTitle.value = '正在重新生成评估报告'
  aiOverlayStages.value = ['读取候选人资料', '解析岗位 JD', '分析简历匹配', '评估面试记录', '生成综合报告']
  aiOverlayProgress.value = 15
  aiOverlayVisible.value = true

  setTimeout(() => { aiOverlayProgress.value = 35 }, 800)
  setTimeout(() => { aiOverlayProgress.value = 55 }, 2000)
  setTimeout(() => { aiOverlayProgress.value = 75 }, 4000)

  try {
    const response = await reportApi.regenerate(reportId)
    aiOverlayProgress.value = 100
    setTimeout(() => {
      aiOverlayVisible.value = false
      ElMessage.success('已生成新的报告版本')
      router.push(`/analysis/${response.data.id}?source=stage-report`)
    }, 600)
  } catch (error) {
    aiOverlayVisible.value = false
    ElMessage.error(error.response?.data?.detail || '重新生成失败')
  } finally {
    generating.value = false
  }
}

const regenerateFromCard = (candidate) => {
  if (!candidate.latest_report_id) return
  regenerateReport(candidate.latest_report_id)
}

const viewReport = (reportId) => {
  router.push(`/analysis/${reportId}?source=stage-report`)
}

const goToList = () => router.push('/analysis/list')
const goCandidateLibrary = () => router.push('/candidates')
const goCandidateNew = () => router.push('/candidates/new')
const goJobNew = () => router.push('/jobs/new')
const goInterviewManagement = () => router.push('/interviews')
const goCandidateDetail = () => {
  if (!selectedCandidate.value) return
  router.push(`/candidates/${selectedCandidate.value.id}`)
}
const goCandidateDetailInterview = () => {
  if (!selectedCandidate.value) return
  router.push(`/candidates/${selectedCandidate.value.id}?tab=interview&from=reports`)
}

onMounted(() => {
  fetchJobs()
  fetchCandidates()
})
</script>

<style scoped>
.analysis-new {
  max-width: 1360px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  gap: 16px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.page-title {
  font-size: 24px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0;
  letter-spacing: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.analysis-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.workspace-card {
  padding: 22px;
}

.form-steps {
  padding: 4px 0 22px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--color-border);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.keyword-input {
  width: 280px;
}

.filter-select {
  width: 170px;
}

.sort-select {
  width: 150px;
}

.inline-alert {
  margin-bottom: 16px;
}

.candidate-area {
  min-height: 360px;
}

.candidate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.candidate-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.candidate-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.candidate-card h3 {
  font-size: 17px;
  color: var(--color-text);
  margin: 0 0 4px;
}

.candidate-card p {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.candidate-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 12px;
  background: var(--color-surface-soft);
  border-radius: var(--radius-sm);
}

.candidate-facts div,
.completion-item div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.candidate-facts span,
.completion-item em {
  font-size: 12px;
  color: var(--color-text-muted);
  font-style: normal;
}

.candidate-facts strong {
  color: var(--color-text);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-actions,
.alert-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}

.selected-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-soft);
  margin-bottom: 18px;
}

.section-kicker {
  margin: 0 0 4px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: var(--font-bold);
}

.selected-header h3 {
  margin: 0 0 4px;
  color: var(--color-text);
  font-size: 20px;
}

.selected-header span {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.context-area {
  min-height: 360px;
}

.context-section {
  padding: 18px 0;
  border-top: 1px solid var(--color-border);
}

.section-title {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  color: var(--color-primary);
}

.section-title h4 {
  margin: 0 0 3px;
  color: var(--color-text);
  font-size: 16px;
}

.section-title p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  align-items: stretch;
}

.option-card,
.record-card {
  display: block;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 14px;
  background: var(--color-surface);
  cursor: pointer;
}

.option-card :deep(.el-radio),
.record-card :deep(.el-checkbox) {
  width: 100%;
  height: auto;
  align-items: flex-start;
  margin-right: 0;
}

.option-card :deep(.el-radio__label),
.record-card :deep(.el-checkbox__label) {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  width: 100%;
  white-space: normal;
}

.option-card strong,
.record-card strong {
  color: var(--color-text);
  font-size: 14px;
}

.option-card span,
.option-card em,
.record-card span {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-style: normal;
}

.resume-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 5px 10px;
  margin-top: 4px;
}

.resume-card p {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
  margin: 4px 0 0;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.record-list {
  display: grid;
  gap: 10px;
}

.record-card :deep(.el-checkbox__label) {
  flex-direction: row;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.record-main {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.history-list {
  display: grid;
  gap: 8px;
}

.history-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
}

.history-row div:first-child {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-row strong {
  color: var(--color-text);
  font-size: 14px;
}

.history-row span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.history-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.side-panel {
  position: sticky;
  top: 24px;
}

.assist-card {
  padding: 18px;
}

.assist-card h3 {
  font-size: 16px;
  color: var(--color-text);
  margin: 0 0 14px;
}

.completion-list {
  display: flex;
  flex-direction: column;
}

.completion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.completion-item:last-child {
  border-bottom: 0;
}

.completion-item span {
  font-size: 13px;
  color: var(--color-text);
  font-weight: var(--font-bold);
}

.reuse-alert {
  margin-top: 14px;
}

.side-actions {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.side-actions .el-button {
  width: 100%;
  margin-left: 0;
}

:deep(.el-step__title) {
  font-size: 13px;
  font-weight: var(--font-bold);
}

@media (max-width: 1100px) {
  .analysis-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-header,
  .selected-header,
  .history-row {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar > * {
    width: 100% !important;
  }

  .candidate-facts,
  .resume-summary {
    grid-template-columns: 1fr;
  }

  .workspace-card {
    padding: 18px;
  }
}
</style>
