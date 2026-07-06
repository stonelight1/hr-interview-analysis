<template>
  <div class="analysis-list">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">历史评估报告</h2>
        <p class="page-subtitle">集中查看 AI 面试分析结果，快速定位高风险候选人和可推进人选</p>
      </div>
      <div class="header-actions">
        <el-button :loading="loading" @click="fetchData">
          <el-icon v-if="!loading"><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" size="large" @click="goToNew">
          <el-icon><Plus /></el-icon>
          新建分析
        </el-button>
      </div>
    </div>

    <div class="stats-row">
      <div v-for="item in statsCards" :key="item.label" class="stat-card">
        <div :class="['stat-icon', item.tone]">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ item.value }}</div>
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-hint">{{ item.hint }}</div>
        </div>
      </div>
    </div>

    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form" @submit.prevent>
        <el-form-item label="候选人" class="filter-item">
          <el-input
            v-model="filters.candidate_name"
            placeholder="姓名关键词"
            clearable
            style="width: 150px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="岗位" class="filter-item">
          <el-input
            v-model="filters.job_title"
            placeholder="岗位关键词"
            clearable
            style="width: 170px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="录用建议" class="filter-item">
          <el-select
            v-model="filters.recommendation"
            placeholder="全部"
            clearable
            style="width: 160px"
            @clear="handleSearch"
          >
            <el-option label="强烈建议进入下一轮" value="强烈建议进入下一轮" />
            <el-option label="建议进入下一轮" value="建议进入下一轮" />
            <el-option label="暂缓" value="暂缓" />
            <el-option label="不建议" value="不建议" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级" class="filter-item">
          <el-select
            v-model="filters.risk_level"
            placeholder="全部"
            clearable
            style="width: 120px"
            @clear="handleSearch"
          >
            <el-option label="低" value="低" />
            <el-option label="中" value="中" />
            <el-option label="高" value="高" />
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

      <div v-if="activeFilterChips.length" class="active-filters">
        <span class="active-filter-label">已筛选</span>
        <el-tag
          v-for="item in activeFilterChips"
          :key="item.key"
          closable
          effect="plain"
          size="small"
          @close="clearFilter(item.key)"
        >
          {{ item.label }}
        </el-tag>
      </div>
    </div>

    <div class="page-card table-section">
      <div class="table-toolbar">
        <div class="toolbar-title">
          <span>报告列表</span>
          <em>点击行可快速预览</em>
        </div>
        <div class="toolbar-meta">
          共 {{ pagination.total }} 份报告
        </div>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        row-key="id"
        style="width: 100%"
        :header-cell-style="{ background: '#F9FAFB', color: '#374151', fontWeight: 600 }"
        :row-class-name="getRowClassName"
        @row-click="openPreview"
      >
        <el-table-column label="候选人 / 岗位" min-width="220">
          <template #default="{ row }">
            <div class="candidate-cell">
              <div class="candidate-line">
                <span class="candidate-name">{{ row.candidate_name || '未命名候选人' }}</span>
                <el-tag v-if="row.confidence" size="small" effect="plain" type="info">
                  置信度 {{ row.confidence }}
                </el-tag>
              </div>
              <div class="job-line">
                <el-icon :size="14"><Briefcase /></el-icon>
                <span>{{ row.job_title || '未填写岗位' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="匹配度" min-width="150">
          <template #default="{ row }">
            <div class="score-cell">
              <el-progress
                :percentage="normalizeScore(row.match_score)"
                :color="getScoreColor(row.match_score)"
                :stroke-width="6"
                :show-text="false"
                style="width: 70px"
              />
              <div class="score-copy">
                <span class="score-text" :style="{ color: getScoreColor(row.match_score) }">
                  {{ row.match_score ?? 0 }}分
                </span>
                <span>{{ getScoreLevel(row.match_score) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="录用建议" min-width="150">
          <template #default="{ row }">
            <el-tag :type="getRecommendationType(row.recommendation)" effect="light" size="small">
              {{ row.recommendation || '暂无建议' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险" min-width="95" align="center">
          <template #default="{ row }">
            <span :class="['risk-badge', `risk-${getRiskClass(row.risk_level)}`]">
              {{ row.risk_level || '未知' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="生成时间" min-width="150">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="132" fixed="right" align="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-tooltip content="快速预览" placement="top">
                <el-button circle plain size="small" @click.stop="openPreview(row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="完整报告" placement="top">
                <el-button circle plain size="small" type="primary" @click.stop="viewDetail(row.id)">
                  <el-icon><Document /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除报告" placement="top">
                <el-button
                  circle
                  plain
                  size="small"
                  type="danger"
                  :loading="deletingId === row.id"
                  @click.stop="handleDelete(row.id)"
                >
                  <el-icon v-if="deletingId !== row.id"><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><Document /></el-icon>
            <p class="empty-title">暂无评估报告</p>
            <p class="empty-desc">完成一次面试分析后，报告会出现在这里，方便后续复盘和对比</p>
            <el-button type="primary" @click="goToNew">
              <el-icon><Plus /></el-icon>
              新建分析
            </el-button>
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

    <el-drawer
      v-model="previewVisible"
      direction="rtl"
      size="520px"
      :with-header="false"
      class="report-drawer"
    >
      <div class="drawer-shell" v-loading="previewLoading">
        <div class="drawer-header">
          <div>
            <p class="drawer-kicker">报告预览</p>
            <h3>{{ selectedReport?.candidate_name || '未命名候选人' }}</h3>
            <span>{{ selectedReport?.job_title || '未填写岗位' }}</span>
          </div>
          <el-button circle text @click="closePreview">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <template v-if="selectedReport">
          <div class="preview-metrics">
            <div class="preview-score" :style="{ color: getScoreColor(selectedReport.match_score) }">
              {{ selectedReport.match_score ?? 0 }}
              <span>分</span>
            </div>
            <div class="preview-tags">
              <el-tag :type="getRecommendationType(selectedReport.recommendation)" effect="light">
                {{ selectedReport.recommendation || '暂无建议' }}
              </el-tag>
              <el-tag :type="getRiskType(selectedReport.risk_level)" effect="light">
                {{ selectedReport.risk_level || '未知' }}风险
              </el-tag>
            </div>
          </div>

          <div class="preview-section">
            <div class="preview-section-title">
              <el-icon><Document /></el-icon>
              总体结论
            </div>
            <p>{{ previewSummary }}</p>
          </div>

          <div class="preview-section" v-if="previewLeader">
            <div class="preview-section-title">
              <el-icon><User /></el-icon>
              给领导看的结论
            </div>
            <p>{{ previewLeader }}</p>
          </div>

          <div class="preview-section split-section">
            <div>
              <div class="preview-section-title success-title">
                <el-icon><CircleCheck /></el-icon>
                主要优势
              </div>
              <ul v-if="previewAdvantages.length" class="preview-list">
                <li v-for="item in previewAdvantages" :key="item.title || item.detail">
                  <strong>{{ item.title || '优势' }}</strong>
                  <span>{{ item.detail || item.evidence || '暂无说明' }}</span>
                </li>
              </ul>
              <p v-else class="muted-text">报告未给出明确优势。</p>
            </div>

            <div>
              <div class="preview-section-title warning-title">
                <el-icon><Warning /></el-icon>
                关注点
              </div>
              <ul v-if="previewWeaknesses.length" class="preview-list">
                <li v-for="item in previewWeaknesses" :key="item.title || item.detail">
                  <strong>{{ item.title || '不足' }}</strong>
                  <span>{{ item.detail || item.evidence || '暂无说明' }}</span>
                </li>
              </ul>
              <p v-else class="muted-text">报告未给出明显不足。</p>
            </div>
          </div>

          <div class="preview-section" v-if="previewRisks.length">
            <div class="preview-section-title danger-title">
              <el-icon><WarningFilled /></el-icon>
              风险点
            </div>
            <div class="risk-preview-list">
              <div v-for="item in previewRisks" :key="item.risk || item.detail" class="risk-preview-item">
                <div>
                  <strong>{{ item.risk || '风险点' }}</strong>
                  <p>{{ item.detail || '暂无说明' }}</p>
                </div>
                <el-tag :type="getRiskType(item.level)" effect="light" size="small">
                  {{ item.level || '中' }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="preview-section" v-if="previewQuestions.length">
            <div class="preview-section-title">
              <el-icon><QuestionFilled /></el-icon>
              建议追问
            </div>
            <ol class="question-list">
              <li v-for="item in previewQuestions" :key="item.question">
                {{ item.question }}
              </li>
            </ol>
          </div>
        </template>

        <div class="drawer-footer">
          <el-button @click="closePreview">关闭</el-button>
          <el-button type="primary" :disabled="!selectedReport" @click="viewDetail(selectedReport.id)">
            查看完整报告
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Document, CircleCheck, Warning, WarningFilled,
  TrendCharts, Refresh, View, Delete, Briefcase, User, Close,
  ArrowRight, QuestionFilled
} from '@element-plus/icons-vue'
import { analysisApi } from '../api/analysis.js'

const router = useRouter()

const loading = ref(false)
const deletingId = ref(null)
const tableData = ref([])
const previewVisible = ref(false)
const previewLoading = ref(false)
const selectedReport = ref(null)
const selectedResult = ref(null)

const filters = reactive({
  candidate_name: '',
  job_title: '',
  recommendation: '',
  risk_level: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const stats = computed(() => {
  const items = tableData.value || []
  const recommended = items.filter(i => i.recommendation === '强烈建议进入下一轮' || i.recommendation === '建议进入下一轮').length
  const highRisk = items.filter(i => i.risk_level === '高').length
  const avgScore = items.length > 0 ? Math.round(items.reduce((sum, i) => sum + normalizeScore(i.match_score), 0) / items.length) : 0
  return { total: pagination.total, recommended, highRisk, avgScore }
})

const statsCards = computed(() => [
  { label: '总报告数', hint: '历史累计', value: stats.value.total, icon: Document, tone: 'tone-blue' },
  { label: '当前页推荐', hint: '建议推进', value: stats.value.recommended, icon: CircleCheck, tone: 'tone-green' },
  { label: '当前页高风险', hint: '需要重点复核', value: stats.value.highRisk, icon: Warning, tone: 'tone-red' },
  { label: '当前页均分', hint: '匹配度均值', value: stats.value.avgScore, icon: TrendCharts, tone: 'tone-amber' }
])

const activeFilterChips = computed(() => {
  const chips = []
  if (filters.candidate_name) chips.push({ key: 'candidate_name', label: `候选人：${filters.candidate_name}` })
  if (filters.job_title) chips.push({ key: 'job_title', label: `岗位：${filters.job_title}` })
  if (filters.recommendation) chips.push({ key: 'recommendation', label: `建议：${filters.recommendation}` })
  if (filters.risk_level) chips.push({ key: 'risk_level', label: `风险：${filters.risk_level}` })
  return chips
})

const previewSummary = computed(() => {
  return selectedResult.value?.candidate_overview?.summary || '该报告暂无结构化总结，可进入完整报告查看原始分析结果。'
})

const previewLeader = computed(() => {
  return selectedResult.value?.leader_summary?.short_conclusion || ''
})

const previewAdvantages = computed(() => {
  return (selectedResult.value?.candidate_analysis?.advantages || []).slice(0, 2)
})

const previewWeaknesses = computed(() => {
  const weaknesses = selectedResult.value?.candidate_analysis?.weaknesses || []
  const risks = selectedResult.value?.candidate_analysis?.risk_points || []
  return weaknesses.length ? weaknesses.slice(0, 2) : risks.slice(0, 2).map(item => ({
    title: item.risk,
    detail: item.detail
  }))
})

const previewRisks = computed(() => {
  return (selectedResult.value?.candidate_analysis?.risk_points || []).slice(0, 3)
})

const previewQuestions = computed(() => {
  return (selectedResult.value?.follow_up_questions || []).slice(0, 3)
})

const normalizeScore = (score) => {
  const value = Number(score)
  if (Number.isNaN(value)) return 0
  return Math.min(100, Math.max(0, value))
}

const getScoreColor = (score) => {
  const value = normalizeScore(score)
  if (value >= 80) return '#10B981'
  if (value >= 60) return '#F59E0B'
  return '#EF4444'
}

const getScoreLevel = (score) => {
  const value = normalizeScore(score)
  if (value >= 85) return '优秀'
  if (value >= 70) return '良好'
  if (value >= 60) return '可观察'
  return '风险'
}

const getRecommendationType = (recommendation) => {
  if (recommendation === '强烈建议进入下一轮' || recommendation === '建议进入下一轮') return 'success'
  if (recommendation === '暂缓') return 'warning'
  if (!recommendation) return 'info'
  return 'danger'
}

const getRiskType = (riskLevel) => {
  if (riskLevel === '低') return 'success'
  if (riskLevel === '中') return 'warning'
  if (!riskLevel) return 'info'
  return 'danger'
}

const getRiskClass = (riskLevel) => {
  if (riskLevel === '低') return 'low'
  if (riskLevel === '中') return 'medium'
  if (riskLevel === '高') return 'high'
  return 'unknown'
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

const parseAnalysisResult = (value) => {
  if (!value) return null
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch (error) {
    return null
  }
}

const buildListParams = () => {
  const params = {
    page: pagination.page,
    page_size: pagination.page_size
  }
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params[key] = value
  })
  return params
}

const fetchData = async () => {
  loading.value = true
  try {
    const response = await analysisApi.list(buildListParams())
    tableData.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filters.candidate_name = ''
  filters.job_title = ''
  filters.recommendation = ''
  filters.risk_level = ''
  pagination.page = 1
  fetchData()
}

const clearFilter = (key) => {
  filters[key] = ''
  handleSearch()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const openPreview = async (row) => {
  selectedReport.value = row
  selectedResult.value = null
  previewVisible.value = true
  previewLoading.value = true

  try {
    const response = await analysisApi.getById(row.id)
    selectedReport.value = response.data
    selectedResult.value = parseAnalysisResult(response.data.analysis_result)
  } catch (error) {
    ElMessage.error('获取报告详情失败')
  } finally {
    previewLoading.value = false
  }
}

const closePreview = () => {
  previewVisible.value = false
}

const getRowClassName = ({ row }) => {
  return selectedReport.value?.id === row.id ? 'current-preview-row' : ''
}

const viewDetail = (id) => {
  if (!id) return
  router.push(`/analysis/${id}`)
}

const goToNew = () => {
  router.push('/analysis/new')
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除这条分析报告吗？删除后不可恢复。', '确认删除', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    deletingId.value = id
    try {
      await analysisApi.delete(id)
      ElMessage.success('已删除')
      if (selectedReport.value?.id === id) {
        closePreview()
        selectedReport.value = null
        selectedResult.value = null
      }
      fetchData()
    } catch (error) {
      ElMessage.error('删除失败')
    } finally {
      deletingId.value = null
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.analysis-list {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0;
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

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  letter-spacing: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-1px);
  border-color: var(--color-border-strong);
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08);
}

.stat-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.tone-blue { background: #e8f1ff; color: var(--color-blue); }
.tone-green { background: #e7f4f2; color: var(--color-primary); }
.tone-red { background: #feecec; color: var(--color-red); }
.tone-amber { background: #fff7db; color: var(--color-amber); }

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.1;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 2px;
  font-weight: 700;
}

.stat-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
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
  font-weight: 600;
  padding-bottom: 6px;
}

.filter-actions {
  margin-left: auto;
  margin-right: 0 !important;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid var(--color-border);
}

.active-filter-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 600;
}

.table-section {
  padding: 0;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.toolbar-title span {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
}

.toolbar-title em {
  font-style: normal;
  font-size: 13px;
  color: var(--color-text-muted);
}

.toolbar-meta {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.table-section :deep(.el-table) {
  border-radius: var(--radius-card);
}

.table-section :deep(.el-table__header th) {
  height: 46px;
}

.table-section :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.table-section :deep(.current-preview-row td.el-table__cell) {
  background: var(--color-primary-soft);
}

.candidate-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.candidate-line {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.candidate-name {
  color: var(--color-text);
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.job-line {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.job-line span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 44px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.score-text {
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.risk-high { background: #feecec; color: var(--color-red); }
.risk-medium { background: #fff7db; color: var(--color-amber); }
.risk-low { background: #e7f4f2; color: var(--color-primary); }
.risk-unknown { background: #eef2f7; color: var(--color-text-secondary); }

.time-cell {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.action-btns {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
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
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-top: 16px;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 20px 0;
  text-align: center;
  max-width: 420px;
}

.drawer-shell {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--color-border);
}

.drawer-kicker {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 700;
  margin: 0 0 4px;
}

.drawer-header h3 {
  font-size: 20px;
  line-height: 1.3;
  color: var(--color-text);
  margin: 0 0 6px;
}

.drawer-header span {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.preview-metrics {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px;
  background: var(--color-surface-soft);
  border-bottom: 1px solid var(--color-border);
}

.preview-score {
  font-size: 34px;
  font-weight: 800;
  line-height: 1;
}

.preview-score span {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.preview-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.preview-section {
  padding: 18px 24px;
  border-bottom: 1px solid var(--color-border);
}

.preview-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 10px;
}

.success-title {
  color: var(--color-primary);
}

.warning-title {
  color: var(--color-amber);
}

.danger-title {
  color: var(--color-red);
}

.preview-section p {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
}

.split-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.preview-list li {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.preview-list strong,
.risk-preview-item strong {
  font-size: 13px;
  color: var(--color-text);
}

.preview-list span {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.muted-text {
  color: var(--color-text-muted) !important;
}

.risk-preview-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-preview-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.risk-preview-item p {
  font-size: 13px;
  margin-top: 4px;
}

.question-list {
  margin: 0;
  padding-left: 20px;
}

.question-list li {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-bottom: 6px;
}

.drawer-footer {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  margin-top: auto;
  border-top: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.96);
}

:deep(.report-drawer .el-drawer__body) {
  padding: 0;
}

@media (max-width: 1080px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .filter-actions {
    margin-left: 0;
  }
}

@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-form :deep(.el-form-item) {
    width: 100%;
  }

  .filter-form :deep(.el-input),
  .filter-form :deep(.el-select) {
    width: 100% !important;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .table-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .split-section {
    grid-template-columns: 1fr;
  }

  :deep(.report-drawer) {
    width: 100% !important;
  }
}
</style>
