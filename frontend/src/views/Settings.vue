<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-subtitle">管理岗位类型、解析规则和 AI 提示词配置</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="岗位类型配置" name="job-types">
        <section class="page-card settings-panel">
          <div class="panel-toolbar">
            <div>
              <h3>岗位类型字典</h3>
              <p>岗位初筛、JD 解析和岗位库会优先使用这里启用的类型。</p>
            </div>
            <el-button type="primary" @click="openJobTypeDialog()">
              <el-icon><Plus /></el-icon>
              新增岗位类型
            </el-button>
          </div>

          <div class="filter-row">
            <el-input
              v-model="jobTypeKeyword"
              placeholder="搜索岗位类型 / 说明"
              clearable
              @clear="fetchJobTypes"
              @keyup.enter="fetchJobTypes"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="fetchJobTypes">查询</el-button>
          </div>

          <el-table
            v-loading="jobTypeLoading"
            :data="jobTypeRows"
            class="settings-table"
          >
            <el-table-column prop="type_name" label="岗位类型" min-width="150">
              <template #default="{ row }">
                <div class="name-cell">
                  <span>{{ row.type_name }}</span>
                  <el-tag v-if="row.builtin" size="small" effect="light">内置</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
            <el-table-column label="筛选重点" min-width="260">
              <template #default="{ row }">
                <div class="tag-list">
                  <el-tag v-for="item in getFocusItems(row).slice(0, 4)" :key="item" size="small" effect="plain">
                    {{ item }}
                  </el-tag>
                  <span v-if="getFocusItems(row).length > 4" class="more-text">+{{ getFocusItems(row).length - 4 }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" effect="light">
                  {{ row.enabled ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sort_order" label="排序" width="90" align="center" />
            <el-table-column label="操作" width="170" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openJobTypeDialog(row)">编辑</el-button>
                <el-button type="danger" link @click="archiveJobType(row)">归档</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </el-tab-pane>

      <el-tab-pane label="AI 提示词配置" name="prompts">
        <section class="page-card settings-panel">
          <div class="panel-toolbar">
            <div>
              <h3>AI 提示词模板</h3>
              <p>启用后的模板会用于 JD 解析、简历解析和岗位匹配初筛。</p>
            </div>
            <el-button type="primary" @click="openPromptDialog()">
              <el-icon><Plus /></el-icon>
              新增提示词版本
            </el-button>
          </div>

          <div class="filter-row prompt-filter">
            <el-input
              v-model="promptKeyword"
              placeholder="搜索模板名称 / 场景"
              clearable
              @clear="fetchPrompts"
              @keyup.enter="fetchPrompts"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select v-model="promptKeyFilter" clearable placeholder="提示词类型" @change="fetchPrompts">
              <el-option v-for="item in promptKeyOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="promptStatusFilter" clearable placeholder="状态" @change="fetchPrompts">
              <el-option label="已启用" value="ACTIVE" />
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已归档" value="ARCHIVED" />
            </el-select>
            <el-button @click="fetchPrompts">查询</el-button>
          </div>

          <el-table
            v-loading="promptLoading"
            :data="promptRows"
            class="settings-table"
          >
            <el-table-column label="模板" min-width="220">
              <template #default="{ row }">
                <div class="name-cell prompt-name">
                  <span>{{ row.prompt_name }}</span>
                  <el-tag v-if="row.builtin" size="small" effect="light">默认</el-tag>
                </div>
                <span class="muted-text">{{ getPromptKeyLabel(row.prompt_key) }} · v{{ row.version }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="scene" label="场景" min-width="120" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="getPromptStatusType(row.status)" effect="light">
                  {{ getPromptStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
            <el-table-column label="更新时间" width="150">
              <template #default="{ row }">
                <span class="muted-text">{{ formatTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openPromptDialog(row)">编辑</el-button>
                <el-button v-if="row.status !== 'ACTIVE'" type="success" link @click="activatePrompt(row)">启用</el-button>
                <el-button type="primary" link @click="copyPrompt(row)">复制</el-button>
                <el-button type="danger" link @click="archivePrompt(row)">归档</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="reset-row">
            <el-select v-model="resetPromptKey" placeholder="选择提示词类型">
              <el-option v-for="item in promptKeyOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-button plain @click="resetPrompt">恢复默认模板</el-button>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="jobTypeDialogVisible"
      :title="jobTypeForm.id ? '编辑岗位类型' : '新增岗位类型'"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="岗位类型" required>
          <el-input v-model="jobTypeForm.type_name" placeholder="例如：销售业务类" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="jobTypeForm.description" type="textarea" :rows="2" placeholder="用于说明该岗位类型的适用范围" />
        </el-form-item>
        <el-form-item label="筛选重点">
          <el-input v-model="jobTypeForm.focus_text" type="textarea" :rows="5" placeholder="一行一个筛选重点" />
        </el-form-item>
        <div class="form-inline">
          <el-form-item label="排序">
            <el-input-number v-model="jobTypeForm.sort_order" :min="0" :max="999" />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="jobTypeForm.enabled" active-text="启用" inactive-text="停用" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="jobTypeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="jobTypeSaving" @click="saveJobType">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="promptDialogVisible"
      :title="promptForm.id ? '编辑提示词模板' : '新增提示词版本'"
      width="920px"
      destroy-on-close
    >
      <el-form label-position="top" class="prompt-form">
        <div class="form-grid">
          <el-form-item label="提示词类型" required>
            <el-select v-model="promptForm.prompt_key" :disabled="Boolean(promptForm.id)" placeholder="请选择">
              <el-option v-for="item in promptKeyOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="模板名称" required>
            <el-input v-model="promptForm.prompt_name" placeholder="例如：JD 解析提示词" />
          </el-form-item>
          <el-form-item label="场景">
            <el-input v-model="promptForm.scene" placeholder="例如：岗位初筛" />
          </el-form-item>
        </div>
        <el-form-item label="系统提示词">
          <el-input v-model="promptForm.system_prompt" type="textarea" :rows="8" placeholder="定义 AI 角色、规则和输出要求" />
        </el-form-item>
        <el-form-item label="用户提示词" required>
          <el-input v-model="promptForm.user_prompt" type="textarea" :rows="12" placeholder="可以使用 {jd_text}、{resume_text} 等变量" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="promptForm.remark" type="textarea" :rows="2" placeholder="记录本次调整目的" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="promptDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="promptSaving" @click="savePrompt">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { settingsApi } from '../api/analysis.js'

const route = useRoute()
const router = useRouter()

const activeTab = ref(route.query.section === 'prompts' ? 'prompts' : 'job-types')

const jobTypeLoading = ref(false)
const jobTypeSaving = ref(false)
const jobTypeKeyword = ref('')
const jobTypeRows = ref([])
const jobTypeDialogVisible = ref(false)
const jobTypeForm = reactive({
  id: null,
  type_name: '',
  description: '',
  focus_text: '',
  enabled: true,
  sort_order: 0
})

const promptLoading = ref(false)
const promptSaving = ref(false)
const promptKeyword = ref('')
const promptKeyFilter = ref('')
const promptStatusFilter = ref('')
const promptRows = ref([])
const promptDialogVisible = ref(false)
const resetPromptKey = ref('JD_PARSE')
const promptForm = reactive({
  id: null,
  prompt_key: '',
  prompt_name: '',
  scene: '',
  system_prompt: '',
  user_prompt: '',
  remark: ''
})

const promptKeyOptions = [
  { label: 'JD 解析', value: 'JD_PARSE' },
  { label: '简历解析', value: 'RESUME_PARSE' },
  { label: '岗位匹配初筛', value: 'SCREENING_MATCH' }
]

const activeSection = computed(() => route.query.section || 'job-types')

watch(
  () => route.query.section,
  (section) => {
    activeTab.value = section === 'prompts' ? 'prompts' : 'job-types'
  }
)

watch(activeTab, (tab) => {
  const section = tab === 'prompts' ? 'prompts' : 'job-types'
  if (activeSection.value !== section) {
    router.replace({ path: '/settings', query: { section } })
  }
  if (tab === 'prompts' && promptRows.value.length === 0) fetchPrompts()
  if (tab === 'job-types' && jobTypeRows.value.length === 0) fetchJobTypes()
})

const splitLines = (text) => {
  return String(text || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

const joinLines = (items) => {
  return Array.isArray(items) ? items.join('\n') : ''
}

const getFocusItems = (row) => {
  return Array.isArray(row?.evaluation_focus) ? row.evaluation_focus : []
}

const fetchJobTypes = async () => {
  jobTypeLoading.value = true
  try {
    const response = await settingsApi.listJobTypes({ keyword: jobTypeKeyword.value })
    jobTypeRows.value = response.data.items || []
  } catch (error) {
    ElMessage.error('获取岗位类型失败')
  } finally {
    jobTypeLoading.value = false
  }
}

const openJobTypeDialog = (row = null) => {
  jobTypeForm.id = row?.id || null
  jobTypeForm.type_name = row?.type_name || ''
  jobTypeForm.description = row?.description || ''
  jobTypeForm.focus_text = joinLines(row?.evaluation_focus)
  jobTypeForm.enabled = row?.enabled ?? true
  jobTypeForm.sort_order = row?.sort_order || 0
  jobTypeDialogVisible.value = true
}

const saveJobType = async () => {
  if (!jobTypeForm.type_name.trim()) {
    ElMessage.warning('请填写岗位类型')
    return
  }
  jobTypeSaving.value = true
  const payload = {
    type_name: jobTypeForm.type_name.trim(),
    description: jobTypeForm.description,
    evaluation_focus: splitLines(jobTypeForm.focus_text),
    enabled: jobTypeForm.enabled,
    sort_order: jobTypeForm.sort_order
  }
  try {
    if (jobTypeForm.id) {
      await settingsApi.updateJobType(jobTypeForm.id, payload)
    } else {
      await settingsApi.createJobType(payload)
    }
    ElMessage.success('岗位类型已保存')
    jobTypeDialogVisible.value = false
    fetchJobTypes()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存岗位类型失败')
  } finally {
    jobTypeSaving.value = false
  }
}

const archiveJobType = (row) => {
  ElMessageBox.confirm(`确认归档「${row.type_name}」吗？归档后不会出现在岗位类型下拉中。`, '归档岗位类型', {
    confirmButtonText: '确认归档',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await settingsApi.archiveJobType(row.id)
      ElMessage.success('已归档')
      fetchJobTypes()
    } catch (error) {
      ElMessage.error('归档失败')
    }
  }).catch(() => {})
}

const fetchPrompts = async () => {
  promptLoading.value = true
  try {
    const response = await settingsApi.listAiPrompts({
      keyword: promptKeyword.value,
      prompt_key: promptKeyFilter.value,
      status: promptStatusFilter.value
    })
    promptRows.value = response.data.items || []
  } catch (error) {
    ElMessage.error('获取提示词模板失败')
  } finally {
    promptLoading.value = false
  }
}

const getPromptKeyLabel = (value) => {
  return promptKeyOptions.find((item) => item.value === value)?.label || value
}

const getPromptStatusLabel = (status) => {
  if (status === 'ACTIVE') return '已启用'
  if (status === 'ARCHIVED') return '已归档'
  return '草稿'
}

const getPromptStatusType = (status) => {
  if (status === 'ACTIVE') return 'success'
  if (status === 'ARCHIVED') return 'info'
  return 'warning'
}

const openPromptDialog = (row = null) => {
  promptForm.id = row?.id || null
  promptForm.prompt_key = row?.prompt_key || promptKeyFilter.value || 'JD_PARSE'
  promptForm.prompt_name = row?.prompt_name || ''
  promptForm.scene = row?.scene || ''
  promptForm.system_prompt = row?.system_prompt || ''
  promptForm.user_prompt = row?.user_prompt || ''
  promptForm.remark = row?.remark || ''
  promptDialogVisible.value = true
}

const savePrompt = async () => {
  if (!promptForm.prompt_key || !promptForm.prompt_name.trim() || !promptForm.user_prompt.trim()) {
    ElMessage.warning('请填写提示词类型、模板名称和用户提示词')
    return
  }
  promptSaving.value = true
  const payload = {
    prompt_key: promptForm.prompt_key,
    prompt_name: promptForm.prompt_name.trim(),
    scene: promptForm.scene,
    system_prompt: promptForm.system_prompt,
    user_prompt: promptForm.user_prompt,
    remark: promptForm.remark
  }
  try {
    if (promptForm.id) {
      await settingsApi.updateAiPrompt(promptForm.id, payload)
    } else {
      await settingsApi.createAiPrompt(payload)
    }
    ElMessage.success('提示词模板已保存')
    promptDialogVisible.value = false
    fetchPrompts()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存提示词失败')
  } finally {
    promptSaving.value = false
  }
}

const activatePrompt = (row) => {
  ElMessageBox.confirm(`启用「${row.prompt_name}」后，同类型其他模板会变为草稿。`, '启用提示词模板', {
    confirmButtonText: '确认启用',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await settingsApi.activateAiPrompt(row.id)
      ElMessage.success('已启用')
      fetchPrompts()
    } catch (error) {
      ElMessage.error('启用失败')
    }
  }).catch(() => {})
}

const copyPrompt = async (row) => {
  try {
    await settingsApi.copyAiPrompt(row.id)
    ElMessage.success('已复制为新版本')
    fetchPrompts()
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const archivePrompt = (row) => {
  ElMessageBox.confirm(`确认归档「${row.prompt_name}」吗？`, '归档提示词模板', {
    confirmButtonText: '确认归档',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await settingsApi.archiveAiPrompt(row.id)
      ElMessage.success('已归档')
      fetchPrompts()
    } catch (error) {
      ElMessage.error('归档失败')
    }
  }).catch(() => {})
}

const resetPrompt = () => {
  if (!resetPromptKey.value) {
    ElMessage.warning('请选择提示词类型')
    return
  }
  ElMessageBox.confirm(`恢复「${getPromptKeyLabel(resetPromptKey.value)}」默认模板并启用？`, '恢复默认模板', {
    confirmButtonText: '确认恢复',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await settingsApi.resetAiPrompt(resetPromptKey.value)
      ElMessage.success('已恢复默认模板')
      fetchPrompts()
    } catch (error) {
      ElMessage.error('恢复失败')
    }
  }).catch(() => {})
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

onMounted(() => {
  fetchJobTypes()
  if (activeTab.value === 'prompts') fetchPrompts()
})
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  color: var(--color-text);
  font-size: 24px;
  letter-spacing: 0;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.settings-panel {
  padding: 20px;
}

.panel-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-toolbar h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 18px;
}

.panel-toolbar p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.filter-row .el-input {
  max-width: 320px;
}

.prompt-filter .el-select {
  width: 170px;
}

.settings-table {
  width: 100%;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text);
  font-weight: var(--font-semibold);
}

.prompt-name {
  margin-bottom: 4px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.more-text,
.muted-text {
  color: var(--color-text-muted);
  font-size: 12px;
}

.reset-row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 14px;
}

.reset-row .el-select {
  width: 190px;
}

.form-inline,
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.prompt-form .form-grid {
  grid-template-columns: 180px 1fr 180px;
}

@media (max-width: 860px) {
  .panel-toolbar,
  .filter-row,
  .reset-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-row .el-input,
  .prompt-filter .el-select,
  .reset-row .el-select {
    max-width: none;
    width: 100%;
  }

  .form-inline,
  .form-grid,
  .prompt-form .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
