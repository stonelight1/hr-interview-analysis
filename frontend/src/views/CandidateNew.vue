<template>
  <div class="candidate-new">
    <div class="page-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <h2 class="page-title">导入候选人</h2>
    </div>

    <div class="page-card form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="候选人姓名" prop="candidate_name">
              <el-input
                v-model="form.candidate_name"
                placeholder="请输入候选人姓名"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="应聘岗位" prop="job_id">
              <el-select
                v-model="form.job_id"
                placeholder="请选择岗位"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="job in jobs"
                  :key="job.id"
                  :label="job.job_name"
                  :value="job.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系方式">
              <el-input
                v-model="form.phone"
                placeholder="手机号/微信"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="候选人来源">
              <el-select
                v-model="form.source"
                placeholder="请选择来源"
                clearable
                style="width: 100%"
              >
                <el-option label="Boss直聘" value="Boss直聘" />
                <el-option label="智联招聘" value="智联招聘" />
                <el-option label="内部推荐" value="内部推荐" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="邮箱">
          <el-input
            v-model="form.email"
            placeholder="可选，候选人邮箱"
            clearable
          />
        </el-form-item>

        <el-form-item label="候选人简历文本" prop="resume_text">
          <el-input
            v-model="form.resume_text"
            type="textarea"
            :rows="10"
            placeholder="请粘贴候选人简历文本..."
            resize="none"
          />
          <div class="field-hint">
            <el-icon :size="14" color="#9CA3AF"><InfoFilled /></el-icon>
            <span>直接复制简历正文，暂不支持 PDF 自动解析</span>
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="可选，补充说明"
            resize="none"
          />
        </el-form-item>

        <div class="form-footer">
          <el-button size="large" @click="goBack">取消</el-button>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
          >
            <el-icon v-if="!loading"><Check /></el-icon>
            <span>{{ loading ? '导入中...' : '导入候选人' }}</span>
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, InfoFilled, Check } from '@element-plus/icons-vue'
import { jobsApi, candidatesApi } from '../api/analysis.js'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const jobs = ref([])

const form = reactive({
  job_id: route.query.job_id ? parseInt(route.query.job_id) : null,
  candidate_name: '',
  phone: '',
  email: '',
  source: '',
  resume_text: '',
  remark: ''
})

const rules = {
  candidate_name: [
    { required: true, message: '请输入候选人姓名', trigger: 'blur' }
  ],
  job_id: [
    { required: true, message: '请选择应聘岗位', trigger: 'change' }
  ],
  resume_text: [
    { required: true, message: '请输入候选人简历文本', trigger: 'blur' }
  ]
}

const fetchJobs = async () => {
  try {
    const response = await jobsApi.list({ page: 1, page_size: 100 })
    jobs.value = response.data.items
  } catch (error) {
    ElMessage.error('获取岗位列表失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  loading.value = true

  try {
    const response = await candidatesApi.create(form)
    ElMessage.success('候选人导入成功')
    router.push(`/candidates/${response.data.id}`)
  } catch (error) {
    const message = error.response?.data?.detail || '导入失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  if (route.query.job_id) {
    router.push(`/jobs/${route.query.job_id}`)
  } else {
    router.push('/candidates')
  }
}

onMounted(() => {
  fetchJobs()
})
</script>

<style scoped>
.candidate-new {
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0;
  letter-spacing: 0;
}

.form-card {
  padding: 28px;
}

.field-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
  margin-top: 8px;
}

:deep(.el-textarea__inner) {
  border-radius: var(--radius-control);
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
}

:deep(.el-input__inner) {
  height: 44px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: var(--color-text);
  font-weight: var(--font-semibold);
  margin-bottom: 8px;
}

@media (max-width: 760px) {
  .form-card {
    padding: 20px;
  }

  :deep(.el-col) {
    max-width: 100%;
    flex: 0 0 100%;
  }
}
</style>
