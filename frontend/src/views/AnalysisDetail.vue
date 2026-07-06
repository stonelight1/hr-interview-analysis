<template>
  <div class="analysis-detail" v-if="analysis">
    <!-- 顶部操作栏 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain @click="copyReport">
          <el-icon><DocumentCopy /></el-icon>
          复制报告
        </el-button>
        <el-button type="danger" plain @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 顶部概要卡片 -->
    <div class="page-card overview-card">
      <div class="overview-main">
        <div class="candidate-info">
          <h2 class="candidate-name">{{ analysis.candidate_name }}</h2>
          <div class="candidate-meta">
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><Briefcase /></el-icon>
              {{ analysis.job_title }}
            </span>
            <span class="meta-item">
              <el-icon :size="14" color="#6B7280"><Clock /></el-icon>
              {{ formatTime(analysis.created_at) }}
            </span>
          </div>
        </div>
        <div class="score-circle" :style="{ background: scoreCircleColor }">
          <div class="score-value">{{ analysis.match_score }}</div>
          <div class="score-label">匹配度</div>
        </div>
      </div>
      <div class="overview-tags">
        <div class="tag-item">
          <span class="tag-label">录用建议</span>
          <el-tag
            :type="recommendationType"
            effect="light"
            size="large"
            class="result-tag"
          >
            {{ analysis.recommendation }}
          </el-tag>
        </div>
        <div class="tag-item">
          <span class="tag-label">风险等级</span>
          <el-tag
            :type="riskLevelType"
            effect="light"
            size="large"
            class="result-tag"
          >
            {{ analysis.risk_level }}
          </el-tag>
        </div>
        <div class="tag-item">
          <span class="tag-label">AI 置信度</span>
          <el-tag
            type="info"
            effect="light"
            size="large"
            class="result-tag"
          >
            {{ analysis.confidence }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="detail-content" v-if="analysisResult">
      <!-- 总体结论 -->
      <div class="page-card section-card">
        <div class="section-header">
          <div class="section-icon">
            <el-icon :size="20" color="#2563EB"><Document /></el-icon>
          </div>
          <h3 class="section-title">总体结论</h3>
        </div>
        <p class="summary-text">{{ analysisResult.candidate_overview?.summary }}</p>
        <div class="leader-card" v-if="analysisResult.leader_summary">
          <div class="leader-header">
            <el-icon :size="16" color="#2563EB"><User /></el-icon>
            <span>给领导看的简短结论</span>
          </div>
          <p class="leader-text">{{ analysisResult.leader_summary.short_conclusion }}</p>
          <div class="leader-decision">
            <span class="decision-label">决策建议：</span>
            <el-tag :type="getDecisionType(analysisResult.leader_summary.decision)" effect="light">
              {{ analysisResult.leader_summary.decision }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 评分明细 -->
      <div class="page-card section-card" v-if="analysisResult.score_detail">
        <div class="section-header">
          <div class="section-icon">
            <el-icon :size="20" color="#10B981"><TrendCharts /></el-icon>
          </div>
          <h3 class="section-title">评分明细</h3>
        </div>
        <div class="score-grid">
          <div
            v-for="(item, index) in scoreDetailData"
            :key="index"
            class="score-card"
          >
            <div class="score-card-header">
              <span class="score-card-name">{{ item.name }}</span>
              <span class="score-card-value" :style="{ color: getScoreColor(item.score / item.max_score) }">
                {{ item.score }}<span class="score-card-max">/{{ item.max_score }}</span>
              </span>
            </div>
            <el-progress
              :percentage="(item.score / item.max_score) * 100"
              :color="getScoreColor(item.score / item.max_score)"
              :stroke-width="6"
              :show-text="false"
            />
            <p class="score-card-reason">{{ item.reason }}</p>
          </div>
        </div>
      </div>

      <!-- 候选人优势 -->
      <div class="page-card section-card" v-if="analysisResult.candidate_analysis?.advantages?.length">
        <div class="section-header">
          <div class="section-icon advantage-icon">
            <el-icon :size="20" color="#fff"><CircleCheck /></el-icon>
          </div>
          <h3 class="section-title">候选人优势</h3>
        </div>
        <div class="item-list">
          <div
            v-for="(item, index) in analysisResult.candidate_analysis.advantages"
            :key="index"
            class="advantage-card item-card"
          >
            <div class="item-header">
              <span class="item-number">{{ index + 1 }}</span>
              <h4 class="item-title">{{ item.title }}</h4>
            </div>
            <p class="item-detail">{{ item.detail }}</p>
            <div class="item-evidence" v-if="item.evidence">
              <el-icon :size="14" color="#10B981"><InfoFilled /></el-icon>
              <span>证据：{{ item.evidence }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 候选人不足 -->
      <div class="page-card section-card" v-if="analysisResult.candidate_analysis?.weaknesses?.length">
        <div class="section-header">
          <div class="section-icon weakness-icon">
            <el-icon :size="20" color="#fff"><Warning /></el-icon>
          </div>
          <h3 class="section-title">候选人不足</h3>
        </div>
        <div class="item-list">
          <div
            v-for="(item, index) in analysisResult.candidate_analysis.weaknesses"
            :key="index"
            class="weakness-card item-card"
          >
            <div class="item-header">
              <span class="item-number">{{ index + 1 }}</span>
              <h4 class="item-title">{{ item.title }}</h4>
            </div>
            <p class="item-detail">{{ item.detail }}</p>
            <div class="item-evidence" v-if="item.evidence">
              <el-icon :size="14" color="#F59E0B"><InfoFilled /></el-icon>
              <span>证据：{{ item.evidence }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 风险点 -->
      <div class="page-card section-card" v-if="analysisResult.candidate_analysis?.risk_points?.length">
        <div class="section-header">
          <div class="section-icon risk-icon">
            <el-icon :size="20" color="#fff"><WarningFilled /></el-icon>
          </div>
          <h3 class="section-title">风险点</h3>
        </div>
        <div class="risk-list">
          <div
            v-for="(item, index) in analysisResult.candidate_analysis.risk_points"
            :key="index"
            class="risk-card"
            :class="`risk-${getRiskLevelClass(item.level)}`"
          >
            <div class="risk-header">
              <div class="risk-title">
                <el-icon :size="16"><WarningFilled /></el-icon>
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
      <div class="page-card section-card" v-if="analysisResult.follow_up_questions?.length">
        <div class="section-header">
          <div class="section-icon">
            <el-icon :size="20" color="#8B5CF6"><QuestionFilled /></el-icon>
          </div>
          <h3 class="section-title">建议追问问题</h3>
        </div>
        <div class="follow-up-list">
          <div
            v-for="(item, index) in analysisResult.follow_up_questions"
            :key="index"
            class="follow-up-card"
          >
            <div class="follow-up-number">{{ index + 1 }}</div>
            <div class="follow-up-content">
              <p class="follow-up-question">{{ item.question }}</p>
              <p class="follow-up-purpose">
                <el-icon :size="14" color="#8B5CF6"><Aim /></el-icon>
                <span>{{ item.purpose }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- HR 面试复盘 -->
      <div class="page-card section-card" v-if="analysisResult.hr_interview_feedback">
        <div class="section-header">
          <div class="section-icon">
            <el-icon :size="20" color="#F59E0B"><User /></el-icon>
          </div>
          <h3 class="section-title">HR 面试复盘</h3>
        </div>
        <div class="hr-feedback">
          <div class="feedback-block">
            <h4 class="feedback-subtitle">总体评价</h4>
            <p class="feedback-text">{{ analysisResult.hr_interview_feedback.overall_comment }}</p>
          </div>

          <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.strengths?.length">
            <h4 class="feedback-subtitle feedback-success">
              <el-icon :size="16" color="#10B981"><CircleCheck /></el-icon>
              做得好的地方
            </h4>
            <ul class="feedback-list">
              <li v-for="(item, index) in analysisResult.hr_interview_feedback.strengths" :key="index">
                {{ item }}
              </li>
            </ul>
          </div>

          <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.improvements?.length">
            <h4 class="feedback-subtitle feedback-warning">
              <el-icon :size="16" color="#F59E0B"><Warning /></el-icon>
              需要改进
            </h4>
            <ul class="feedback-list">
              <li v-for="(item, index) in analysisResult.hr_interview_feedback.improvements" :key="index">
                {{ item }}
              </li>
            </ul>
          </div>

          <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.missed_questions?.length">
            <h4 class="feedback-subtitle feedback-info">
              <el-icon :size="16" color="#2563EB"><InfoFilled /></el-icon>
              遗漏问题
            </h4>
            <ul class="feedback-list">
              <li v-for="(item, index) in analysisResult.hr_interview_feedback.missed_questions" :key="index">
                {{ item }}
              </li>
            </ul>
          </div>

          <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.compliance_risks?.length">
            <h4 class="feedback-subtitle" :class="hasComplianceRisk ? 'feedback-danger' : 'feedback-success'">
              <el-icon :size="16" :color="hasComplianceRisk ? '#EF4444' : '#10B981'">
                <component :is="hasComplianceRisk ? 'WarningFilled' : 'CircleCheck'" />
              </el-icon>
              合规风险
            </h4>
            <div
              v-for="(item, index) in analysisResult.hr_interview_feedback.compliance_risks"
              :key="index"
              class="compliance-item"
              :class="item.risk === '无明显不合规问题' ? 'compliance-safe' : 'compliance-danger'"
            >
              <p class="compliance-risk">{{ item.risk }}</p>
              <p class="compliance-detail">{{ item.detail }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, DocumentCopy, Delete, Document, User,
  TrendCharts, CircleCheck, Warning, WarningFilled,
  QuestionFilled, Aim, InfoFilled, Briefcase, Clock
} from '@element-plus/icons-vue'
import { analysisApi } from '../api/analysis.js'

const route = useRoute()
const router = useRouter()

const analysis = ref(null)
const analysisResult = ref(null)

const scoreCircleColor = computed(() => {
  const score = analysis.value?.match_score || 0
  if (score >= 80) return 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
  if (score >= 60) return 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
  return 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'
})

const recommendationType = computed(() => {
  const rec = analysis.value?.recommendation
  if (rec === '强烈建议进入下一轮' || rec === '建议进入下一轮') return 'success'
  if (rec === '暂缓') return 'warning'
  return 'danger'
})

const riskLevelType = computed(() => {
  const level = analysis.value?.risk_level
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  return 'danger'
})

const hasComplianceRisk = computed(() => {
  const risks = analysisResult.value?.hr_interview_feedback?.compliance_risks || []
  return risks.some(r => r.risk !== '无明显不合规问题')
})

const scoreDetailData = computed(() => {
  if (!analysisResult.value?.score_detail) return []

  const dimensionNames = {
    job_experience_match: '岗位经验匹配',
    industry_product_match: '行业/产品理解',
    communication_ability: '沟通表达能力',
    stability_motivation: '稳定性与求职动机',
    salary_arrival_match: '薪资/到岗匹配',
    risk_control: '风险控制'
  }

  return Object.entries(analysisResult.value.score_detail).map(([key, value]) => ({
    name: dimensionNames[key] || key,
    score: value.score,
    max_score: value.max_score,
    reason: value.reason
  }))
})

const getScoreColor = (ratio) => {
  if (ratio >= 0.8) return '#10B981'
  if (ratio >= 0.6) return '#F59E0B'
  return '#EF4444'
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

const getDecisionType = (decision) => {
  if (decision === '可复试') return 'success'
  if (decision === '待观察') return 'warning'
  return 'danger'
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

const copyReport = () => {
  if (!analysisResult.value) return

  const overview = analysisResult.value.candidate_overview
  const advantages = analysisResult.value.candidate_analysis?.advantages || []
  const weaknesses = analysisResult.value.candidate_analysis?.weaknesses || []
  const riskPoints = analysisResult.value.candidate_analysis?.risk_points || []
  const followUpQuestions = analysisResult.value.follow_up_questions || []
  const hrFeedback = analysisResult.value.hr_interview_feedback
  const leaderSummary = analysisResult.value.leader_summary

  let reportText = `【面试分析报告】\n\n`
  reportText += `候选人：${analysis.value.candidate_name}\n`
  reportText += `应聘岗位：${analysis.value.job_title}\n`
  reportText += `综合匹配度：${analysis.value.match_score}分\n`
  reportText += `录用建议：${analysis.value.recommendation}\n`
  reportText += `风险等级：${analysis.value.risk_level}\n`
  reportText += `AI置信度：${analysis.value.confidence}\n\n`

  reportText += `【总体结论】\n${overview?.summary || ''}\n\n`

  if (advantages.length) {
    reportText += `【候选人优势】\n`
    advantages.forEach((item, index) => {
      reportText += `${index + 1}. ${item.title}：${item.detail}\n`
      if (item.evidence) {
        reportText += `证据：${item.evidence}\n`
      }
    })
    reportText += `\n`
  }

  if (weaknesses.length) {
    reportText += `【候选人不足】\n`
    weaknesses.forEach((item, index) => {
      reportText += `${index + 1}. ${item.title}：${item.detail}\n`
      if (item.evidence) {
        reportText += `证据：${item.evidence}\n`
      }
    })
    reportText += `\n`
  }

  if (riskPoints.length) {
    reportText += `【风险点】\n`
    riskPoints.forEach((item, index) => {
      reportText += `${index + 1}. ${item.risk}（${item.level}）：${item.detail}\n`
    })
    reportText += `\n`
  }

  if (followUpQuestions.length) {
    reportText += `【建议追问】\n`
    followUpQuestions.forEach((item, index) => {
      reportText += `${index + 1}. ${item.question}\n`
      reportText += `目的：${item.purpose}\n\n`
    })
  }

  if (hrFeedback) {
    reportText += `【HR面试复盘】\n${hrFeedback.overall_comment || ''}\n\n`

    if (hrFeedback.strengths?.length) {
      reportText += `优点：\n`
      hrFeedback.strengths.forEach((item, index) => {
        reportText += `${index + 1}. ${item}\n`
      })
      reportText += `\n`
    }

    if (hrFeedback.improvements?.length) {
      reportText += `改进建议：\n`
      hrFeedback.improvements.forEach((item, index) => {
        reportText += `${index + 1}. ${item}\n`
      })
      reportText += `\n`
    }
  }

  if (leaderSummary) {
    reportText += `【给领导看的简短结论】\n${leaderSummary.short_conclusion || ''}\n`
  }

  navigator.clipboard.writeText(reportText).then(() => {
    ElMessage.success('报告已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const goBack = () => {
  router.push('/analysis/list')
}

const handleDelete = () => {
  ElMessageBox.confirm('确定要删除这条分析报告吗？删除后不可恢复。', '确认删除', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    try {
      await analysisApi.delete(analysis.value.id)
      ElMessage.success('已删除')
      router.push('/analysis/list')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const fetchAnalysis = async () => {
  try {
    const response = await analysisApi.getById(route.params.id)
    analysis.value = response.data
    if (response.data.analysis_result) {
      analysisResult.value = JSON.parse(response.data.analysis_result)
    }
  } catch (error) {
    ElMessage.error('获取分析报告失败')
  }
}

onMounted(() => {
  fetchAnalysis()
})
</script>

<style scoped>
.analysis-detail {
  max-width: 1180px;
  margin: 0 auto;
}

/* 顶部操作栏 */
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

/* 概要卡片 */
.overview-card {
  padding: 28px 32px;
  margin-bottom: 20px;
}

.overview-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.score-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}

.overview-tags {
  display: flex;
  gap: 32px;
  padding-top: 20px;
  border-top: 1px solid #F3F4F6;
}

.tag-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-label {
  font-size: 13px;
  color: #9CA3AF;
}

.result-tag {
  font-size: 14px;
  font-weight: 600;
}

/* 内容区 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  padding: 28px 32px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #EFF6FF;
}

.advantage-icon {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
}

.weakness-icon {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
}

.risk-icon {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

/* 总体结论 */
.summary-text {
  font-size: 15px;
  color: #374151;
  line-height: 1.8;
  margin-bottom: 20px;
}

.leader-card {
  background: #F8FAFC;
  border-radius: 12px;
  padding: 20px 24px;
  border-left: 4px solid #2563EB;
}

.leader-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #2563EB;
  margin-bottom: 8px;
}

.leader-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
  margin: 0 0 12px 0;
}

.leader-decision {
  display: flex;
  align-items: center;
  gap: 8px;
}

.decision-label {
  font-size: 14px;
  color: #6B7280;
}

/* 评分明细 */
.score-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.score-card {
  background: #F9FAFB;
  border-radius: 12px;
  padding: 20px;
}

.score-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.score-card-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.score-card-value {
  font-size: 20px;
  font-weight: 700;
}

.score-card-max {
  font-size: 14px;
  font-weight: 400;
  color: #9CA3AF;
}

.score-card-reason {
  font-size: 13px;
  color: #6B7280;
  line-height: 1.6;
  margin: 12px 0 0 0;
}

/* 优势/不足卡片 */
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

.weakness-card {
  background: #FFFBEB;
  border-left-color: #F59E0B;
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
  font-size: 15px;
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

/* 风险点 */
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
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.risk-detail {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0;
}

/* 追问问题 */
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
  font-size: 15px;
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

/* HR 复盘 */
.hr-feedback {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feedback-block {
  padding-bottom: 24px;
  border-bottom: 1px solid #F3F4F6;
}

.feedback-block:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.feedback-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 12px 0;
}

.feedback-success {
  color: #059669;
}

.feedback-warning {
  color: #D97706;
}

.feedback-info {
  color: #2563EB;
}

.feedback-danger {
  color: #DC2626;
}

.feedback-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
  margin: 0;
}

.feedback-list {
  margin: 0;
  padding-left: 20px;
}

.feedback-list li {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
  margin-bottom: 6px;
}

.compliance-item {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.compliance-safe {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
}

.compliance-danger {
  background: #FEF2F2;
  border: 1px solid #FECACA;
}

.compliance-risk {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.compliance-detail {
  font-size: 13px;
  color: #6B7280;
  margin: 0;
}

/* 响应式 */
@media (max-width: 1024px) {
  .score-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .overview-main {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .overview-tags {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .score-grid {
    grid-template-columns: 1fr;
  }

  .detail-header {
    flex-direction: column;
    gap: 12px;
  }

  .section-card {
    padding: 20px;
  }

  .overview-card {
    padding: 20px;
  }
}
</style>
