<template>
  <div class="job-detail" v-if="job">
    <div class="detail-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain @click="goToNewCandidate">
          <el-icon><Plus /></el-icon>
          导入候选人
        </el-button>
      </div>
    </div>

    <div class="page-card overview-card">
      <div class="overview-main">
        <div class="job-info">
          <h2 class="job-name">{{ job.job_name }}</h2>
          <div class="job-meta">
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><OfficeBuilding /></el-icon>
              {{ job.department }}
            </span>
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><User /></el-icon>
              招聘 {{ job.headcount }} 人
            </span>
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><Clock /></el-icon>
              {{ formatTime(job.created_at) }}
            </span>
          </div>
        </div>
        <div class="job-status">
          <el-tag :type="getStatusType(job.status)" effect="light" size="large">
            {{ getStatusLabel(job.status) }}
          </el-tag>
        </div>
      </div>

      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ job.candidate_count }}</div>
          <div class="stat-label">候选人数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ job.resume_passed_count }}</div>
          <div class="stat-label">简历通过</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ job.first_interview_passed_count }}</div>
          <div class="stat-label">面试推进</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ job.second_interview_passed_count }}</div>
          <div class="stat-label">后续通过</div>
        </div>
      </div>
    </div>

    <div class="page-card jd-card">
      <div class="section-header">
        <h3 class="section-title">岗位 JD / 岗位要求</h3>
      </div>
      <div class="jd-content">{{ job.jd_text }}</div>
    </div>

    <div class="page-card candidates-card">
      <div class="section-header">
        <h3 class="section-title">候选人列表</h3>
      </div>

      <el-table
        :data="candidates"
        v-loading="loadingCandidates"
        style="width: 100%"
      >
        <el-table-column prop="candidate_name" label="候选人" min-width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewCandidate(row.id)">
              {{ row.candidate_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系方式" min-width="120" />
        <el-table-column prop="source" label="来源" min-width="80" />
        <el-table-column label="当前状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getCandidateStatusType(row.current_status)" effect="light" size="small">
              {{ getCandidateStatusLabel(row.current_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="简历匹配度" min-width="90">
          <template #default="{ row }">
            <span v-if="row.resume_match_score != null" class="score-text" :style="{ color: getScoreColor(row.resume_match_score) }">{{ row.resume_match_score }}分</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="面试评分" min-width="90">
          <template #default="{ row }">
            <span v-if="getLatestInterviewScore(row) != null" class="score-text" :style="{ color: getScoreColor(getLatestInterviewScore(row)) }">{{ getLatestInterviewScore(row) }}分</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="viewCandidate(row.id)">
              查看
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><User /></el-icon>
            <p class="empty-title">暂无候选人</p>
            <p class="empty-desc">点击「导入候选人」，开始筛选第一位候选人</p>
          </div>
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, OfficeBuilding, User, Clock } from '@element-plus/icons-vue'
import { jobsApi, candidatesApi } from '../api/analysis.js'

const route = useRoute()
const router = useRouter()

const job = ref(null)
const candidates = ref([])
const loadingCandidates = ref(false)

const getStatusType = (status) => {
  if (status === 'OPEN') return 'success'
  if (status === 'PAUSED') return 'warning'
  return 'info'
}

const getStatusLabel = (status) => {
  if (status === 'OPEN') return '招聘中'
  if (status === 'PAUSED') return '已暂停'
  if (status === 'CLOSED') return '已关闭'
  return status
}

const candidateStatusTypeMap = {
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

const candidateStatusLabelMap = {
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

const getCandidateStatusType = (status) => candidateStatusTypeMap[status] || 'info'
const getCandidateStatusLabel = (status) => candidateStatusLabelMap[status] || status
const getLatestInterviewScore = (row) => row.second_interview_score ?? row.first_interview_score ?? null
const getScoreColor = (score) => {
  if (score >= 80) return '#059669'
  if (score >= 60) return '#d97706'
  return '#dc2626'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const fetchJob = async () => {
  try {
    const response = await jobsApi.getById(route.params.id)
    job.value = response.data
  } catch (error) {
    ElMessage.error('获取岗位详情失败')
  }
}

const fetchCandidates = async () => {
  loadingCandidates.value = true
  try {
    const response = await candidatesApi.list({
      job_id: route.params.id,
      page: 1,
      page_size: 100
    })
    candidates.value = response.data.items
  } catch (error) {
    ElMessage.error('获取候选人列表失败')
  } finally {
    loadingCandidates.value = false
  }
}

const goBack = () => {
  router.push('/jobs')
}

const goToNewCandidate = () => {
  router.push(`/candidates/new?job_id=${route.params.id}`)
}

const viewCandidate = (id) => {
  router.push(`/candidates/${id}`)
}

onMounted(() => {
  fetchJob()
  fetchCandidates()
})
</script>

<style scoped>
.job-detail {
  max-width: 1440px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-card {
  padding: 24px;
  margin-bottom: 20px;
}

.overview-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.job-info {
  flex: 1;
}

.job-name {
  font-size: 26px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 12px 0;
  letter-spacing: 0;
}

.job-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.stat-card {
  min-height: 82px;
  padding: 12px 16px;
  border-right: 1px solid var(--color-border);
  text-align: center;
}

.stat-card:last-child {
  border-right: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  font-weight: var(--font-semibold);
}

.jd-card {
  padding: 24px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0;
}

.jd-content {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  padding: 16px;
  border-radius: var(--radius-card);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
}

.candidates-card {
  padding: 24px;
}

.candidates-card :deep(.el-table) {
  border-radius: var(--radius-card);
}

.time-cell {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.text-muted {
  color: var(--color-text-muted);
}

.score-text {
  font-size: 13px;
  font-weight: var(--font-bold);
  white-space: nowrap;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
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
}

@media (max-width: 900px) {
  .overview-main,
  .detail-header {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
