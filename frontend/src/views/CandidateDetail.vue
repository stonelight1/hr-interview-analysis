<template>
  <div class="candidate-detail" v-if="candidate">
    <!-- 顶部导航 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <div class="header-actions">
        <el-button
          v-if="candidate.current_status === 'RESUME_PENDING'"
          type="primary" plain
          :loading="screeningLoading"
          @click="triggerResumeScreening"
        >
          <el-icon><Search /></el-icon>
          {{ screeningLoading ? '筛选中...' : '生成简历筛选' }}
        </el-button>
      </div>
    </div>

    <!-- 候选人概览 -->
    <div class="page-card overview-card">
      <div class="overview-main">
        <div class="candidate-info">
          <div class="info-row-top">
            <h2 class="candidate-name">{{ candidate.candidate_name }}</h2>
            <el-tag :type="getStatusType(candidate.current_status)" effect="light" size="large">
              {{ getStatusLabel(candidate.current_status) }}
            </el-tag>
          </div>
          <div class="candidate-meta">
            <span class="meta-item"><el-icon :size="14"><OfficeBuilding /></el-icon>{{ candidate.job_name || '岗位 #' + candidate.job_id }}</span>
            <span class="meta-item" v-if="candidate.job_type"><el-tag size="small" effect="plain" round>{{ candidate.job_type }}</el-tag></span>
            <span class="meta-item" v-if="candidate.phone"><el-icon :size="14"><Phone /></el-icon>{{ candidate.phone }}</span>
            <span class="meta-item" v-if="candidate.email"><el-icon :size="14"><Message /></el-icon>{{ candidate.email }}</span>
            <span class="meta-item" v-if="candidate.source"><el-icon :size="14"><Connection /></el-icon>{{ candidate.source }}</span>
          </div>
        </div>
      </div>

      <!-- 分数概览 -->
      <div class="scores-row">
        <div class="score-item">
          <div class="score-circle-sm" :style="{ background: getScoreCircleColor(candidate.resume_match_score) }">
            {{ candidate.resume_match_score || '—' }}
          </div>
          <div class="score-label">简历匹配度</div>
        </div>
        <div class="score-item">
          <div class="score-circle-sm" :style="{ background: getScoreCircleColor(candidate.first_interview_score) }">
            {{ candidate.first_interview_score || '—' }}
          </div>
          <div class="score-label">初试评分</div>
        </div>
        <div class="score-item">
          <div class="score-circle-sm" :style="{ background: getScoreCircleColor(candidate.second_interview_score) }">
            {{ candidate.second_interview_score || '—' }}
          </div>
          <div class="score-label">复试评分</div>
        </div>
        <div class="score-item">
          <div class="score-label score-label-top">AI 建议</div>
          <el-tag v-if="candidate.latest_ai_suggestion" :type="getSuggestionType(candidate.latest_ai_suggestion)" effect="light">
            {{ candidate.latest_ai_suggestion }}
          </el-tag>
          <span v-else class="text-muted">—</span>
        </div>
        <div class="score-item">
          <div class="score-label score-label-top">风险等级</div>
          <el-tag v-if="candidate.latest_ai_suggestion === '不建议'" type="danger" effect="light">高</el-tag>
          <el-tag v-else-if="candidate.latest_ai_suggestion === '暂缓'" type="warning" effect="light">中</el-tag>
          <el-tag v-else-if="candidate.latest_ai_suggestion" type="success" effect="light">低</el-tag>
          <span v-else class="text-muted">—</span>
        </div>
      </div>
    </div>

    <!-- 招聘流程进度条 -->
    <div class="page-card progress-card">
      <div class="progress-steps">
        <div v-for="(step, idx) in progressSteps" :key="idx" class="progress-step" :class="step.status">
          <div class="step-dot">
            <el-icon v-if="step.status === 'done'"><Check /></el-icon>
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <div class="step-label">{{ step.label }}</div>
          <div class="step-bar" v-if="idx < progressSteps.length - 1" />
        </div>
      </div>
    </div>

    <!-- Tab 内容 -->
    <div class="page-card tab-card">
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- Tab1: 基础信息 -->
        <el-tab-pane label="基础信息" name="info">
          <div class="tab-content">
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="姓名">{{ candidate.candidate_name }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ candidate.gender || '—' }}</el-descriptions-item>
              <el-descriptions-item label="年龄">{{ candidate.age || '—' }}</el-descriptions-item>
              <el-descriptions-item label="手机号">{{ candidate.phone || '—' }}</el-descriptions-item>
              <el-descriptions-item label="邮箱">{{ candidate.email || '—' }}</el-descriptions-item>
              <el-descriptions-item label="当前城市">{{ candidate.current_city || '—' }}</el-descriptions-item>
              <el-descriptions-item label="最高学历">{{ candidate.education_level || '—' }}</el-descriptions-item>
              <el-descriptions-item label="毕业学校">{{ candidate.graduation_school || '—' }}</el-descriptions-item>
              <el-descriptions-item label="专业">{{ candidate.major || '—' }}</el-descriptions-item>
              <el-descriptions-item label="工作年限">{{ candidate.work_years != null ? candidate.work_years + '年' : '—' }}</el-descriptions-item>
              <el-descriptions-item label="期望薪资">{{ candidate.expected_salary || '—' }}</el-descriptions-item>
              <el-descriptions-item label="求职状态">{{ candidate.job_search_status || '—' }}</el-descriptions-item>
              <el-descriptions-item label="应聘岗位">{{ candidate.job_name || '岗位 #' + candidate.job_id }}</el-descriptions-item>
              <el-descriptions-item label="岗位类型">{{ candidate.job_type || '—' }}</el-descriptions-item>
              <el-descriptions-item label="候选人来源">{{ candidate.source || '—' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- Tab2: 原始简历 -->
        <el-tab-pane label="原始简历" name="resume">
          <div class="tab-content">
            <div class="resume-text">{{ candidate.resume_text }}</div>
          </div>
        </el-tab-pane>

        <!-- Tab3: 简历筛选报告 -->
        <el-tab-pane label="简历筛选报告" name="screening">
          <div class="tab-content" v-if="resumeScreeningReport">
            <div class="report-header">
              <div class="report-score-big" :style="{ color: getScoreColor(resumeScreeningReport.score) }">
                {{ resumeScreeningReport.score }}
                <span class="score-unit">分</span>
              </div>
              <div class="report-meta">
                <div><span class="meta-lbl">AI 建议：</span><el-tag :type="getSuggestionType(resumeScreeningReport.suggestion)" effect="light">{{ resumeScreeningReport.suggestion }}</el-tag></div>
                <div v-if="resumeScreeningReport.risk_level"><span class="meta-lbl">风险等级：</span><el-tag :type="getRiskType(resumeScreeningReport.risk_level)" effect="light">{{ resumeScreeningReport.risk_level }}</el-tag></div>
                <div><span class="meta-lbl">生成时间：</span>{{ formatTime(resumeScreeningReport.created_at) }}</div>
              </div>
            </div>
            <ReportSection :reportJson="resumeScreeningReport.report_json" />
          </div>
          <div class="tab-empty" v-else>
            <p>暂无简历筛选报告</p>
            <el-button v-if="candidate.current_status === 'RESUME_PENDING'" type="primary" plain @click="triggerResumeScreening">
              开始简历筛选
            </el-button>
          </div>
        </el-tab-pane>

        <!-- Tab4: 初试记录与评估 -->
        <el-tab-pane label="初试记录与评估" name="firstInterview">
          <div class="tab-content">
            <div class="subsection">
              <h4 class="sub-title">初试记录</h4>
              <div v-if="firstInterviewRecord" class="interview-display">
                <div class="interview-meta" v-if="firstInterviewRecord.interviewer_name || firstInterviewRecord.interview_time">
                  <span v-if="firstInterviewRecord.interviewer_name">面试官：{{ firstInterviewRecord.interviewer_name }}</span>
                  <span v-if="firstInterviewRecord.interview_time">时间：{{ formatTime(firstInterviewRecord.interview_time) }}</span>
                </div>
                <div class="interview-text">{{ firstInterviewRecord.record_text }}</div>
              </div>
              <div v-else class="tab-empty">
                <p>暂无初试记录</p>
                <el-button type="primary" plain @click="showFirstInterviewDialog = true">
                  <el-icon><Plus /></el-icon>
                  添加初试记录
                </el-button>
              </div>
            </div>

            <el-divider />

            <div class="subsection">
              <h4 class="sub-title">初试评估报告</h4>
              <div v-if="firstInterviewReport" class="report-section-compact">
                <div class="report-header">
                  <div class="report-score-big" :style="{ color: getScoreColor(firstInterviewReport.score) }">
                    {{ firstInterviewReport.score }}<span class="score-unit">分</span>
                  </div>
                  <div class="report-meta">
                    <div><span class="meta-lbl">AI 建议：</span><el-tag :type="getSuggestionType(firstInterviewReport.suggestion)" effect="light">{{ firstInterviewReport.suggestion }}</el-tag></div>
                    <div>生成时间：{{ formatTime(firstInterviewReport.created_at) }}</div>
                  </div>
                </div>
                <ReportSection :reportJson="firstInterviewReport.report_json" />
              </div>
              <div v-else class="tab-empty">
                <p>暂无初试评估报告</p>
                <el-button v-if="firstInterviewRecord" type="primary" plain :loading="firstAnalysisLoading" @click="triggerFirstAnalysis">
                  {{ firstAnalysisLoading ? '分析中...' : '生成初试评估' }}
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab5: 复试记录与评估 -->
        <el-tab-pane label="复试记录与评估" name="secondInterview">
          <div class="tab-content">
            <div class="subsection">
              <h4 class="sub-title">复试记录</h4>
              <div v-if="secondInterviewRecord" class="interview-display">
                <div class="interview-meta" v-if="secondInterviewRecord.interviewer_name || secondInterviewRecord.interview_time">
                  <span v-if="secondInterviewRecord.interviewer_name">面试官：{{ secondInterviewRecord.interviewer_name }}</span>
                  <span v-if="secondInterviewRecord.interview_time">时间：{{ formatTime(secondInterviewRecord.interview_time) }}</span>
                </div>
                <div class="interview-text">{{ secondInterviewRecord.record_text }}</div>
              </div>
              <div v-else class="tab-empty">
                <p>暂无复试记录</p>
                <el-button type="primary" plain @click="showSecondInterviewDialog = true">
                  <el-icon><Plus /></el-icon>
                  添加复试记录
                </el-button>
              </div>
            </div>

            <el-divider />

            <div class="subsection">
              <h4 class="sub-title">复试评估报告</h4>
              <div v-if="secondInterviewReport" class="report-section-compact">
                <div class="report-header">
                  <div class="report-score-big" :style="{ color: getScoreColor(secondInterviewReport.score) }">
                    {{ secondInterviewReport.score }}<span class="score-unit">分</span>
                  </div>
                  <div class="report-meta">
                    <div><span class="meta-lbl">AI 建议：</span><el-tag :type="getSuggestionType(secondInterviewReport.suggestion)" effect="light">{{ secondInterviewReport.suggestion }}</el-tag></div>
                    <div>生成时间：{{ formatTime(secondInterviewReport.created_at) }}</div>
                  </div>
                </div>
                <ReportSection :reportJson="secondInterviewReport.report_json" />
              </div>
              <div v-else class="tab-empty">
                <p>暂无复试评估报告</p>
                <el-button v-if="secondInterviewRecord" type="primary" plain :loading="secondAnalysisLoading" @click="triggerSecondAnalysis">
                  {{ secondAnalysisLoading ? '分析中...' : '生成复试评估' }}
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab6: 最终建议 -->
        <el-tab-pane label="最终建议" name="final">
          <div class="tab-content">
            <div class="final-summary">
              <el-alert
                v-if="candidate.latest_ai_suggestion"
                :title="'当前建议：' + candidate.latest_ai_suggestion"
                :type="getSuggestionType(candidate.latest_ai_suggestion) === 'success' ? 'success' : (getSuggestionType(candidate.latest_ai_suggestion) === 'warning' ? 'warning' : 'info')"
                show-icon
              />
              <div class="final-scores">
                <div class="final-score-item">
                  <span class="final-label">简历匹配度</span>
                  <span class="final-value" :style="{ color: getScoreColor(candidate.resume_match_score) }">{{ candidate.resume_match_score || '—' }}</span>
                </div>
                <div class="final-score-item">
                  <span class="final-label">初试评分</span>
                  <span class="final-value" :style="{ color: getScoreColor(candidate.first_interview_score) }">{{ candidate.first_interview_score || '—' }}</span>
                </div>
                <div class="final-score-item">
                  <span class="final-label">复试评分</span>
                  <span class="final-value" :style="{ color: getScoreColor(candidate.second_interview_score) }">{{ candidate.second_interview_score || '—' }}</span>
                </div>
              </div>
              <p class="final-note">综合评价基于简历筛选、初试评估和复试评估的结果综合得出。</p>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加初试记录对话框 -->
    <el-dialog v-model="showFirstInterviewDialog" title="添加初试记录" width="600px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="面试官">
          <el-input v-model="firstInterviewForm.interviewer_name" placeholder="面试官姓名" />
        </el-form-item>
        <el-form-item label="面试时间">
          <el-date-picker v-model="firstInterviewForm.interview_time" type="datetime" placeholder="选择面试时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="面试记录">
          <el-input v-model="firstInterviewForm.record_text" type="textarea" :rows="8" placeholder="请粘贴面试记录文本..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFirstInterviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingFirstRecord" @click="saveFirstInterviewRecord">
          {{ savingFirstRecord ? '保存中...' : '保存并生成评估' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加复试记录对话框 -->
    <el-dialog v-model="showSecondInterviewDialog" title="添加复试记录" width="600px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="面试官">
          <el-input v-model="secondInterviewForm.interviewer_name" placeholder="面试官姓名" />
        </el-form-item>
        <el-form-item label="面试时间">
          <el-date-picker v-model="secondInterviewForm.interview_time" type="datetime" placeholder="选择面试时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="面试记录">
          <el-input v-model="secondInterviewForm.record_text" type="textarea" :rows="8" placeholder="请粘贴复试记录文本..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSecondInterviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSecondRecord" @click="saveSecondInterviewRecord">
          {{ savingSecondRecord ? '保存中...' : '保存并生成评估' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search, User, Phone, Message, Connection, InfoFilled, Warning, Aim, ChatLineRound, Plus, Check, OfficeBuilding } from '@element-plus/icons-vue'
import { candidatesApi, screeningApi, firstInterviewRecordApi, firstInterviewAnalysisApi, secondInterviewRecordApi, secondInterviewAnalysisApi } from '../api/analysis.js'

import ReportSection from '../components/ReportSection.vue'

const route = useRoute()
const router = useRouter()

const candidate = ref(null)
const resumeScreeningReport = ref(null)
const firstInterviewRecord = ref(null)
const firstInterviewReport = ref(null)
const secondInterviewRecord = ref(null)
const secondInterviewReport = ref(null)
const screeningLoading = ref(false)
const firstAnalysisLoading = ref(false)
const secondAnalysisLoading = ref(false)
const savingFirstRecord = ref(false)
const savingSecondRecord = ref(false)
const activeTab = ref('info')
const showFirstInterviewDialog = ref(false)
const showSecondInterviewDialog = ref(false)

const firstInterviewForm = reactive({ interviewer_name: '', interview_time: null, record_text: '' })
const secondInterviewForm = reactive({ interviewer_name: '', interview_time: null, record_text: '' })

const progressSteps = computed(() => {
  const status = candidate.value?.current_status || ''
  const stages = [
    { key: 'parsed', label: '简历解析', done: status !== 'IMPORTED' },
    { key: 'screened', label: '简历筛选', done: ['RESUME_PASSED','RESUME_REJECTED','FIRST_INTERVIEW_PENDING','FIRST_INTERVIEW_PASSED','FIRST_INTERVIEW_REJECTED','SECOND_INTERVIEW_PENDING','SECOND_INTERVIEW_PASSED','SECOND_INTERVIEW_REJECTED','HIRED','ABANDONED','TALENT_POOL'].includes(status) },
    { key: 'first', label: '初试', done: ['FIRST_INTERVIEW_PASSED','FIRST_INTERVIEW_REJECTED','SECOND_INTERVIEW_PENDING','SECOND_INTERVIEW_PASSED','SECOND_INTERVIEW_REJECTED','HIRED','ABANDONED'].includes(status) },
    { key: 'second', label: '复试', done: ['SECOND_INTERVIEW_PASSED','SECOND_INTERVIEW_REJECTED','HIRED'].includes(status) },
    { key: 'final', label: '最终结论', done: ['HIRED','ABANDONED'].includes(status) },
  ]
  let activeFound = false
  return stages.map(s => {
    if (!s.done && !activeFound) { activeFound = true; return { ...s, status: 'active' } }
    if (s.done) return { ...s, status: 'done' }
    return { ...s, status: 'pending' }
  })
})

const getStatusType = (s) => {
  const m = { RESUME_PENDING: 'warning', RESUME_PASSED: 'success', RESUME_REJECTED: 'danger', FIRST_INTERVIEW_PENDING: 'warning', FIRST_INTERVIEW_PASSED: 'success', FIRST_INTERVIEW_REJECTED: 'danger', SECOND_INTERVIEW_PENDING: 'warning', SECOND_INTERVIEW_PASSED: 'success', SECOND_INTERVIEW_REJECTED: 'danger', HIRED: 'success', ABANDONED: 'info', TALENT_POOL: 'info' }
  return m[s] || 'info'
}
const getStatusLabel = (s) => {
  const m = { IMPORTED: '简历待解析', RESUME_PENDING: '简历待筛选', RESUME_PASSED: '简历通过', RESUME_REJECTED: '简历淘汰', FIRST_INTERVIEW_PENDING: '待约初试', FIRST_INTERVIEW_PASSED: '初试通过', FIRST_INTERVIEW_REJECTED: '初试淘汰', SECOND_INTERVIEW_PENDING: '待复试', SECOND_INTERVIEW_PASSED: '复试通过', SECOND_INTERVIEW_REJECTED: '复试淘汰', HIRED: '已录用', ABANDONED: '已放弃', TALENT_POOL: '人才库储备' }
  return m[s] || s
}
const getScoreColor = (s) => { if (!s && s !== 0) return '#9CA3AF'; if (s >= 80) return '#10B981'; if (s >= 60) return '#F59E0B'; return '#EF4444' }
const getScoreCircleColor = (s) => { if (!s && s !== 0) return 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%)'; if (s >= 80) return 'linear-gradient(135deg, #10B981 0%, #059669 100%)'; if (s >= 60) return 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'; return 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)' }
const getSuggestionType = (s) => { if (s === '建议约初试' || s === '建议进入复试' || s === '强烈建议进入下一轮' || s === '建议进入下一轮') return 'success'; if (s === '暂缓' || s === '人才库储备') return 'warning'; return 'danger' }
const getRiskType = (l) => { if (l === '低') return 'success'; if (l === '中') return 'warning'; return 'danger' }
const formatTime = (t) => { if (!t) return ''; const d = new Date(t); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}` }

const fetchCandidate = async () => {
  try { const r = await candidatesApi.getById(route.params.id); candidate.value = r.data } catch (e) { ElMessage.error('获取候选人详情失败') }
}
const fetchResumeScreeningReport = async () => {
  try { const r = await screeningApi.getLatest(route.params.id); resumeScreeningReport.value = r.data } catch (e) { resumeScreeningReport.value = null }
}
const fetchFirstInterviewRecord = async () => {
  try { const r = await firstInterviewRecordApi.getLatest(route.params.id); firstInterviewRecord.value = r.data } catch (e) { firstInterviewRecord.value = null }
}
const fetchFirstInterviewReport = async () => {
  try { const r = await firstInterviewAnalysisApi.getLatest(route.params.id); firstInterviewReport.value = r.data } catch (e) { firstInterviewReport.value = null }
}
const fetchSecondInterviewRecord = async () => {
  try { const r = await secondInterviewRecordApi.getLatest(route.params.id); secondInterviewRecord.value = r.data } catch (e) { secondInterviewRecord.value = null }
}
const fetchSecondInterviewReport = async () => {
  try { const r = await secondInterviewAnalysisApi.getLatest(route.params.id); secondInterviewReport.value = r.data } catch (e) { secondInterviewReport.value = null }
}

const triggerResumeScreening = async () => {
  screeningLoading.value = true
  try {
    await screeningApi.trigger(route.params.id, { force: false, request_id: null })
    ElMessage.success('简历筛选完成')
    await fetchResumeScreeningReport()
    await fetchCandidate()
    activeTab.value = 'screening'
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '简历筛选失败')
  } finally { screeningLoading.value = false }
}

const saveFirstInterviewRecord = async () => {
  if (!firstInterviewForm.record_text.trim()) { ElMessage.warning('请填写面试记录'); return }
  savingFirstRecord.value = true
  try {
    const r = await firstInterviewRecordApi.create(route.params.id, firstInterviewForm)
    await fetchFirstInterviewRecord()
    showFirstInterviewDialog.value = false
    ElMessage.success('初试记录已保存')

    // 自动触发分析
    firstAnalysisLoading.value = true
    try {
      await firstInterviewAnalysisApi.trigger(route.params.id, { interview_record_id: r.data.id, force: false })
      await fetchFirstInterviewReport()
      await fetchCandidate()
      ElMessage.success('初试评估已生成')
      activeTab.value = 'firstInterview'
    } catch (e) {
      ElMessage.warning('初试记录已保存，但评估生成失败')
    } finally { firstAnalysisLoading.value = false }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally { savingFirstRecord.value = false }
}

const saveSecondInterviewRecord = async () => {
  if (!secondInterviewForm.record_text.trim()) { ElMessage.warning('请填写面试记录'); return }
  savingSecondRecord.value = true
  try {
    const r = await secondInterviewRecordApi.create(route.params.id, secondInterviewForm)
    await fetchSecondInterviewRecord()
    showSecondInterviewDialog.value = false
    ElMessage.success('复试记录已保存')

    secondAnalysisLoading.value = true
    try {
      await secondInterviewAnalysisApi.trigger(route.params.id, { interview_record_id: r.data.id, force: false })
      await fetchSecondInterviewReport()
      await fetchCandidate()
      ElMessage.success('复试评估已生成')
      activeTab.value = 'secondInterview'
    } catch (e) {
      ElMessage.warning('复试记录已保存，但评估生成失败')
    } finally { secondAnalysisLoading.value = false }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally { savingSecondRecord.value = false }
}

const goBack = () => {
  if (candidate.value?.job_id) router.push(`/jobs/${candidate.value.job_id}`)
  else router.push('/candidates')
}

onMounted(() => {
  fetchCandidate()
  fetchResumeScreeningReport()
  fetchFirstInterviewRecord()
  fetchFirstInterviewReport()
  fetchSecondInterviewRecord()
  fetchSecondInterviewReport()
})
</script>

<style scoped>
.candidate-detail { max-width: 1160px; margin: 0 auto; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-actions { display: flex; gap: 8px; }
.overview-card { padding: 24px; margin-bottom: 16px; }
.overview-main { margin-bottom: 20px; }
.info-row-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.candidate-name { font-size: 26px; font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: 0; }
.candidate-meta { display: flex; gap: 12px 16px; flex-wrap: wrap; font-size: 13px; color: var(--color-text-secondary); align-items: center; }
.meta-item { display: flex; align-items: center; gap: 4px; }
.scores-row { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 0; padding-top: 16px; border-top: 1px solid var(--color-border); align-items: stretch; }
.score-item { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 58px; padding: 4px 12px; border-right: 1px solid var(--color-border); }
.score-item:last-child { border-right: 0; }
.score-circle-sm { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 16px; font-weight: 700; flex-shrink: 0; }
.score-label { font-size: 13px; color: var(--color-text-secondary); font-weight: 600; }
.score-label-top { margin-bottom: 4px; }
.text-muted { color: var(--color-text-muted); }

/* 进度条 */
.progress-card { padding: 20px 24px; margin-bottom: 16px; }
.progress-steps { display: flex; align-items: flex-start; gap: 0; }
.progress-step { display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; }
.step-dot { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; z-index: 1; }
.progress-step.done .step-dot { background: var(--color-primary); color: #fff; }
.progress-step.active .step-dot { background: var(--color-blue); color: #fff; box-shadow: 0 0 0 4px #e8f1ff; }
.progress-step.pending .step-dot { background: #edf1f5; color: var(--color-text-muted); }
.step-label { font-size: 12px; color: var(--color-text-secondary); margin-top: 8px; text-align: center; white-space: nowrap; font-weight: 600; }
.progress-step.active .step-label { color: var(--color-blue); }
.progress-step.done .step-label { color: var(--color-primary); }
.step-bar { position: absolute; top: 16px; left: calc(50% + 16px); right: calc(-50% + 16px); height: 2px; background: var(--color-border); }
.progress-step.done .step-bar { background: var(--color-primary); }
.progress-step.active .step-bar { background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-border) 100%); }

/* Tab */
.tab-card { padding: 0 24px; }
.detail-tabs { padding-top: 8px; }
.tab-content { padding: 16px 0 24px; }
.tab-empty { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px 20px; color: var(--color-text-muted); }
.tab-empty p { margin: 0; }

.resume-text { font-size: 14px; line-height: 1.8; white-space: pre-wrap; color: var(--color-text-secondary); padding: 18px; border-radius: var(--radius-card); background: var(--color-surface-soft); border: 1px solid var(--color-border); }

/* 报告 */
.report-header { display: flex; gap: 24px; margin-bottom: 20px; padding: 16px; background: var(--color-surface-soft); border: 1px solid var(--color-border); border-radius: var(--radius-card); align-items: center; }
.report-score-big { font-size: 36px; font-weight: 700; line-height: 1; }
.score-unit { font-size: 14px; font-weight: 400; }
.report-meta { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--color-text-secondary); }
.meta-lbl { color: var(--color-text-muted); }

.subsection { margin-bottom: 8px; }
.sub-title { font-size: 15px; font-weight: 700; color: var(--color-text); margin: 0 0 12px 0; }
.interview-meta { display: flex; gap: 20px; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 12px; }
.interview-text { font-size: 14px; line-height: 1.8; white-space: pre-wrap; color: var(--color-text-secondary); padding: 16px; border-radius: var(--radius-card); background: var(--color-surface-soft); border: 1px solid var(--color-border); }

.final-summary { padding: 16px 0; }
.final-scores { display: flex; gap: 32px; margin: 20px 0; }
.final-score-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.final-label { font-size: 13px; color: var(--color-text-secondary); }
.final-value { font-size: 28px; font-weight: 700; }
.final-note { font-size: 13px; color: var(--color-text-muted); margin-top: 16px; }

:deep(.el-descriptions__cell) { padding: 8px 12px !important; }
:deep(.el-divider) { margin: 20px 0; }

:deep(.el-tabs__item) {
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background: var(--color-primary);
}

:deep(.el-tabs__item.is-active),
:deep(.el-tabs__item:hover) {
  color: var(--color-primary);
}

@media (max-width: 900px) {
  .detail-header,
  .info-row-top {
    flex-direction: column;
    align-items: stretch;
  }

  .scores-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .score-item {
    justify-content: flex-start;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .score-item:last-child {
    border-bottom: 0;
  }

  .progress-steps {
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .progress-step {
    min-width: 92px;
  }
}
</style>
