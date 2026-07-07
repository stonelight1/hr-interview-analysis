<template>
  <div class="resume-records-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">简历解析记录</h2>
        <p class="page-subtitle">查看简历上传、解析复用、初筛结果和手动重新解析记录</p>
      </div>
      <el-button :icon="Refresh" plain @click="fetchRecords">刷新</el-button>
    </div>

    <section class="page-card filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索文件名 / 候选人 / 手机号 / 岗位"
            clearable
            style="width: 280px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="解析状态">
          <el-select
            v-model="filters.status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
            @change="handleSearch"
            @clear="handleSearch"
          >
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="复用来源">
          <el-select
            v-model="filters.reuse_source"
            placeholder="全部来源"
            clearable
            style="width: 170px"
            @change="handleSearch"
            @clear="handleSearch"
          >
            <el-option label="文件完全一致" value="FILE_HASH" />
            <el-option label="简历内容一致" value="TEXT_HASH" />
            <el-option label="手机号或邮箱一致" value="IDENTITY" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="page-card table-card">
      <div class="table-header">
        <div>
          <h3>解析记录</h3>
          <span>共 {{ pagination.total }} 条</span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="records"
        style="width: 100%"
      >
        <el-table-column label="简历文件" min-width="220">
          <template #default="{ row }">
            <div class="file-cell">
              <el-icon><Document /></el-icon>
              <div>
                <strong>{{ row.file_name }}</strong>
                <span>{{ row.file_type || '-' }} · #{{ row.id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="候选人" min-width="170">
          <template #default="{ row }">
            <div class="stack-cell">
              <strong>{{ row.candidate_name || '待解析' }}</strong>
              <span>{{ row.phone || row.email || '暂无联系方式' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="岗位 / 任务" min-width="210">
          <template #default="{ row }">
            <div class="stack-cell">
              <strong>{{ row.job_title || '未命名岗位' }}</strong>
              <span>{{ row.task_name || `任务 #${row.task_id}` }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="解析状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.parse_status)" effect="light">
              {{ statusText(row.parse_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="复用情况" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.reuse_source" type="success" effect="light">
              {{ reuseSourceText(row.reuse_source) }}
            </el-tag>
            <span v-else class="muted">AI 解析</span>
          </template>
        </el-table-column>
        <el-table-column label="初筛结果" width="150">
          <template #default="{ row }">
            <div v-if="row.screening_result_id" class="score-cell">
              <strong>{{ row.screening_score ?? '-' }}</strong>
              <span>{{ conclusionText(row.screening_conclusion) }}</span>
            </div>
            <span v-else class="muted">未筛选</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openDetail(row)">查看详情</el-button>
            <el-button text type="warning" size="small" :loading="row.reparsing" @click="reparseRecord(row)">
              重新解析
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="42" color="#CBD5E1"><Document /></el-icon>
            <p>暂无简历解析记录</p>
            <span>完成岗位初筛上传后，这里会展示每份简历的解析和复用情况。</span>
          </div>
        </template>
      </el-table>

      <div v-if="pagination.total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="fetchRecords"
        />
      </div>
    </section>

    <el-drawer v-model="detailVisible" title="简历解析详情" size="640px">
      <div v-loading="detailLoading" class="detail-panel">
        <template v-if="detail">
          <div class="detail-title">
            <h3>{{ detail.candidate_profile?.name || detail.resume_file.file_name }}</h3>
            <el-tag :type="statusTag(detail.resume_file.parse_status)" effect="light">
              {{ statusText(detail.resume_file.parse_status) }}
            </el-tag>
          </div>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="简历文件">{{ detail.resume_file.file_name }}</el-descriptions-item>
            <el-descriptions-item label="所属任务">{{ detail.task?.task_name || `任务 #${detail.resume_file.task_id}` }}</el-descriptions-item>
            <el-descriptions-item label="岗位">{{ detail.job_position?.position_name || detail.task?.job_title || '-' }}</el-descriptions-item>
            <el-descriptions-item label="候选人">{{ detail.candidate_profile?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系方式">
              {{ detail.candidate_profile?.phone || detail.candidate_profile?.email || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="解析复用">
              {{ detail.resume_file.reuse_source ? reuseSourceText(detail.resume_file.reuse_source) : '未复用历史解析' }}
            </el-descriptions-item>
            <el-descriptions-item label="初筛结果">
              <span v-if="detail.screening_result">
                {{ detail.screening_result.score ?? '-' }} 分 · {{ conclusionText(detail.screening_result.conclusion) }}
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="detail.resume_file.parse_error_message" label="处理说明">
              {{ detail.resume_file.parse_error_message }}
            </el-descriptions-item>
          </el-descriptions>

          <section v-if="detail.screening_result" class="detail-section">
            <h4>初筛依据</h4>
            <div class="tag-block">
              <el-tag
                v-for="item in detail.screening_result.match_highlights || []"
                :key="item"
                effect="light"
              >
                {{ item }}
              </el-tag>
              <el-tag
                v-for="item in detail.screening_result.risk_points || []"
                :key="item"
                type="warning"
                effect="light"
              >
                {{ item }}
              </el-tag>
            </div>
          </section>

          <el-collapse class="detail-collapse">
            <el-collapse-item title="结构化候选人信息" name="profile">
              <pre class="json-view">{{ formatJson(detail.candidate_profile?.profile_json) }}</pre>
            </el-collapse-item>
            <el-collapse-item title="原始简历文本" name="raw">
              <pre class="raw-text">{{ detail.resume_file.raw_text || '暂无原始文本' }}</pre>
            </el-collapse-item>
          </el-collapse>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Refresh, Search } from '@element-plus/icons-vue'
import { resumeFilesApi } from '../api/analysis.js'

const loading = ref(false)
const records = ref([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)

const filters = reactive({
  keyword: '',
  status: '',
  reuse_source: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const statusOptions = [
  { value: 'PENDING', label: '待处理' },
  { value: 'PARSING', label: '解析中' },
  { value: 'SCREENING', label: '初筛中' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'FAILED', label: '失败' }
]

const getErrorMessage = (error, fallback) => {
  const detailMessage = error?.response?.data?.detail
  if (typeof detailMessage === 'string') return detailMessage
  return fallback
}

const fetchRecords = async () => {
  loading.value = true
  try {
    const response = await resumeFilesApi.list({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      reuse_source: filters.reuse_source || undefined,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    records.value = (response.data.items || []).map((item) => ({ ...item, reparsing: false }))
    pagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '简历解析记录加载失败'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchRecords()
}

const handleReset = () => {
  filters.keyword = ''
  filters.status = ''
  filters.reuse_source = ''
  pagination.page = 1
  fetchRecords()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchRecords()
}

const openDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    const response = await resumeFilesApi.getById(row.id)
    detail.value = response.data
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '简历解析详情加载失败'))
  } finally {
    detailLoading.value = false
  }
}

const reparseRecord = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认重新解析「${row.file_name}」？这会重新调用 AI，并同步刷新当前任务的初筛结果。`,
      '重新解析简历',
      {
        confirmButtonText: '重新解析',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    row.reparsing = true
    await resumeFilesApi.reparse(row.id, { force_screen: true })
    ElMessage.success('已重新解析并刷新结果')
    await fetchRecords()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '重新解析失败，请稍后重试'))
    }
  } finally {
    row.reparsing = false
  }
}

const statusText = (status) => {
  const matched = statusOptions.find((item) => item.value === status)
  return matched?.label || status || '-'
}

const statusTag = (status) => {
  if (status === 'COMPLETED') return 'success'
  if (status === 'FAILED') return 'danger'
  if (status === 'PARSING' || status === 'SCREENING') return 'warning'
  return 'info'
}

const reuseSourceText = (source) => {
  if (source === 'FILE_HASH') return '文件一致'
  if (source === 'TEXT_HASH') return '内容一致'
  if (source === 'IDENTITY') return '身份一致'
  return source || '-'
}

const conclusionText = (value) => {
  if (value === 'RECOMMENDED') return '推荐面试'
  if (value === 'PENDING') return '待定'
  if (value === 'REJECTED') return '不推荐'
  return value || '-'
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const formatJson = (value) => {
  if (!value) return '暂无结构化信息'
  try {
    const parsed = typeof value === 'string' ? JSON.parse(value) : value
    return JSON.stringify(parsed, null, 2)
  } catch (error) {
    return String(value)
  }
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.resume-records-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  color: var(--color-text);
  font-size: 24px;
  font-weight: var(--font-bold);
  letter-spacing: 0;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.filter-card {
  padding: 16px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.filter-form :deep(.el-form-item__label) {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: var(--font-semibold);
  padding-bottom: 6px;
}

.filter-actions {
  margin-left: auto;
}

.table-card {
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border);
}

.table-header h3 {
  margin: 0 0 4px;
  color: var(--color-text);
  font-size: 17px;
}

.table-header span,
.muted,
.time-cell {
  color: var(--color-text-muted);
  font-size: 13px;
}

.file-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.file-cell .el-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.file-cell strong,
.stack-cell strong {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
  font-size: 14px;
}

.file-cell span,
.stack-cell span {
  display: block;
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.score-cell {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.score-cell strong {
  color: var(--color-primary);
  font-size: 18px;
}

.score-cell span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 14px 16px;
  background: var(--color-surface-soft);
  border-top: 1px solid var(--color-border);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 54px 20px;
}

.empty-state p {
  margin: 0;
  color: var(--color-text-secondary);
  font-weight: var(--font-bold);
}

.empty-state span {
  color: var(--color-text-muted);
  font-size: 13px;
}

.detail-panel {
  min-height: 260px;
}

.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-title h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 20px;
  letter-spacing: 0;
}

.detail-section {
  margin-top: 18px;
}

.detail-section h4 {
  margin: 0 0 10px;
  color: var(--color-text);
  font-size: 15px;
}

.tag-block {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-collapse {
  margin-top: 18px;
}

.json-view,
.raw-text {
  max-height: 320px;
  overflow: auto;
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  background: var(--color-surface-soft);
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-actions {
    margin-left: 0;
  }

  .filter-form :deep(.el-form-item),
  .filter-form :deep(.el-input),
  .filter-form :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
