<template>
  <div class="candidate-detail" v-if="candidate">
    <div class="detail-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain @click="triggerResumeScreening" :loading="screeningLoading">
          <el-icon><Search /></el-icon>
          {{ screeningLoading ? '筛选中...' : '开始简历筛选' }}
        </el-button>
      </div>
    </div>

    <!-- 基础信息卡片 -->
    <div class="page-card overview-card">
      <div class="overview-main">
        <div class="candidate-info">
          <h2 class="candidate-name">{{ candidate.candidate_name }}</h2>
          <div class="candidate-meta">
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><User /></el-icon>
              {{ candidate.job_name || '岗位 #' + candidate.job_id }}
            </span>
            <span class="meta-item" v-if="candidate.phone">
              <el-icon :size="14" color="#6B7280"><Phone /></el-icon>
              {{ candidate.phone }}
            </span>
            <span class="meta-item" v-if="candidate.email">
              <el-icon :size="14" color="#6B7280"><Message /></el-icon>
              {{ candidate.email }}
            </span>
            <span class="meta-item" v-if="candidate.source">
              <el-icon :size="14" color="#6B7280"><Connection /></el-icon>
              {{ candidate.source }}
            </span>
          </div>
        </div>
        <div class="status-section">
          <div class="current-status">
            <span class="status-label">当前状态</span>
            <el-tag effect="light" size="large">
              {{ getStatusLabel(candidate.current_status) }}
            </el-tag>
          </div>
          <div class="ai-suggestion" v-if="candidate.latest_ai_suggestion">
            <span class="status-label">AI 建议</span>
            <el-tag type="info" effect="light" size="large">
              {{ candidate.latest_ai_suggestion }}
            </el-tag>
          </div>
        </div>
      </div>

      <div class="scores-row">
        <div class="score-item">
          <div class="score-value" :style="{ color: getScoreColor(candidate.resume_match_score) }">
            {{ candidate.resume_match_score || '—' }}
          </div>
          <div class="score-label">简历匹配度</div>
        </div>
        <div class="score-item">
          <div class="score-value" :style="{ color: getScoreColor(candidate.first_interview_score) }">
            {{ candidate.first_interview_score || '—' }}
          </div>
          <div class="score-label">初试评分</div>
        </div>
        <div class="score-item">
          <div class="score-value" :style="{ color: getScoreColor(candidate.second_interview_score) }">
            {{ candidate.second_interview_score || '—' }}
          </div>
          <div class="score-label">复试评分</div>
        </div>
      </div>
    </div>

    <!-- 简历内容 -->
    <div class="page-card resume-card">
      <div class="section-header">
        <h3 class="section-title">简历内容</h3>
      </div>
      <div class="resume-content">{{ candidate.resume_text }}</div>
    </div>

    <!-- 简历筛选报告 -->
    <div class="page-card screening-card" v-if="resumeScreeningReport">
      <div class="section-header">
        <div class="section-icon screening-icon">
          <el-icon :size="20" color="#fff"><Search /></el-icon>
        </div>
        <h3 class="section-title">简历筛选报告</h3>
        <span class="section-time">{{ formatTime(resumeScreeningReport.created_at) }}</span>
      </div>

      <div class="report-summary">
        <div class="summary-score">
          <div class="score-circle" :style="{ background: getScoreCircleColor(resumeScreeningReport.score) }">
            <div class="score-value">{{ resumeScreeningReport.score }}</div>
            <div class="score-label">匹配度</div>
          </div>
        </div>
        <div class="summary-content">
          <div class="summary-suggestion">
            <span class="summary-label">AI 建议</span>
            <el-tag :type="getSuggestionType(resumeScreeningReport.suggestion)" effect="light">
              {{ resumeScreeningReport.suggestion }}
            </el-tag>
          </div>
          <div class="summary-risk" v-if="resumeScreeningReport.risk_level">
            <span class="summary-label">风险等级</span>
            <el-tag :type="getRiskType(resumeScreeningReport.risk_level)" effect="light">
              {{ resumeScreeningReport.risk_level }}风险
            </el-tag>
          </div>
        </div>
      </div>

      <div class="report-text" v-if="getReportField('summary')">
        {{ getReportField('summary') }}
      </div>

      <!-- 匹配优势 -->
      <div class="report-section" v-if="getReportField('strengths')?.length">
        <h4 class="report-section-title">匹配优势</h4>
        <div class="item-list">
          <div v-for="(item, index) in getReportField('strengths')" :key="index" class="advantage-card item-card">
            <div class="item-header">
              <span class="item-number">{{ index + 1 }}</span>
              <h5 class="item-title">{{ item.title }}</h5>
            </div>
            <p class="item-detail">{{ item.detail }}</p>
            <div class="item-evidence" v-if="item.evidence">
              <el-icon :size="14" color="#10B981"><InfoFilled /></el-icon>
              <span>证据：{{ item.evidence }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 不匹配点 -->
      <div class="report-section" v-if="getReportField('mismatches')?.length">
        <h4 class="report-section-title">不匹配点</h4>
        <div class="item-list">
          <div v-for="(item, index) in getReportField('mismatches')" :key="index" class="mismatch-card item-card">
            <div class="item-header">
              <span class="item-number">{{ index + 1 }}</span>
              <h5 class="item-title">{{ item.title }}</h5>
            </div>
            <p class="item-detail">{{ item.detail }}</p>
          </div>
        </div>
      </div>

      <!-- 风险点 -->
      <div class="report-section" v-if="getReportField('risk_points')?.length">
        <h4 class="report-section-title">风险点</h4>
        <div class="risk-list">
          <div v-for="(item, index) in getReportField('risk_points')" :key="index" class="risk-card" :class="`risk-${getRiskLevelClass(item.level)}`">
            <div class="risk-header">
              <div class="risk-title">
                <el-icon :size="16"><Warning /></el-icon>
                <span>{{ item.risk }}</span>
              </div>
              <el-tag :type="getRiskType(item.level)" effect="light" size="small">
                {{ item.level }}风险
              </el-tag>
            </div>
            <p class="risk-detail">{{ item.detail }}</p>
          </div>
        </div>
      </div>

      <!-- 建议追问 -->
      <div class="report-section" v-if="getReportField('follow_up_questions')?.length">
        <h4 class="report-section-title">建议追问问题</h4>
        <div class="follow-up-list">
          <div v-for="(item, index) in getReportField('follow_up_questions')" :key="index" class="follow-up-card">
            <div class="follow-up-number">{{ index + 1 }}</div>
            <div class="follow-up-content">
              <p class="follow-up-question">{{ item.question }}</p>
              <p class="follow-up-purpose" v-if="item.purpose">
                <el-icon :size="14" color="#8B5CF6"><Aim /></el-icon>
                <span>{{ item.purpose }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 初试记录与分析 -->
    <div class="page-card first-interview-card">
      <div class="section-header">
        <div class="section-icon interview-icon">
          <el-icon :size="20" color="#fff"><ChatLineRound /></el-icon>
        </div>
        <h3 class="section-title">初试记录</h3>
      </div>

      <div class="empty-interview" v-if="!firstInterviewRecord">
        <p>暂无初试记录</p>
        <el-button type="primary" plain @click="goToAddInterviewRecord">
          <el-icon><Plus /></el-icon>
          添加初试记录
        </el-button>
      </div>

      <div class="interview-content" v-else>
        <div class="interview-meta">
          <span v-if="firstInterviewRecord.interviewer_name">
            面试官：{{ firstInterviewRecord.interviewer_name }}
          </span>
          <span v-if="firstInterviewRecord.interview_time">
            面试时间：{{ formatTime(firstInterviewRecord.interview_time) }}
          </span>
        </div>
        <div class="interview-text">{{ firstInterviewRecord.record_text }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search, User, Phone, Message, Connection, InfoFilled, Warning, Aim, ChatLineRound, Plus } from '@element-plus/icons-vue'
import { candidatesApi, screeningApi, firstInterviewRecordApi } from '../api/analysis.js'

const route = useRoute()
const router = useRouter()

const candidate = ref(null)
const resumeScreeningReport = ref(null)
const firstInterviewRecord = ref(null)
const screeningLoading = ref(false)

const getScoreColor = (score) => {
  if (!score) return '#9CA3AF'
  if (score >= 80) return '#10B981'
  if (score >= 60) return '#F59E0B'
  return '#EF4444'
}

const getScoreCircleColor = (score) => {
  if (!score) return 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%)'
  if (score >= 80) return 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
  if (score >= 60) return 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
  return 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'
}

const getSuggestionType = (suggestion) => {
  if (suggestion === '建议约初试' || suggestion === '建议进入复试') return 'success'
  if (suggestion === '人才库储备') return 'warning'
  return 'danger'
}

const getRiskType = (level) => {
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  return 'danger'
}

const getRiskLevelClass = (level) => {
  if (level === '高') return 'high'
  if (level === '中') return 'medium'
  return 'low'
}

const getStatusLabel = (status) => {
  const statusMap = {
    'IMPORTED': '已导入',
    'RESUME_PENDING': '简历待筛选',
    'RESUME_PASSED': '简历通过',
    'RESUME_REJECTED': '简历淘汰',
    'FIRST_INTERVIEW_PENDING': '待初试',
    'FIRST_INTERVIEW_PASSED': '初试通过',
    'FIRST_INTERVIEW_REJECTED': '初试淘汰',
    'SECOND_INTERVIEW_PENDING': '待复试',
    'SECOND_INTERVIEW_PASSED': '复试通过',
    'SECOND_INTERVIEW_REJECTED': '复试淘汰',
    'HIRED': '已录用',
    'ABANDONED': '已放弃',
    'TALENT_POOL': '人才库储备'
  }
  return statusMap[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const getReportField = (field) => {
  if (!resumeScreeningReport.value) return null
  try {
    const report = JSON.parse(resumeScreeningReport.value.report_json)
    return report[field]
  } catch (error) {
    return null
  }
}

const fetchCandidate = async () => {
  try {
    const response = await candidatesApi.getById(route.params.id)
    candidate.value = response.data
  } catch (error) {
    ElMessage.error('获取候选人详情失败')
  }
}

const fetchResumeScreeningReport = async () => {
  try {
    const response = await screeningApi.getLatest(route.params.id)
    resumeScreeningReport.value = response.data
  } catch (error) {
    // 可能还没有报告
    resumeScreeningReport.value = null
  }
}

const fetchFirstInterviewRecord = async () => {
  try {
    const response = await firstInterviewRecordApi.getLatest(route.params.id)
    firstInterviewRecord.value = response.data
  } catch (error) {
    firstInterviewRecord.value = null
  }
}

const triggerResumeScreening = async () => {
  screeningLoading.value = true
  try {
    await screeningApi.trigger(route.params.id, { force: false, request_id: null })
    ElMessage.success('简历筛选完成')
    await fetchResumeScreeningReport()
    await fetchCandidate() // 刷新分数
  } catch (error) {
    const message = error.response?.data?.detail || '简历筛选失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    screeningLoading.value = false
  }
}

const goBack = () => {
  if (candidate.value?.job_id) {
    router.push(`/jobs/${candidate.value.job_id}`)
  } else {
    router.push('/candidates')
  }
}

const goToAddInterviewRecord = () => {
  // TODO: 创建添加初试记录的对话框或页面
  ElMessage.info('功能开发中')
}

onMounted(() => {
  fetchCandidate()
  fetchResumeScreeningReport()
  fetchFirstInterviewRecord()
})
</script>

<style scoped>
.candidate-detail {
  max-width: 1180px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-card {
  padding: 28px 32px;
  margin-bottom: 20px;
}

.overview-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.candidate-info {
  flex: 1;
}

.candidate-name {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px 0;
}

.candidate-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6B7280;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.status-label {
  font-size: 13px;
  color: #9CA3AF;
  margin-right: 8px;
}

.scores-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding-top: 20px;
  border-top: 1px solid #F3F4F6;
}

.score-item {
  text-align: center;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.score-label {
  font-size: 13px;
  color: #6B7280;
  margin-top: 4px;
}

.resume-card {
  padding: 28px 32px;
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
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.section-time {
  font-size: 13px;
  color: #9CA3AF;
  margin-left: auto;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.screening-icon {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
}

.interview-icon {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
}

.resume-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
}

.screening-card {
  padding: 28px 32px;
  margin-bottom: 20px;
}

.report-summary {
  display: flex;
  gap: 32px;
  margin-bottom: 24px;
}

.score-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.score-circle .score-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.score-circle .score-label {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-label {
  font-size: 13px;
  color: #9CA3AF;
  margin-right: 8px;
}

.report-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.8;
  margin-bottom: 24px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 12px 0;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-card {
  padding: 16px 20px;
  border-radius: 10px;
  border-left: 4px solid;
}

.advantage-card {
  background: #F0FDF4;
  border-left-color: #10B981;
}

.mismatch-card {
  background: #FFF7ED;
  border-left-color: #F97316;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.item-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #6B7280;
  flex-shrink: 0;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.item-detail {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0 0 8px 0;
  padding-left: 34px;
}

.item-evidence {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #6B7280;
  padding-left: 34px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-card {
  padding: 16px 20px;
  border-radius: 10px;
  border: 1px solid;
}

.risk-high {
  background: #FEF2F2;
  border-color: #FECACA;
}

.risk-medium {
  background: #FFFBEB;
  border-color: #FEF3C7;
}

.risk-low {
  background: #F0FDF4;
  border-color: #BBF7D0;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.risk-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.risk-detail {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0;
}

.follow-up-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.follow-up-card {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  background: #F5F3FF;
  border-radius: 10px;
  border: 1px solid #EDE9FE;
}

.follow-up-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.follow-up-content {
  flex: 1;
}

.follow-up-question {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.follow-up-purpose {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #8B5CF6;
  margin: 0;
}

.first-interview-card {
  padding: 28px 32px;
}

.empty-interview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 20px;
  color: #9CA3AF;
}

.interview-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #6B7280;
}

.interview-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
