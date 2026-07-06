<template>
  <div class="candidate-list">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">候选人管理</h2>
        <p class="page-subtitle">查看所有候选人，快速筛选待处理的候选人</p>
      </div>
      <el-button type="primary" size="large" @click="goToNew">
        <el-icon><Plus /></el-icon>
        导入候选人
      </el-button>
    </div>

    <div class="page-card filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="候选人姓名" class="filter-item">
          <el-input
            v-model="filters.candidate_name"
            placeholder="请输入"
            clearable
            @clear="handleSearch"
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item label="当前状态" class="filter-item">
          <el-select
            v-model="filters.current_status"
            placeholder="请选择"
            clearable
            @clear="handleSearch"
            style="width: 140px"
          >
            <el-option label="简历待筛选" value="RESUME_PENDING" />
            <el-option label="简历通过" value="RESUME_PASSED" />
            <el-option label="简历淘汰" value="RESUME_REJECTED" />
            <el-option label="待初试" value="FIRST_INTERVIEW_PENDING" />
            <el-option label="初试通过" value="FIRST_INTERVIEW_PASSED" />
            <el-option label="初试淘汰" value="FIRST_INTERVIEW_REJECTED" />
            <el-option label="已录用" value="HIRED" />
            <el-option label="人才库储备" value="TALENT_POOL" />
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
        <el-table-column prop="candidate_name" label="候选人" min-width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">
              {{ row.candidate_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="job_id" label="应聘岗位" min-width="100">
          <template #default="{ row }">
            <span v-if="row.job_id">岗位 #{{ row.job_id }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系方式" min-width="120" />
        <el-table-column prop="source" label="来源" min-width="80" />
        <el-table-column label="当前状态" min-width="110">
          <template #default="{ row }">
            <el-tag effect="light" size="small">
              {{ getStatusLabel(row.current_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="简历匹配度" min-width="90">
          <template #default="{ row }">
            <span v-if="row.resume_match_score">{{ row.resume_match_score }}分</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="初试评分" min-width="90">
          <template #default="{ row }">
            <span v-if="row.first_interview_score">{{ row.first_interview_score }}分</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="viewDetail(row.id)">
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
import { ElMessage } from 'element-plus'
import { Plus, Search, User } from '@element-plus/icons-vue'
import { candidatesApi } from '../api/analysis.js'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

const filters = reactive({
  candidate_name: '',
  current_status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

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

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const response = await candidatesApi.list(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取候选人列表失败')
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
  filters.current_status = ''
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
  router.push(`/candidates/${id}`)
}

const goToNew = () => {
  router.push('/candidates/new')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.candidate-list {
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

.text-muted {
  color: #9CA3AF;
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
