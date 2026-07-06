<template>
  <div class="job-new">
    <div class="page-header">
      <div class="header-left">
        <el-button plain @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
      <h2 class="page-title">新建岗位</h2>
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
            <el-form-item label="岗位名称" prop="job_name">
              <el-input
                v-model="form.job_name"
                placeholder="例如：电商客服、售后客服"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属部门" prop="department">
              <el-input
                v-model="form.department"
                placeholder="例如：客服部、销售部"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="招聘人数" prop="headcount">
          <el-input-number
            v-model="form.headcount"
            :min="1"
            :max="999"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="岗位 JD / 岗位要求" prop="jd_text">
          <el-input
            v-model="form.jd_text"
            type="textarea"
            :rows="10"
            placeholder="请粘贴岗位职责、任职要求..."
            resize="none"
          />
          <div class="field-hint">
            <el-icon :size="14" color="#9CA3AF"><InfoFilled /></el-icon>
            <span>包含岗位职责、任职要求、薪资范围、工作时间等</span>
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
            <span>{{ loading ? '保存中...' : '保存岗位' }}</span>
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, InfoFilled, Check } from '@element-plus/icons-vue'
import { jobsApi } from '../api/analysis.js'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  job_name: '',
  department: '',
  headcount: 1,
  jd_text: '',
  remark: ''
})

const rules = {
  job_name: [
    { required: true, message: '请输入岗位名称', trigger: 'blur' }
  ],
  department: [
    { required: true, message: '请输入所属部门', trigger: 'blur' }
  ],
  headcount: [
    { required: true, message: '请输入招聘人数', trigger: 'blur' }
  ],
  jd_text: [
    { required: true, message: '请输入岗位 JD', trigger: 'blur' }
  ]
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
    const response = await jobsApi.create(form)
    ElMessage.success('岗位创建成功')
    router.push(`/jobs/${response.data.id}`)
  } catch (error) {
    const message = error.response?.data?.detail || '创建失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/jobs')
}
</script>

<style scoped>
.job-new {
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
  font-size: 22px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.form-card {
  padding: 32px;
}

.field-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: #9CA3AF;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #F3F4F6;
  margin-top: 8px;
}

:deep(.el-textarea__inner) {
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
}

:deep(.el-input__inner) {
  border-radius: 10px;
  height: 44px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  margin-bottom: 8px;
}
</style>
