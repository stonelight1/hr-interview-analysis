<template>
  <div class="candidate-list">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ pageTitle }}</h2>
        <p class="page-subtitle">{{ pageSubtitle }}</p>
      </div>
      <el-button plain size="large" @click="goToNew">
        <el-icon><Plus /></el-icon>
        手动新增候选人
      </el-button>
    </div>

    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="候选人姓名" class="filter-item">
          <el-input v-model="filters.candidate_name" placeholder="请输入" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item label="应聘岗位" class="filter-item">
          <el-select v-model="filters.job_id" placeholder="请选择" clearable style="width: 160px" filterable>
            <el-option v-for="job in jobs" :key="job.id" :label="job.job_name" :value="job.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="当前阶段" class="filter-item">
          <el-select v-model="filters.current_status" placeholder="请选择" clearable style="width: 150px">
            <el-option label="简历待解析" value="IMPORTED" />
            <el-option label="简历待筛选" value="RESUME_PENDING" />
            <el-option label="简历通过" value="RESUME_PASSED" />
            <el-option label="简历淘汰" value="RESUME_REJECTED" />
            <el-option label="待安排面试" value="INTERVIEW_WAITING" />
            <el-option label="面试待进行" value="INTERVIEW_SCHEDULED" />
            <el-option label="面试完成待决策" value="INTERVIEW_DECISION_PENDING" />
            <el-option label="面试待进行" value="FIRST_INTERVIEW_PENDING" />
            <el-option label="面试完成待决策" value="FIRST_INTERVIEW_PASSED" />
            <el-option label="面试淘汰" value="FIRST_INTERVIEW_REJECTED" />
            <el-option label="下一轮待进行" value="SECOND_INTERVIEW_PENDING" />
            <el-option label="面试完成待决策" value="SECOND_INTERVIEW_PASSED" />
            <el-option label="面试淘汰" value="SECOND_INTERVIEW_REJECTED" />
            <el-option label="已录用" value="HIRED" />
            <el-option label="已放弃" value="ABANDONED" />
            <el-option label="人才库储备" value="TALENT_POOL" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI 建议" class="filter-item">
          <el-select v-model="filters.recommendation" placeholder="请选择" clearable style="width: 130px">
            <el-option label="建议通过" value="建议进入下一轮" />
            <el-option label="暂缓" value="暂缓" />
            <el-option label="不建议" value="不建议" />
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
      <el-table
        :data="tableData"
        v-loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column label="候选人" min-width="110">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">
              {{ row.candidate_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="应聘岗位" min-width="130">
          <template #default="{ row }">
            <div class="cell-text">{{ row.job_name || '岗位 #' + row.job_id }}</div>
            <div class="cell-tag" v-if="row.job_type">
              <el-tag size="small" effect="plain" round>{{ row.job_type }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="当前阶段" min-width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.current_status)" effect="light" size="small">
              {{ getStatusLabel(row.current_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="简历匹配度" min-width="100" align="center">
          <template #default="{ row }">
            <div v-if="row.resume_match_score != null" class="score-cell">
              <el-progress
                :percentage="row.resume_match_score"
                :color="getScoreColor(row.resume_match_score)"
                :stroke-width="6"
                :show-text="false"
                style="width: 50px"
              />
              <span class="score-text" :style="{ color: getScoreColor(row.resume_match_score) }">
                {{ row.resume_match_score }}
              </span>
            </div>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="最近面试评分" min-width="110" align="center">
          <template #default="{ row }">
            <span v-if="getLatestInterviewScore(row) != null" class="score-num" :style="{ color: getScoreColor(getLatestInterviewScore(row)) }">
              {{ getLatestInterviewScore(row) }}
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" min-width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.latest_ai_suggestion === '不建议'" class="risk-badge risk-high">高</span>
            <span v-else-if="row.latest_ai_suggestion === '暂缓'" class="risk-badge risk-medium">中</span>
            <span v-else-if="row.latest_ai_suggestion" class="risk-badge risk-low">低</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="下一步动作" min-width="120">
          <template #default="{ row }">
            <el-tag :type="getNextActionType(row.current_status)" effect="dark" size="small">
              {{ getNextAction(row.current_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="140">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" link size="small" @click="viewDetail(row.id)">查看</el-button>
              <el-button
                v-if="row.current_status === 'RESUME_PENDING'"
                type="success" link size="small"
                @click="goToScreening(row.id)"
              >筛选</el-button>
              <el-button
                v-if="['RESUME_PASSED', 'INTERVIEW_WAITING', 'INTERVIEW_SCHEDULED', 'FIRST_INTERVIEW_PENDING', 'SECOND_INTERVIEW_PENDING'].includes(row.current_status)"
                type="warning" link size="small"
                @click="goToArrangeInterview(row.id)"
              >{{ getPrimaryActionLabel(row.current_status) }}</el-button>
              <el-button
                v-if="['INTERVIEW_DECISION_PENDING', 'FIRST_INTERVIEW_PASSED', 'SECOND_INTERVIEW_PASSED'].includes(row.current_status)"
                type="primary" link size="small"
                @click="viewDetail(row.id)"
              >决策</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><User /></el-icon>
            <p class="empty-title">暂无候选人数据</p>
            <p class="empty-desc">请从岗位初筛工作台批量导入简历，系统会自动完成简历解析与筛选</p>
            <div class="empty-actions">
              <el-button type="primary" @click="goToScreeningWorkbench">
                进入岗位初筛
              </el-button>
              <el-button plain @click="goToNew">
                <el-icon><Plus /></el-icon>
                手动新增候选人
              </el-button>
            </div>
          </div>
        </template>
      </el-table>

      <div class="pagination-wrapper" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search, User } from '@element-plus/icons-vue'
import { candidatesApi, jobsApi } from '../api/analysis.js'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const tableData = ref([])
const jobs = ref([])

const filters = reactive({
  candidate_name: '',
  job_id: null,
  current_status: '',
  recommendation: ''
})

// 从 URL query 初始化筛选条件
const applyRouteQuery = () => {
  if (route.query.status) {
    filters.current_status = route.query.status
  } else {
    filters.current_status = ''
  }
}

// 路由变化时重新筛选
watch(() => route.fullPath, () => {
  applyRouteQuery()
  pagination.page = 1
  fetchData()
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const statusTypeMap = {
  IMPORTED: 'info',
  RESUME_PENDING: 'warning',
  RESUME_PASSED: 'success',
  RESUME_REJECTED: 'danger',
  INTERVIEW_WAITING: 'warning',
  INTERVIEW_SCHEDULED: 'warning',
  INTERVIEW_DECISION_PENDING: 'warning',
  FINAL_PASSED: 'success',
  REJECTED: 'danger',
  ON_HOLD: 'info',
  FIRST_INTERVIEW_PENDING: 'warning',
  FIRST_INTERVIEW_PASSED: 'success',
  FIRST_INTERVIEW_REJECTED: 'danger',
  SECOND_INTERVIEW_PENDING: 'warning',
  SECOND_INTERVIEW_PASSED: 'success',
  SECOND_INTERVIEW_REJECTED: 'danger',
  HIRED: 'success',
  ABANDONED: 'info',
  TALENT_POOL: 'info'
}

const statusLabelMap = {
  IMPORTED: '简历待解析',
  RESUME_PENDING: '简历待筛选',
  RESUME_PASSED: '简历通过',
  RESUME_REJECTED: '简历淘汰',
  INTERVIEW_WAITING: '待安排面试',
  INTERVIEW_SCHEDULED: '面试待进行',
  INTERVIEW_DECISION_PENDING: '面试完成待决策',
  FINAL_PASSED: '通过并结束',
  REJECTED: '已淘汰',
  ON_HOLD: '暂定',
  FIRST_INTERVIEW_PENDING: '面试待进行',
  FIRST_INTERVIEW_PASSED: '面试完成待决策',
  FIRST_INTERVIEW_REJECTED: '面试淘汰',
  SECOND_INTERVIEW_PENDING: '下一轮待进行',
  SECOND_INTERVIEW_PASSED: '面试完成待决策',
  SECOND_INTERVIEW_REJECTED: '面试淘汰',
  HIRED: '已录用',
  ABANDONED: '已放弃',
  TALENT_POOL: '人才库储备'
}

const nextActionMap = {
  RESUME_PENDING: '生成简历筛选',
  RESUME_PASSED: '安排面试',
  INTERVIEW_WAITING: '安排面试',
  INTERVIEW_SCHEDULED: '填写记录',
  INTERVIEW_DECISION_PENDING: 'HR 决策',
  ON_HOLD: '暂定',
  REJECTED: '已淘汰',
  FINAL_PASSED: '已结束',
  FIRST_INTERVIEW_PENDING: '填写记录',
  FIRST_INTERVIEW_PASSED: 'HR 决策',
  SECOND_INTERVIEW_PENDING: '填写记录',
  SECOND_INTERVIEW_PASSED: 'HR 决策',
  IMPORTED: '待解析简历'
}

const getStatusType = (s) => statusTypeMap[s] || 'info'
const getStatusLabel = (s) => statusLabelMap[s] || s
const getNextAction = (s) => nextActionMap[s] || '—'
const getLatestInterviewScore = (row) => row.second_interview_score ?? row.first_interview_score ?? null
const getPrimaryActionLabel = (s) => ['RESUME_PASSED', 'INTERVIEW_WAITING'].includes(s) ? '安排' : '记录'

const getNextActionType = (s) => {
  if (['RESUME_PENDING', 'INTERVIEW_WAITING', 'INTERVIEW_SCHEDULED', 'INTERVIEW_DECISION_PENDING', 'FIRST_INTERVIEW_PENDING', 'SECOND_INTERVIEW_PENDING'].includes(s)) return 'warning'
  if (['RESUME_PASSED', 'FINAL_PASSED', 'FIRST_INTERVIEW_PASSED', 'SECOND_INTERVIEW_PASSED'].includes(s)) return 'success'
  return 'info'
}

const getScoreColor = (score) => {
  if (score >= 80) return 'var(--color-green)'
  if (score >= 60) return 'var(--color-amber)'
  return 'var(--color-red)'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchJobs = async () => {
  try {
    const res = await jobsApi.list({ page: 1, page_size: 100 })
    jobs.value = res.data.items
  } catch (e) { /* ignore */ }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.candidate_name) params.candidate_name = filters.candidate_name
    if (filters.job_id) params.job_id = filters.job_id
    if (filters.current_status) params.current_status = filters.current_status

    const response = await candidatesApi.list(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取候选人列表失败')
  } finally {
    loading.value = false
  }
}

// 页面标题根据筛选状态联动
const pageTitle = computed(() => {
  if (route.path === '/interviews') return '面试管理'
  const s = route.query.status
  if (s === 'RESUME_PENDING') return '简历筛选'
  if (s === 'FIRST_INTERVIEW_PASSED') return '面试决策'
  return '候选人管理'
})

const pageSubtitle = computed(() => {
  if (route.path === '/interviews') return '管理开放式面试流程，由 HR 根据每轮结果决定下一步'
  const s = route.query.status
  if (s === 'RESUME_PENDING') return '查看待筛选简历，使用 AI 快速评估候选人匹配度'
  if (s === 'FIRST_INTERVIEW_PASSED') return '查看面试完成待决策的候选人，决定结束、暂定、淘汰或进入下一轮'
  return '查看所有候选人，快速筛选并推进招聘流程'
})

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => {
  filters.candidate_name = ''
  filters.job_id = null
  filters.current_status = ''
  filters.recommendation = ''
  pagination.page = 1
  fetchData()
}
const handleSizeChange = (size) => { pagination.page_size = size; pagination.page = 1; fetchData() }
const handlePageChange = (page) => { pagination.page = page; fetchData() }
const viewDetail = (id) => router.push(`/candidates/${id}`)
const goToNew = () => router.push('/candidates/new')
const goToJobNew = () => router.push('/jobs/new')
const goToScreeningWorkbench = () => router.push('/screening')
const goToScreening = (id) => router.push(`/candidates/${id}`)
const goToArrangeInterview = (id) => router.push(`/candidates/${id}`)

onMounted(() => {
  applyRouteQuery()
  fetchJobs()
  fetchData()
})
</script>

<style scoped>
.candidate-list {
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

.table-section :deep(.el-table) {
  border-radius: var(--radius-card);
}

.table-section :deep(.el-table__header th) {
  height: 46px;
}

.table-section :deep(.el-table__row) {
  transition: background-color 0.2s ease;
}

.cell-text {
  font-size: 13px;
  color: var(--color-text);
  font-weight: var(--font-semibold);
}

.cell-tag {
  margin-top: 4px;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.score-text {
  font-size: 13px;
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

.score-num {
  font-size: 16px;
  font-weight: var(--font-bold);
}

.risk-badge {
  display: inline-block;
  min-width: 28px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: var(--font-semibold);
}

.risk-high { color: var(--color-red); background: var(--color-red-soft); }
.risk-medium { color: var(--color-amber); background: var(--color-amber-soft); }
.risk-low { color: var(--color-primary); background: var(--color-primary-soft); }

.time-cell {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.text-muted { color: var(--color-text-muted); }

.action-btns {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
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
  margin: 0 0 20px 0;
  text-align: center;
  max-width: 400px;
}

.empty-actions {
  display: flex;
  gap: 12px;
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
