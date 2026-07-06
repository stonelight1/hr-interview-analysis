<template>
  <div class="job-list">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">岗位管理</h2>
        <p class="page-subtitle">管理招聘岗位，查看各岗位候选人情况</p>
      </div>
      <el-button type="primary" size="large" @click="goToNew">
        <el-icon><Plus /></el-icon>
        新建岗位
      </el-button>
    </div>

    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="岗位名称" class="filter-item">
          <el-input
            v-model="filters.job_name"
            placeholder="请输入"
            clearable
            @clear="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="所属部门" class="filter-item">
          <el-input
            v-model="filters.department"
            placeholder="请输入"
            clearable
            @clear="handleSearch"
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item label="岗位状态" class="filter-item">
          <el-select
            v-model="filters.status"
            placeholder="请选择"
            clearable
            @clear="handleSearch"
            style="width: 120px"
          >
            <el-option label="招聘中" value="OPEN" />
            <el-option label="已暂停" value="PAUSED" />
            <el-option label="已关闭" value="CLOSED" />
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
        :header-cell-style="{ background: '#F9FAFB', color: '#374151', fontWeight: 600 }"
      >
        <el-table-column prop="job_name" label="岗位名称" min-width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">
              {{ row.job_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="所属部门" min-width="100" />
        <el-table-column prop="headcount" label="招聘人数" min-width="80" align="center" />
        <el-table-column label="岗位状态" min-width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="140">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" plain size="small" @click="viewDetail(row.id)">
                查看详情
              </el-button>
              <el-button type="danger" plain size="small" @click="handleDelete(row.id)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="#D1D5DB"><Briefcase /></el-icon>
            <p class="empty-title">暂无岗位</p>
            <p class="empty-desc">点击「新建岗位」，开始发布第一个招聘岗位</p>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Briefcase } from '@element-plus/icons-vue'
import { jobsApi } from '../api/analysis.js'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

const filters = reactive({
  job_name: '',
  department: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

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
    const response = await jobsApi.list(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取岗位列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filters.job_name = ''
  filters.department = ''
  filters.status = ''
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
  router.push(`/jobs/${id}`)
}

const goToNew = () => {
  router.push('/jobs/new')
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除这个岗位吗？删除后不可恢复。', '确认删除', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    try {
      await jobsApi.delete(id)
      ElMessage.success('已删除')
      fetchData()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.job-list {
  max-width: 1180px;
  margin: 0 auto;
}

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

.table-section {
  padding: 0;
}

.table-section :deep(.el-table) {
  border-radius: 16px;
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

.pagination-wrapper {
  padding: 16px 24px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #F3F4F6;
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
  color: #6B7280;
  margin-top: 16px;
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 14px;
  color: #9CA3AF;
  margin: 0;
}
</style>
