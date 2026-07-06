<template>
  <div class="analysis-list">
    <!-- 标题区 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">历史分析报告</h2>
        <p class="page-subtitle">查看候选人分析结果，快速筛选高匹配或高风险候选人</p>
      </div>
      <el-button type="primary" size="large" @click="goToNew">
        <el-icon><Plus /></el-icon>
        新建分析
      </el-button>
    </div>

    <!-- 数据概览 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon stat-icon-blue">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总报告数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-green">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.recommended }}</div>
          <div class="stat-label">建议进入下一轮</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-red">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.highRisk }}</div>
          <div class="stat-label">高风险候选人</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-purple">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.avgScore }}</div>
          <div class="stat-label">平均匹配度</div>
        </div>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="候选人姓名" class="filter-item">
          <el-input
            v-model="filters.candidate_name"
            placeholder="请输入"
            clearable
            @clear="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="应聘岗位" class="filter-item">
          <el-input
            v-model="filters.job_title"
            placeholder="请输入"
            clearable
            @clear="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="录用建议" class="filter-item">
          <el-select
            v-model="filters.recommendation"
            placeholder="请选择"
            clearable
            @clear="handleSearch"
            style="width: 160px"
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
            placeholder="请选择"
            clearable
            @clear="handleSearch"
            style="width: 120px"
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
    </div>

    <!-- 表格区 -->
    <div class="page-card table-section">
      <el-table
        :data="tableData"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ background: '#F9FAFB', color: '#374151', fontWeight: 600 }"
      >
        <el-table-column prop="candidate_name" label="候选人姓名" min-width="110" />
        <el-table-column prop="job_title" label="应聘岗位" min-width="120" />
        <el-table-column label="匹配度" min-width="140">
          <template #default="{ row }">
            <div class="score-cell">
              <el-progress
                :percentage="row.match_score"
                :color="getScoreColor(row.match_score)"
                :stroke-width="6"
                :show-text="false"
                style="width: 60px"
              />
              <span class="score-text" :style="{ color: getScoreColor(row.match_score) }">
                {{ row.match_score }}分
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="录用建议" min-width="140">
          <template #default="{ row }">
            <el-tag
              :type="getRecommendationType(row.recommendation)"
              effect="light"
              size="small"
            >
              {{ row.recommendation }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" min-width="90">
          <template #default="{ row }">
            <el-tag
              :type="getRiskType(row.risk_level)"
              effect="light"
              size="small"
            >
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AI置信度" min-width="90">
          <template #default="{ row }">
            <el-tag type="info" effect="light" size="small">
              {{ row.confidence }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="150">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button
                type="primary"
                plain
                size="small"
                @click="viewDetail(row.id)"
              >
                查看
              </el-button>
              <el-button
                type="danger"
                plain
                size="small"
                @click="handleDelete(row.id)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><Document /></el-icon>
            <p class="empty-title">暂无分析报告</p>
            <p class="empty-desc">点击「新建分析」，开始生成第一份候选人报告</p>
          </div>
        </template>
      </el-table>

      <!-- 分页 -->
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Document, CircleCheck, Warning, TrendCharts } from '@element-plus/icons-vue'
import { analysisApi } from '../api/analysis.js'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

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

// 统计数据（基于当前列表数据计算）
const stats = computed(() => {
  const items = tableData.value || []
  const total = pagination.total
  const recommended = items.filter(i => i.recommendation === '强烈建议进入下一轮' || i.recommendation === '建议进入下一轮').length
  const highRisk = items.filter(i => i.risk_level === '高').length
  const avgScore = items.length > 0 ? Math.round(items.reduce((sum, i) => sum + (i.match_score || 0), 0) / items.length) : 0
  return { total, recommended, highRisk, avgScore }
})

const getScoreColor = (score) => {
  if (score >= 80) return '#10B981'
  if (score >= 60) return '#F59E0B'
  return '#EF4444'
}

const getRecommendationType = (recommendation) => {
  if (recommendation === '强烈建议进入下一轮' || recommendation === '建议进入下一轮') return 'success'
  if (recommendation === '暂缓') return 'warning'
  return 'danger'
}

const getRiskType = (riskLevel) => {
  if (riskLevel === '低') return 'success'
  if (riskLevel === '中') return 'warning'
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

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const response = await analysisApi.list(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取数据失败')
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

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const viewDetail = (id) => {
  router.push(`/analysis/${id}`)
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除这条分析报告吗？删除后不可恢复。', '确认删除', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    try {
      await analysisApi.delete(id)
      ElMessage.success('已删除')
      fetchData()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const goToNew = () => {
  router.push('/analysis/new')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.analysis-list {
  max-width: 1180px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #6B7280;
  margin: 0;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid #F3F4F6;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-icon-blue {
  background: #EFF6FF;
  color: #2563EB;
}

.stat-icon-green {
  background: #ECFDF5;
  color: #10B981;
}

.stat-icon-red {
  background: #FEF2F2;
  color: #EF4444;
}

.stat-icon-purple {
  background: #F5F3FF;
  color: #8B5CF6;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #6B7280;
  margin-top: 2px;
}

/* 筛选区 */
.filter-section {
  padding: 20px 24px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.filter-form :deep(.el-form-item__label) {
  font-size: 13px;
  color: #6B7280;
  font-weight: 500;
  padding-bottom: 6px;
}

.filter-actions {
  margin-left: auto;
  margin-right: 0 !important;
}

/* 表格区 */
.table-section {
  padding: 0;
}

.table-section :deep(.el-table) {
  border-radius: 16px;
}

.table-section :deep(.el-table__header-wrapper) {
  border-radius: 16px 16px 0 0;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-text {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.time-cell {
  font-size: 13px;
  color: #6B7280;
  white-space: nowrap;
}

.action-btns {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 分页 */
.pagination-wrapper {
  padding: 16px 24px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #F3F4F6;
}

/* 空状态 */
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
  color: #6B7280;
  margin-top: 16px;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: #9CA3AF;
  margin: 0;
}

/* 响应式 */
@media (max-width: 1280px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .filter-form {
    flex-direction: column;
  }
}
</style>
