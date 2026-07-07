<template>
  <div class="interview-list">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">面试管理</h2>
        <p class="page-subtitle">按面试任务推进安排、记录和决策。</p>
      </div>
      <el-button plain size="large" @click="fetchData">
        刷新
      </el-button>
    </div>

    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="候选人姓名" class="filter-item">
          <el-input v-model="filters.candidate_name" placeholder="请输入" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="应聘岗位" class="filter-item">
          <el-select v-model="filters.job_id" placeholder="请选择" clearable filterable style="width: 180px">
            <el-option v-for="job in jobs" :key="job.id" :label="job.job_name" :value="job.id" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card table-section">
      <el-tabs v-model="activeTab" class="task-tabs">
        <el-tab-pane
          v-for="tab in taskTabs"
          :key="tab.name"
          :name="tab.name"
          :label="`${tab.label} ${taskCountMap[tab.name] || 0}`"
        />
      </el-tabs>

      <el-table
        :data="pagedRows"
        v-loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column label="候选人" min-width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToInterview(row)">
              {{ row.candidate_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="应聘岗位" min-width="150">
          <template #default="{ row }">
            <div class="cell-title">{{ row.job_name || '岗位 #' + row.job_id }}</div>
            <el-tag v-if="row.job_type" size="small" effect="plain" round>{{ row.job_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="任务状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="getTaskTagType(row.task_type)" effect="light" size="small">
              {{ getTaskLabel(row.task_type) }}
            </el-tag>
            <div class="sub-text">{{ getCandidateStatusLabel(row.current_status) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="面试轮次" min-width="140">
          <template #default="{ row }">
            <div class="cell-title">{{ row.round_name || getFallbackRoundName(row) }}</div>
            <div class="sub-text">{{ row.round_type || '面试' }} / {{ row.round_focus || '待确认' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="面试时间" min-width="145">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.scheduled_time) || '待安排' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="面试官/方式" min-width="130">
          <template #default="{ row }">
            <div class="cell-title">{{ row.interviewer || '待确认' }}</div>
            <div class="sub-text">{{ row.interview_method || '方式待定' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="评分/决策" min-width="120">
          <template #default="{ row }">
            <div v-if="row.score != null" class="score-text" :style="{ color: getScoreColor(row.score) }">
              {{ row.score }} 分
            </div>
            <div v-else class="text-muted">暂无评分</div>
            <div class="sub-text">{{ row.decision || row.conclusion || '待处理' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="145">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="goToInterview(row)">
              {{ getActionLabel(row.task_type) }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><User /></el-icon>
            <p class="empty-title">暂无面试任务</p>
            <p class="empty-desc">当前筛选条件下没有需要处理的面试任务。</p>
          </div>
        </template>
      </el-table>

      <div class="pagination-wrapper" v-if="filteredRows.length > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="filteredRows.length"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, User } from '@element-plus/icons-vue'
import { candidatesApi, interviewRoundsApi, jobsApi } from '../api/analysis.js'

const router = useRouter()
const route = useRoute()

const taskTabs = [
  { name: 'toArrange', label: '待安排' },
  { name: 'scheduled', label: '待面试' },
  { name: 'toRecord', label: '待填写记录' },
  { name: 'toDecision', label: '待决策' },
  { name: 'completed', label: '已完成' }
]

const taskTabNames = taskTabs.map(tab => tab.name)

const loading = ref(false)
const jobs = ref([])
const taskRows = ref([])
const activeTab = ref(getInitialTab())

const filters = reactive({
  candidate_name: '',
  job_id: null
})

const pagination = reactive({
  page: 1,
  page_size: 10
})

const statusLabels = {
  IMPORTED: '简历待解析',
  RESUME_PENDING: '简历待筛选',
  RESUME_SCREENING: '简历筛选中',
  RESUME_SCREENING_DONE: '初筛完成',
  RESUME_PASSED: '简历通过',
  RESUME_TBD: '简历待定',
  RESUME_REJECTED: '简历淘汰',
  INTERVIEW_WAITING: '待安排面试',
  INTERVIEW_SCHEDULED: '面试待进行',
  INTERVIEW_DECISION_PENDING: '面试完成待决策',
  FIRST_INTERVIEW_PENDING: '面试待进行',
  FIRST_INTERVIEW_IN_PROGRESS: '面试中',
  FIRST_INTERVIEW_PASSED: '面试完成待决策',
  FIRST_INTERVIEW_REJECTED: '面试淘汰',
  SECOND_INTERVIEW_PENDING: '下一轮待进行',
  SECOND_INTERVIEW_IN_PROGRESS: '下一轮面试中',
  SECOND_INTERVIEW_PASSED: '面试完成待决策',
  SECOND_INTERVIEW_REJECTED: '面试淘汰',
  FINAL_PASSED: '通过并结束',
  REJECTED: '已淘汰',
  ON_HOLD: '暂定',
  HIRED: '已录用',
  ONBOARDED: '已入职',
  ABANDONED: '已放弃',
  OFFER_ABANDONED: '放弃入职',
  TALENT_POOL: '人才库储备'
}

const interviewCandidateStatuses = new Set([
  'RESUME_PASSED',
  'INTERVIEW_WAITING',
  'INTERVIEW_SCHEDULED',
  'INTERVIEW_DECISION_PENDING',
  'ON_HOLD',
  'FIRST_INTERVIEW_PENDING',
  'FIRST_INTERVIEW_IN_PROGRESS',
  'FIRST_INTERVIEW_PASSED',
  'FIRST_INTERVIEW_REJECTED',
  'SECOND_INTERVIEW_PENDING',
  'SECOND_INTERVIEW_IN_PROGRESS',
  'SECOND_INTERVIEW_PASSED',
  'SECOND_INTERVIEW_REJECTED',
  'FINAL_PASSED',
  'REJECTED',
  'HIRED',
  'ONBOARDED',
  'ABANDONED',
  'OFFER_ABANDONED',
  'TALENT_POOL'
])

const arrangeStatuses = new Set(['RESUME_PASSED', 'INTERVIEW_WAITING', 'ON_HOLD'])
const scheduledStatuses = new Set([
  'INTERVIEW_SCHEDULED',
  'FIRST_INTERVIEW_PENDING',
  'FIRST_INTERVIEW_IN_PROGRESS',
  'SECOND_INTERVIEW_PENDING',
  'SECOND_INTERVIEW_IN_PROGRESS'
])
const decisionStatuses = new Set(['INTERVIEW_DECISION_PENDING', 'FIRST_INTERVIEW_PASSED', 'SECOND_INTERVIEW_PASSED'])
const completedStatuses = new Set([
  'FINAL_PASSED',
  'REJECTED',
  'FIRST_INTERVIEW_REJECTED',
  'SECOND_INTERVIEW_REJECTED',
  'HIRED',
  'ONBOARDED',
  'ABANDONED',
  'OFFER_ABANDONED',
  'TALENT_POOL'
])

function getInitialTab() {
  const tab = Array.isArray(route.query.stage) ? route.query.stage[0] : route.query.stage
  return taskTabNames.includes(tab) ? tab : 'toArrange'
}

const taskCountMap = computed(() => {
  return taskRows.value.reduce((acc, row) => {
    if (matchesFilters(row)) {
      acc[row.task_type] = (acc[row.task_type] || 0) + 1
    }
    return acc
  }, {})
})

const filteredRows = computed(() => {
  return taskRows.value
    .filter(row => row.task_type === activeTab.value)
    .filter(matchesFilters)
    .sort((a, b) => {
      const aTime = new Date(a.scheduled_time || a.updated_at || 0).getTime()
      const bTime = new Date(b.scheduled_time || b.updated_at || 0).getTime()
      return aTime - bTime
    })
})

const pagedRows = computed(() => {
  const start = (pagination.page - 1) * pagination.page_size
  return filteredRows.value.slice(start, start + pagination.page_size)
})

watch(activeTab, (tab) => {
  pagination.page = 1
  if (route.query.stage !== tab) {
    router.replace({ path: '/interviews', query: { ...route.query, stage: tab } })
  }
})

watch(() => route.query.stage, () => {
  const tab = getInitialTab()
  if (tab !== activeTab.value) activeTab.value = tab
})

function matchesFilters(row) {
  const keyword = filters.candidate_name.trim()
  if (keyword && !String(row.candidate_name || '').includes(keyword)) return false
  if (filters.job_id && row.job_id !== filters.job_id) return false
  return true
}

const fetchJobs = async () => {
  try {
    const response = await jobsApi.list({ page: 1, page_size: 100 })
    jobs.value = response.data.items || []
  } catch {
    jobs.value = []
  }
}

const fetchAllCandidates = async () => {
  const pageSize = 100
  let page = 1
  const items = []
  while (true) {
    const response = await candidatesApi.list({ page, page_size: pageSize })
    const currentItems = response.data.items || []
    items.push(...currentItems)
    const total = response.data.total || items.length
    if (items.length >= total || currentItems.length < pageSize) break
    page += 1
  }
  return items
}

const fetchCandidateRoundsMap = async (candidateIds) => {
  const uniqueIds = [...new Set(candidateIds.filter(Boolean))]
  const roundsMap = new Map(uniqueIds.map(candidateId => [candidateId, []]))
  const batchSize = 500

  for (let start = 0; start < uniqueIds.length; start += batchSize) {
    const ids = uniqueIds.slice(start, start + batchSize)
    const response = await interviewRoundsApi.batchList(ids)
    const items = response.data.items || []
    items.forEach(item => {
      roundsMap.set(item.candidate_id, Array.isArray(item.rounds) ? item.rounds : [])
    })
  }

  return roundsMap
}

const fetchData = async () => {
  loading.value = true
  try {
    const candidates = await fetchAllCandidates()
    const interviewCandidates = candidates.filter(candidate =>
      interviewCandidateStatuses.has(candidate.current_status)
    )
    const roundsByCandidateId = await fetchCandidateRoundsMap(interviewCandidates.map(candidate => candidate.id))
    const rows = interviewCandidates.map((candidate) => {
      const rounds = roundsByCandidateId.get(candidate.id) || []
      return buildTaskRows(candidate, rounds)
    })
    taskRows.value = rows.flat()
    pagination.page = 1
  } catch (error) {
    ElMessage.error('获取面试任务失败')
  } finally {
    loading.value = false
  }
}

const buildTaskRows = (candidate, rounds) => {
  const activeRounds = [...rounds]
    .filter(round => round.status !== 'CANCELED')
    .sort((a, b) => {
      if ((a.round_no || 0) !== (b.round_no || 0)) return (a.round_no || 0) - (b.round_no || 0)
      return String(a.created_at || '').localeCompare(String(b.created_at || ''))
    })
  const decisionRound = [...activeRounds].reverse().find(round => round.status === 'COMPLETED' && !round.decision)
  const scheduledRound = activeRounds.find(round => round.status === 'SCHEDULED')
  const latestRound = activeRounds[activeRounds.length - 1]

  if (decisionRound) return [buildRoundTask(candidate, decisionRound, 'toDecision')]
  if (scheduledRound) return [buildRoundTask(candidate, scheduledRound, isOverdue(scheduledRound.scheduled_time) ? 'toRecord' : 'scheduled')]
  if (latestRound?.status === 'COMPLETED') return [buildRoundTask(candidate, latestRound, 'completed')]
  if (arrangeStatuses.has(candidate.current_status)) return [buildCandidateTask(candidate, 'toArrange')]
  if (decisionStatuses.has(candidate.current_status)) return [buildCandidateTask(candidate, 'toDecision')]
  if (scheduledStatuses.has(candidate.current_status)) return [buildCandidateTask(candidate, 'scheduled')]
  if (completedStatuses.has(candidate.current_status)) return [buildCandidateTask(candidate, 'completed')]
  return []
}

const buildCandidateTask = (candidate, taskType) => ({
  task_id: `candidate-${candidate.id}-${taskType}`,
  candidate_id: candidate.id,
  candidate_name: candidate.candidate_name,
  job_id: candidate.job_id,
  job_name: candidate.job_name,
  job_type: candidate.job_type,
  current_status: candidate.current_status,
  task_type: taskType,
  round_no: candidate.current_round_no || null,
  round_name: '',
  round_type: '',
  round_focus: '',
  scheduled_time: null,
  interviewer: '',
  interview_method: '',
  score: candidate.second_interview_score ?? candidate.first_interview_score ?? null,
  conclusion: candidate.final_conclusion || '',
  decision: candidate.final_conclusion || '',
  updated_at: candidate.updated_at
})

const buildRoundTask = (candidate, round, taskType) => ({
  task_id: `round-${round.id}`,
  candidate_id: candidate.id,
  candidate_name: candidate.candidate_name,
  job_id: candidate.job_id,
  job_name: candidate.job_name,
  job_type: candidate.job_type,
  current_status: candidate.current_status,
  task_type: taskType,
  round_no: round.round_no,
  round_name: round.round_name,
  round_type: round.round_type,
  round_focus: round.round_focus,
  scheduled_time: round.scheduled_time,
  interviewer: round.interviewer,
  interview_method: round.interview_method,
  score: round.score,
  conclusion: round.conclusion,
  decision: round.decision,
  updated_at: round.updated_at || candidate.updated_at
})

const isOverdue = (time) => {
  if (!time) return false
  return new Date(time).getTime() <= Date.now()
}

const getTaskLabel = (type) => {
  const map = {
    toArrange: '待安排',
    scheduled: '待面试',
    toRecord: '待填写记录',
    toDecision: '待决策',
    completed: '已完成'
  }
  return map[type] || type
}

const getTaskTagType = (type) => {
  if (type === 'toArrange' || type === 'scheduled' || type === 'toRecord') return 'warning'
  if (type === 'toDecision') return 'primary'
  if (type === 'completed') return 'success'
  return 'info'
}

const getActionLabel = (type) => {
  const map = {
    toArrange: '安排面试',
    scheduled: '查看安排',
    toRecord: '填写记录',
    toDecision: '去决策',
    completed: '查看详情'
  }
  return map[type] || '查看详情'
}

const getFallbackRoundName = (row) => {
  if (row.task_type === 'toArrange') return '第 1 轮面试'
  if (row.round_no) return `第 ${row.round_no} 轮面试`
  return '面试轮次待定'
}

const getCandidateStatusLabel = (status) => statusLabels[status] || status || '—'

const getScoreColor = (score) => {
  if (score >= 80) return 'var(--color-green)'
  if (score >= 60) return 'var(--color-amber)'
  return 'var(--color-red)'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const handleSearch = () => {
  pagination.page = 1
}

const handleReset = () => {
  filters.candidate_name = ''
  filters.job_id = null
  pagination.page = 1
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
}

const handlePageChange = (page) => {
  pagination.page = page
}

const goToInterview = (row) => {
  router.push({
    path: `/candidates/${row.candidate_id}`,
    query: { tab: 'interview', from: 'interviews' }
  })
}

onMounted(() => {
  fetchJobs()
  fetchData()
})
</script>

<style scoped>
.interview-list {
  max-width: 1440px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.filter-section {
  padding: 16px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.filter-form :deep(.el-form-item__label) {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: var(--font-semibold);
  padding-bottom: 6px;
}

.filter-actions {
  margin-left: auto;
  margin-right: 0 !important;
}

.table-section {
  padding: 0;
}

.task-tabs {
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border);
}

.task-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.task-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.table-section :deep(.el-table__header th) {
  height: 46px;
}

.cell-title {
  font-size: 13px;
  color: var(--color-text);
  font-weight: var(--font-semibold);
  line-height: 1.5;
}

.sub-text {
  margin-top: 3px;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.4;
}

.time-cell {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.score-text {
  font-size: 13px;
  font-weight: var(--font-bold);
}

.text-muted {
  color: var(--color-text-muted);
  font-size: 13px;
}

.pagination-wrapper {
  padding: 14px 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.empty-title {
  font-size: 16px;
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  margin-top: 16px;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
  text-align: center;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-actions {
    margin-left: 0;
  }

  .filter-form :deep(.el-form-item) {
    width: 100%;
  }

  .filter-form :deep(.el-input),
  .filter-form :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
