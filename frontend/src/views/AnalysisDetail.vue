<template>
  <div class="analysis-detail" v-loading="loading">
    <template v-if="analysis">
      <div class="detail-header">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
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

      <div class="page-card overview-card">
        <div class="overview-main">
          <div class="candidate-info">
            <p class="report-kicker">面试分析报告</p>
            <h2 class="candidate-name">{{ analysis.candidate_name }}</h2>
            <div class="candidate-meta">
              <span class="meta-item">
                <el-icon :size="14"><Briefcase /></el-icon>
                {{ analysis.job_title }}
              </span>
              <span class="meta-item">
                <el-icon :size="14"><Clock /></el-icon>
                {{ formatTime(analysis.created_at) }}
              </span>
            </div>
          </div>
          <div class="score-panel">
            <div class="score-value" :style="{ color: getScoreColor(analysis.match_score / 100) }">
              {{ analysis.match_score ?? 0 }}
            </div>
            <div class="score-label">综合匹配度</div>
          </div>
        </div>

        <p v-if="overviewSummary" class="overview-summary">{{ overviewSummary }}</p>

        <div class="overview-metrics">
          <div class="overview-metric">
            <span>录用建议</span>
            <el-tag :type="recommendationType" effect="light" size="large">
              {{ analysis.recommendation || '暂无建议' }}
            </el-tag>
          </div>
          <div class="overview-metric">
            <span>风险等级</span>
            <el-tag :type="riskLevelType" effect="light" size="large">
              {{ analysis.risk_level || '未知' }}
            </el-tag>
          </div>
          <div class="overview-metric">
            <span>AI 置信度</span>
            <el-tag type="info" effect="light" size="large">
              {{ analysis.confidence || '未知' }}
            </el-tag>
          </div>
          <div class="overview-metric">
            <span>待复核项</span>
            <strong>{{ riskPointCount + weaknessCount }}</strong>
          </div>
        </div>
      </div>

      <div v-if="navSections.length" class="section-nav">
        <button
          v-for="item in navSections"
          :key="item.id"
          type="button"
          @click="scrollToSection(item.id)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </button>
      </div>

      <div v-if="analysisResult" class="detail-layout">
        <main class="report-stack">
          <section id="conclusion" class="page-card section-card" v-if="overviewSummary || analysisResult.leader_summary">
            <div class="section-header">
              <div class="section-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div>
                <h3 class="section-title">总体结论</h3>
                <p class="section-subtitle">优先用于快速判断是否继续推进</p>
              </div>
            </div>

            <p v-if="overviewSummary" class="body-text">{{ overviewSummary }}</p>

            <div class="leader-block" v-if="analysisResult.leader_summary">
              <div class="leader-heading">
                <span>给领导看的简短结论</span>
                <el-tag :type="getDecisionType(analysisResult.leader_summary.decision)" effect="light">
                  {{ analysisResult.leader_summary.decision }}
                </el-tag>
              </div>
              <p>{{ analysisResult.leader_summary.short_conclusion }}</p>
            </div>
          </section>

          <section id="scores" class="page-card section-card" v-if="scoreDetailData.length">
            <div class="section-header">
              <div class="section-icon success-bg">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div>
                <h3 class="section-title">评分明细</h3>
                <p class="section-subtitle">按岗位匹配、沟通、稳定性等维度拆解分数</p>
              </div>
            </div>

            <div class="score-list">
              <div v-for="item in scoreDetailData" :key="item.name" class="score-row">
                <div class="score-row-main">
                  <div class="score-row-title">
                    <span>{{ item.name }}</span>
                    <strong :style="{ color: getScoreColor(item.score / item.max_score) }">
                      {{ item.score }} / {{ item.max_score }}
                    </strong>
                  </div>
                  <el-progress
                    :percentage="Math.round((item.score / item.max_score) * 100)"
                    :color="getScoreColor(item.score / item.max_score)"
                    :stroke-width="7"
                    :show-text="false"
                  />
                </div>
                <p>{{ item.reason || '暂无评分说明' }}</p>
              </div>
            </div>
          </section>

          <section id="verification" class="page-card section-card" v-if="interviewVerification.length">
            <div class="section-header">
              <div class="section-icon">
                <el-icon><Aim /></el-icon>
              </div>
              <div>
                <h3 class="section-title">面试验证</h3>
                <p class="section-subtitle">核对简历声称是否被面试回答证明</p>
              </div>
            </div>

            <div class="verification-list">
              <div v-for="(item, index) in interviewVerification" :key="index" class="verification-item">
                <div class="verification-head">
                  <strong>{{ item.claim || '未命名能力点' }}</strong>
                  <el-tag :type="getVerificationStatusType(item.status)" effect="light">
                    {{ getVerificationStatusText(item.status) }}
                  </el-tag>
                </div>
                <p><span>面试证据：</span>{{ item.interview_evidence || '信息不足' }}</p>
                <p v-if="item.score_impact"><span>评分影响：</span>{{ item.score_impact }}</p>
              </div>
            </div>
          </section>

          <section id="advantages" class="page-card section-card" v-if="advantages.length">
            <div class="section-header">
              <div class="section-icon success-bg">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div>
                <h3 class="section-title">候选人优势</h3>
                <p class="section-subtitle">可作为推进下一轮的正向依据</p>
              </div>
            </div>
            <div class="evidence-list">
              <article v-for="(item, index) in advantages" :key="index" class="evidence-item">
                <span class="item-number">{{ index + 1 }}</span>
                <div>
                  <h4>{{ item.title }}</h4>
                  <p>{{ item.detail }}</p>
                  <div v-if="item.evidence" class="evidence-note">
                    <el-icon><InfoFilled /></el-icon>
                    <span>{{ item.evidence }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section id="weaknesses" class="page-card section-card" v-if="weaknesses.length">
            <div class="section-header">
              <div class="section-icon warning-bg">
                <el-icon><Warning /></el-icon>
              </div>
              <div>
                <h3 class="section-title">候选人不足</h3>
                <p class="section-subtitle">需要在下一轮继续验证的问题</p>
              </div>
            </div>
            <div class="evidence-list">
              <article v-for="(item, index) in weaknesses" :key="index" class="evidence-item warning-item">
                <span class="item-number">{{ index + 1 }}</span>
                <div>
                  <h4>{{ item.title }}</h4>
                  <p>{{ item.detail }}</p>
                  <div v-if="item.evidence" class="evidence-note">
                    <el-icon><InfoFilled /></el-icon>
                    <span>{{ item.evidence }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section id="risks" class="page-card section-card" v-if="riskPoints.length">
            <div class="section-header">
              <div class="section-icon danger-bg">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div>
                <h3 class="section-title">风险点</h3>
                <p class="section-subtitle">建议 HR 或业务面试官重点复核</p>
              </div>
            </div>
            <div class="risk-list">
              <article
                v-for="(item, index) in riskPoints"
                :key="index"
                :class="['risk-item', `risk-${getRiskLevelClass(item.level)}`]"
              >
                <div class="risk-title">
                  <strong>{{ item.risk }}</strong>
                  <el-tag :type="getRiskType(item.level)" effect="light" size="small">
                    {{ item.level }}风险
                  </el-tag>
                </div>
                <p>{{ item.detail }}</p>
              </article>
            </div>
          </section>

          <section id="questions" class="page-card section-card" v-if="followUpQuestions.length">
            <div class="section-header">
              <div class="section-icon info-bg">
                <el-icon><QuestionFilled /></el-icon>
              </div>
              <div>
                <h3 class="section-title">建议追问问题</h3>
                <p class="section-subtitle">下一轮面试可直接复用的问题清单</p>
              </div>
            </div>
            <div class="question-list">
              <article v-for="(item, index) in followUpQuestions" :key="index" class="question-item">
                <span>{{ index + 1 }}</span>
                <div>
                  <h4>{{ item.question }}</h4>
                  <p>
                    <el-icon><Aim /></el-icon>
                    {{ item.purpose }}
                  </p>
                </div>
              </article>
            </div>
          </section>

          <section id="hr-feedback" class="page-card section-card" v-if="analysisResult.hr_interview_feedback">
            <div class="section-header">
              <div class="section-icon warning-bg">
                <el-icon><User /></el-icon>
              </div>
              <div>
                <h3 class="section-title">HR 面试复盘</h3>
                <p class="section-subtitle">用于改进面试提问和合规性</p>
              </div>
            </div>

            <div class="feedback-stack">
              <div class="feedback-block">
                <h4>总体评价</h4>
                <p>{{ analysisResult.hr_interview_feedback.overall_comment || '暂无评价' }}</p>
              </div>

              <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.strengths?.length">
                <h4 class="success-text">
                  <el-icon><CircleCheck /></el-icon>
                  做得好的地方
                </h4>
                <ul>
                  <li v-for="(item, index) in analysisResult.hr_interview_feedback.strengths" :key="index">
                    {{ item }}
                  </li>
                </ul>
              </div>

              <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.improvements?.length">
                <h4 class="warning-text">
                  <el-icon><Warning /></el-icon>
                  需要改进
                </h4>
                <ul>
                  <li v-for="(item, index) in analysisResult.hr_interview_feedback.improvements" :key="index">
                    {{ item }}
                  </li>
                </ul>
              </div>

              <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.missed_questions?.length">
                <h4 class="info-text">
                  <el-icon><InfoFilled /></el-icon>
                  遗漏问题
                </h4>
                <ul>
                  <li v-for="(item, index) in analysisResult.hr_interview_feedback.missed_questions" :key="index">
                    {{ item }}
                  </li>
                </ul>
              </div>

              <div class="feedback-block" v-if="analysisResult.hr_interview_feedback.compliance_risks?.length">
                <h4 :class="hasComplianceRisk ? 'danger-text' : 'success-text'">
                  <el-icon>
                    <component :is="hasComplianceRisk ? WarningFilled : CircleCheck" />
                  </el-icon>
                  合规风险
                </h4>
                <div
                  v-for="(item, index) in analysisResult.hr_interview_feedback.compliance_risks"
                  :key="index"
                  :class="['compliance-item', item.risk === '无明显不合规问题' ? 'compliance-safe' : 'compliance-danger']"
                >
                  <strong>{{ item.risk }}</strong>
                  <p>{{ item.detail }}</p>
                </div>
              </div>
            </div>
          </section>
        </main>

        <aside class="side-panel">
          <div class="page-card side-card">
            <h3>快速复核</h3>
            <div class="side-metric">
              <span>优势</span>
              <strong>{{ advantageCount }}</strong>
            </div>
            <div class="side-metric">
              <span>不足</span>
              <strong>{{ weaknessCount }}</strong>
            </div>
            <div class="side-metric">
              <span>风险点</span>
              <strong>{{ riskPointCount }}</strong>
            </div>
            <div class="side-metric">
              <span>追问问题</span>
              <strong>{{ followUpCount }}</strong>
            </div>
          </div>
        </aside>
      </div>

      <div v-else class="page-card empty-detail">
        <el-icon :size="44" color="#D1D5DB"><Document /></el-icon>
        <p>报告结构解析失败</p>
        <span>可以复制报告或返回列表重新打开。</span>
      </div>
    </template>

    <div v-else-if="!loading" class="page-card empty-detail">
      <el-icon :size="44" color="#D1D5DB"><Document /></el-icon>
      <p>未找到分析报告</p>
      <span>这条报告可能已经被删除。</span>
      <el-button type="primary" @click="goBack">返回列表</el-button>
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

const loading = ref(false)
const analysis = ref(null)
const analysisResult = ref(null)

const overviewSummary = computed(() => {
  return analysisResult.value?.candidate_overview?.summary || ''
})

const advantages = computed(() => analysisResult.value?.candidate_analysis?.advantages || [])
const weaknesses = computed(() => analysisResult.value?.candidate_analysis?.weaknesses || [])
const riskPoints = computed(() => analysisResult.value?.candidate_analysis?.risk_points || [])
const followUpQuestions = computed(() => analysisResult.value?.follow_up_questions || [])
const interviewVerification = computed(() => {
  const items = analysisResult.value?.interview_verification
  return Array.isArray(items) ? items : []
})
const isVerificationScoring = computed(() => analysisResult.value?.scoring_model?.version === 'interview_verification_v1')

const advantageCount = computed(() => advantages.value.length)
const weaknessCount = computed(() => weaknesses.value.length)
const riskPointCount = computed(() => riskPoints.value.length)
const followUpCount = computed(() => followUpQuestions.value.length)

const recommendationType = computed(() => {
  const rec = analysis.value?.recommendation
  if (rec === '强烈建议进入下一轮' || rec === '建议进入下一轮') return 'success'
  if (rec === '暂缓') return 'warning'
  if (!rec) return 'info'
  return 'danger'
})

const riskLevelType = computed(() => {
  const level = analysis.value?.risk_level
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  if (!level) return 'info'
  return 'danger'
})

const hasComplianceRisk = computed(() => {
  const risks = analysisResult.value?.hr_interview_feedback?.compliance_risks || []
  return risks.some(r => r.risk !== '无明显不合规问题')
})

const scoreDetailData = computed(() => {
  if (!analysisResult.value?.score_detail) return []

  const dimensionNames = {
    job_experience_match: isVerificationScoring.value ? '岗位核心能力验证' : '岗位经验匹配',
    industry_product_match: isVerificationScoring.value ? '简历真实性/经历一致性' : '行业/产品理解',
    communication_ability: isVerificationScoring.value ? '问题解决与案例深度' : '沟通表达能力',
    stability_motivation: isVerificationScoring.value ? '沟通表达与稳定性' : '稳定性与求职动机',
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

const navSections = computed(() => {
  const sections = []
  if (overviewSummary.value || analysisResult.value?.leader_summary) {
    sections.push({ id: 'conclusion', label: '结论', icon: Document })
  }
  if (scoreDetailData.value.length) sections.push({ id: 'scores', label: '评分', icon: TrendCharts })
  if (interviewVerification.value.length) sections.push({ id: 'verification', label: '验证', icon: Aim })
  if (advantages.value.length) sections.push({ id: 'advantages', label: '优势', icon: CircleCheck })
  if (weaknesses.value.length) sections.push({ id: 'weaknesses', label: '不足', icon: Warning })
  if (riskPoints.value.length) sections.push({ id: 'risks', label: '风险', icon: WarningFilled })
  if (followUpQuestions.value.length) sections.push({ id: 'questions', label: '追问', icon: QuestionFilled })
  if (analysisResult.value?.hr_interview_feedback) sections.push({ id: 'hr-feedback', label: 'HR复盘', icon: User })
  return sections
})

const getScoreColor = (ratio) => {
  const value = Number(ratio) || 0
  if (value >= 0.8) return '#10B981'
  if (value >= 0.6) return '#F59E0B'
  return '#EF4444'
}

const getRiskType = (level) => {
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  if (!level) return 'info'
  return 'danger'
}

const getVerificationStatusText = (status) => {
  const map = {
    VERIFIED: '已验证',
    PARTIAL: '部分验证',
    MISSING: '缺少证据',
    CONTRADICTED: '存在矛盾',
    UNVERIFIED: '未验证'
  }
  return map[status] || '未验证'
}

const getVerificationStatusType = (status) => {
  if (status === 'VERIFIED') return 'success'
  if (status === 'PARTIAL' || status === 'UNVERIFIED') return 'warning'
  if (status === 'MISSING' || status === 'CONTRADICTED') return 'danger'
  return 'info'
}

const getRiskLevelClass = (level) => {
  if (level === '高') return 'high'
  if (level === '中') return 'medium'
  return 'low'
}

const getDecisionType = (decision) => {
  if (decision === '可复试') return 'success'
  if (decision === '待观察') return 'warning'
  if (!decision) return 'info'
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

const scrollToSection = (id) => {
  const target = document.getElementById(id)
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const copyReport = () => {
  if (!analysisResult.value) return

  const overview = analysisResult.value.candidate_overview
  const leaderSummary = analysisResult.value.leader_summary
  const hrFeedback = analysisResult.value.hr_interview_feedback

  let reportText = `【面试分析报告】\n\n`
  reportText += `候选人：${analysis.value.candidate_name}\n`
  reportText += `应聘岗位：${analysis.value.job_title}\n`
  reportText += `综合匹配度：${analysis.value.match_score}分\n`
  reportText += `录用建议：${analysis.value.recommendation}\n`
  reportText += `风险等级：${analysis.value.risk_level}\n`
  reportText += `AI置信度：${analysis.value.confidence}\n\n`

  reportText += `【总体结论】\n${overview?.summary || ''}\n\n`

  if (advantages.value.length) {
    reportText += `【候选人优势】\n`
    advantages.value.forEach((item, index) => {
      reportText += `${index + 1}. ${item.title}：${item.detail}\n`
      if (item.evidence) reportText += `证据：${item.evidence}\n`
    })
    reportText += `\n`
  }

  if (weaknesses.value.length) {
    reportText += `【候选人不足】\n`
    weaknesses.value.forEach((item, index) => {
      reportText += `${index + 1}. ${item.title}：${item.detail}\n`
      if (item.evidence) reportText += `证据：${item.evidence}\n`
    })
    reportText += `\n`
  }

  if (riskPoints.value.length) {
    reportText += `【风险点】\n`
    riskPoints.value.forEach((item, index) => {
      reportText += `${index + 1}. ${item.risk}（${item.level}）：${item.detail}\n`
    })
    reportText += `\n`
  }

  if (followUpQuestions.value.length) {
    reportText += `【建议追问】\n`
    followUpQuestions.value.forEach((item, index) => {
      reportText += `${index + 1}. ${item.question}\n`
      reportText += `目的：${item.purpose}\n\n`
    })
  }

  if (hrFeedback) {
    reportText += `【HR面试复盘】\n${hrFeedback.overall_comment || ''}\n\n`
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
  loading.value = true
  try {
    const response = await analysisApi.getById(route.params.id)
    analysis.value = response.data
    if (response.data.analysis_result) {
      try {
        analysisResult.value = JSON.parse(response.data.analysis_result)
      } catch (error) {
        analysisResult.value = null
        ElMessage.warning('报告结构解析失败')
      }
    }
  } catch (error) {
    ElMessage.error('获取分析报告失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAnalysis()
})
</script>

<style scoped>
.analysis-detail {
  max-width: 1440px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-card {
  padding: 24px;
  margin-bottom: 16px;
}

.overview-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.report-kicker {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 700;
  margin: 0 0 6px;
}

.candidate-name {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 10px;
  letter-spacing: 0;
}

.candidate-meta {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.score-panel {
  min-width: 118px;
  padding: 14px 18px;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  text-align: center;
}

.score-value {
  font-size: 38px;
  line-height: 1;
  font-weight: 800;
}

.score-label {
  margin-top: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.overview-summary {
  margin: 18px 0 0;
  padding: 14px 16px;
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-soft);
  border-radius: var(--radius-card);
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text);
}

.overview-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin-top: 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.overview-metric {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  background: var(--color-surface-soft);
  border-right: 1px solid var(--color-border);
}

.overview-metric:last-child {
  border-right: 0;
}

.overview-metric span {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 700;
}

.overview-metric strong {
  font-size: 22px;
  color: var(--color-text);
}

.section-nav {
  position: sticky;
  top: 16px;
  z-index: 5;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--shadow-card);
}

.section-nav button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.section-nav button:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 20px;
  align-items: start;
}

.report-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.section-card {
  padding: 24px;
  scroll-margin-top: 86px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-card);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-blue);
  background: #e8f1ff;
  flex-shrink: 0;
}

.success-bg { color: var(--color-primary); background: var(--color-primary-soft); }
.warning-bg { color: var(--color-amber); background: #fff7db; }
.danger-bg { color: var(--color-red); background: #feecec; }
.info-bg { color: var(--color-blue); background: #e8f1ff; }

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 4px;
}

.section-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.body-text,
.leader-block p,
.score-row p,
.evidence-item p,
.risk-item p,
.question-item p,
.feedback-block p,
.feedback-block li,
.compliance-item p {
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.body-text {
  margin: 0;
}

.leader-block {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-blue);
  border-radius: var(--radius-card);
  background: var(--color-surface-soft);
}

.leader-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.leader-heading span {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-row {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 18px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);
}

.score-row:last-child {
  border-bottom: 0;
}

.score-row-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
}

.score-row p {
  margin: 0;
}

.evidence-list,
.verification-list,
.risk-list,
.question-list,
.feedback-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evidence-item,
.question-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface-soft);
}

.warning-item {
  border-left: 3px solid var(--color-amber);
}

.item-number,
.question-item > span {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 800;
}

.evidence-item h4,
.question-item h4 {
  margin: 2px 0 6px;
  font-size: 15px;
  color: var(--color-text);
}

.evidence-item p,
.question-item p {
  margin: 0;
}

.evidence-note {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.verification-item {
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface-soft);
}

.verification-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.verification-head strong {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.4;
}

.verification-item p {
  margin: 6px 0 0;
}

.verification-item p span {
  color: var(--color-text);
  font-weight: var(--font-semibold);
}

.risk-item {
  padding: 14px 16px;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.risk-high { border-left: 3px solid var(--color-red); }
.risk-medium { border-left: 3px solid var(--color-amber); }
.risk-low { border-left: 3px solid var(--color-primary); }

.risk-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.risk-title strong {
  color: var(--color-text);
  font-size: 15px;
}

.question-item p {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 6px;
}

.feedback-block {
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
}

.feedback-block:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.feedback-block h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  color: var(--color-text);
  font-size: 15px;
}

.feedback-block ul {
  margin: 0;
  padding-left: 20px;
}

.success-text { color: var(--color-primary) !important; }
.warning-text { color: var(--color-amber) !important; }
.info-text { color: var(--color-blue) !important; }
.danger-text { color: var(--color-red) !important; }

.compliance-item {
  padding: 12px 14px;
  border-radius: var(--radius-card);
  margin-bottom: 8px;
}

.compliance-safe {
  background: var(--color-primary-soft);
  border: 1px solid #bfe4df;
}

.compliance-danger {
  background: #feecec;
  border: 1px solid #fecaca;
}

.compliance-item strong {
  color: var(--color-text);
  font-size: 14px;
}

.side-panel {
  position: sticky;
  top: 84px;
}

.side-card {
  padding: 18px;
}

.side-card h3 {
  font-size: 16px;
  color: var(--color-text);
  margin: 0 0 14px;
}

.side-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}

.side-metric:last-child {
  border-bottom: 0;
}

.side-metric span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.side-metric strong {
  color: var(--color-text);
  font-size: 18px;
}

.empty-detail {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: var(--color-text-muted);
}

.empty-detail p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 16px;
  font-weight: 700;
}

.empty-detail span {
  font-size: 14px;
}

@media (max-width: 1180px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .detail-header,
  .overview-main {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .el-button,
  .detail-header > .el-button {
    flex: 1;
  }

  .overview-card,
  .section-card {
    padding: 20px;
  }

  .overview-metrics {
    grid-template-columns: 1fr 1fr;
  }

  .overview-metric:nth-child(2) {
    border-right: 0;
  }

  .overview-metric:nth-child(-n + 2) {
    border-bottom: 1px solid var(--color-border);
  }

  .score-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .section-nav {
    top: 8px;
  }
}
</style>
