<template>
  <div class="report-section" v-if="report">
    <!-- 摘要 -->
    <div class="report-text" v-if="report.summary">
      <p>{{ report.summary }}</p>
    </div>

    <!-- 匹配优势 -->
    <div class="report-group" v-if="report.strengths?.length">
      <h4 class="group-title">匹配优势</h4>
      <div v-for="(item, i) in report.strengths" :key="i" class="report-card card-green">
        <div class="card-header">
          <span class="card-num">{{ i + 1 }}</span>
          <span class="card-title">{{ item.title }}</span>
        </div>
        <p class="card-detail">{{ item.detail }}</p>
        <div class="card-evidence" v-if="item.evidence">
          <el-icon :size="14" color="#10B981"><InfoFilled /></el-icon>
          <span>{{ item.evidence }}</span>
        </div>
      </div>
    </div>

    <!-- 不匹配点 -->
    <div class="report-group" v-if="report.mismatches?.length">
      <h4 class="group-title">不匹配点</h4>
      <div v-for="(item, i) in report.mismatches" :key="i" class="report-card card-orange">
        <div class="card-header">
          <span class="card-num">{{ i + 1 }}</span>
          <span class="card-title">{{ item.title }}</span>
        </div>
        <p class="card-detail">{{ item.detail }}</p>
      </div>
    </div>

    <!-- 风险点 -->
    <div class="report-group" v-if="report.risk_points?.length">
      <h4 class="group-title">风险点</h4>
      <div v-for="(item, i) in report.risk_points" :key="i" class="risk-card" :class="getRiskClass(item.level)">
        <div class="risk-header">
          <div class="risk-title">
            <el-icon :size="16"><Warning /></el-icon>
            <span>{{ item.risk }}</span>
          </div>
          <el-tag :type="getRiskTag(item.level)" effect="light" size="small">{{ item.level }}风险</el-tag>
        </div>
        <p class="card-detail">{{ item.detail }}</p>
      </div>
    </div>

    <!-- 建议追问 -->
    <div class="report-group" v-if="report.follow_up_questions?.length">
      <h4 class="group-title">建议追问问题</h4>
      <div v-for="(item, i) in report.follow_up_questions" :key="i" class="follow-up-card">
        <div class="fu-num">{{ i + 1 }}</div>
        <div class="fu-content">
          <p class="fu-question">{{ item.question }}</p>
          <p class="fu-purpose" v-if="item.purpose"><el-icon :size="14" color="#8B5CF6"><Aim /></el-icon>{{ item.purpose }}</p>
        </div>
      </div>
    </div>

    <!-- 详细评分 -->
    <div class="report-group" v-if="report.score_detail || report.dimensions">
      <h4 class="group-title">评分明细</h4>
      <div class="score-grid">
        <div v-for="(dim, key) in (report.score_detail || report.dimensions)" :key="key" class="score-row-item">
          <span class="dim-label">{{ dim.label || key }}</span>
          <el-progress
            :percentage="Math.round((dim.score / dim.max_score) * 100)"
            :color="getScoreColor(dim.score, dim.max_score)"
            :stroke-width="8"
            :show-text="false"
            style="flex:1; max-width: 120px;"
          />
          <span class="dim-score" :style="{ color: getScoreColor(dim.score, dim.max_score) }">{{ dim.score }}/{{ dim.max_score }}</span>
        </div>
      </div>
    </div>

    <!-- 优势不足（初试/复试格式兼容） -->
    <div class="report-group" v-if="report.advantages?.length">
      <h4 class="group-title">优势</h4>
      <div v-for="(item, i) in report.advantages" :key="i" class="report-card card-green">
        <div class="card-header"><span class="card-num">{{ i + 1 }}</span><span class="card-title">{{ item.title }}</span></div>
        <p class="card-detail">{{ item.detail }}</p>
      </div>
    </div>
    <div class="report-group" v-if="report.weaknesses?.length">
      <h4 class="group-title">不足</h4>
      <div v-for="(item, i) in report.weaknesses" :key="i" class="report-card card-orange">
        <div class="card-header"><span class="card-num">{{ i + 1 }}</span><span class="card-title">{{ item.title }}</span></div>
        <p class="card-detail">{{ item.detail }}</p>
      </div>
    </div>

    <!-- HR 反馈 -->
    <div class="report-group" v-if="report.hr_interview_feedback">
      <h4 class="group-title">面试反馈</h4>
      <p class="card-detail">{{ report.hr_interview_feedback.overall_comment }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled, Warning, Aim } from '@element-plus/icons-vue'

const props = defineProps({
  reportJson: { type: String, default: '' }
})

const report = computed(() => {
  if (!props.reportJson) return null
  try { return JSON.parse(props.reportJson) } catch { return null }
})

const getScoreColor = (score, max) => {
  const pct = score / max * 100
  if (pct >= 80) return '#10B981'
  if (pct >= 60) return '#F59E0B'
  return '#EF4444'
}

const getRiskClass = (level) => {
  if (level === '高') return 'risk-high'
  if (level === '中') return 'risk-medium'
  return 'risk-low'
}

const getRiskTag = (level) => {
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  return 'danger'
}
</script>

<style scoped>
.report-section { font-size: 14px; }
.report-text { color: var(--color-text-secondary); line-height: 1.8; margin-bottom: 20px; padding: 14px 16px; background: var(--color-surface-soft); border: 1px solid var(--color-border); border-radius: var(--radius-card); }
.report-group { margin-bottom: 20px; }
.group-title { font-size: 15px; font-weight: 700; color: var(--color-text); margin: 0 0 10px 0; }

.report-card { padding: 14px 16px; border-radius: var(--radius-card); border: 1px solid; border-left-width: 4px; margin-bottom: 10px; }
.card-green { background: #f2fbf8; border-color: #bbebdd; border-left-color: var(--color-primary); }
.card-orange { background: #fff8ed; border-color: #fed7aa; border-left-color: #ea580c; }

.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.card-num { width: 22px; height: 22px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: var(--color-text-secondary); flex-shrink: 0; border: 1px solid var(--color-border); }
.card-title { font-size: 14px; font-weight: 700; color: var(--color-text); }
.card-detail { font-size: 13px; color: var(--color-text-secondary); line-height: 1.65; margin: 0; }
.card-evidence { display: flex; align-items: flex-start; gap: 4px; font-size: 12px; color: var(--color-text-secondary); margin-top: 8px; }

.risk-card { padding: 14px 16px; border-radius: var(--radius-card); border: 1px solid; margin-bottom: 10px; }
.risk-high { background: #fff1f1; border-color: #fecaca; }
.risk-medium { background: #fff8e6; border-color: #fde68a; }
.risk-low { background: #f2fbf8; border-color: #bbebdd; }
.risk-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.risk-title { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700; color: var(--color-text); }

.follow-up-card { display: flex; gap: 12px; padding: 14px 16px; background: #f7f5ff; border-radius: var(--radius-card); border: 1px solid #ddd6fe; margin-bottom: 8px; }
.fu-num { width: 26px; height: 26px; border-radius: 50%; background: #7c3aed; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.fu-content { flex: 1; }
.fu-question { font-size: 14px; font-weight: 600; color: var(--color-text); margin: 0 0 4px 0; }
.fu-purpose { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #8B5CF6; margin: 0; }

.score-grid { display: flex; flex-direction: column; gap: 10px; }
.score-row-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--color-surface-soft); border: 1px solid var(--color-border); border-radius: var(--radius-card); }
.dim-label { font-size: 13px; color: var(--color-text-secondary); width: 100px; flex-shrink: 0; font-weight: 600; }
.dim-score { font-size: 13px; font-weight: 600; white-space: nowrap; }
</style>
