<template>
  <div class="analysis-new">
    <!-- 顶部说明 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">新建面试分析</h2>
        <p class="page-subtitle">粘贴 JD、简历和面试记录，系统将自动生成候选人匹配分析与 HR 面试复盘</p>
      </div>
      <div class="header-tip">
        <el-icon color="#F59E0B" :size="16"><InfoFilled /></el-icon>
        <span>建议面试记录越完整，AI 分析越准确</span>
      </div>
    </div>

    <!-- 表单卡片 -->
    <div class="page-card form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
      >
        <!-- 第一组：基础信息 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">1</div>
            <div class="section-title">
              <h3>基础信息</h3>
              <p>填写候选人的基本信息</p>
            </div>
          </div>
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
              <el-form-item label="应聘岗位" prop="job_title">
                <el-input
                  v-model="form.job_title"
                  placeholder="例如：电商客服、售后客服"
                  clearable
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 第二组：岗位与简历 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">2</div>
            <div class="section-title">
              <h3>岗位与简历</h3>
              <p>粘贴岗位 JD 和候选人简历文本</p>
            </div>
          </div>
          <el-form-item prop="jd_text">
            <template #label>
              <span class="field-label">岗位 JD / 岗位要求</span>
            </template>
            <el-input
              v-model="form.jd_text"
              type="textarea"
              :rows="5"
              placeholder="请粘贴岗位 JD 或岗位要求..."
              resize="none"
            />
            <div class="field-hint">
              <el-icon :size="14" color="#9CA3AF"><InfoFilled /></el-icon>
              <span>建议包含岗位职责、任职要求、薪资范围、工作时间等</span>
            </div>
          </el-form-item>

          <el-form-item prop="resume_text">
            <template #label>
              <span class="field-label">候选人简历文本</span>
            </template>
            <el-input
              v-model="form.resume_text"
              type="textarea"
              :rows="5"
              placeholder="请粘贴候选人简历文本..."
              resize="none"
            />
            <div class="field-hint">
              <el-icon :size="14" color="#9CA3AF"><InfoFilled /></el-icon>
              <span>可以直接复制简历正文，暂不支持 PDF 自动解析</span>
            </div>
          </el-form-item>
        </div>

        <!-- 第三组：面试记录 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">3</div>
            <div class="section-title">
              <h3>面试记录</h3>
              <p>粘贴面试过程中的对话记录</p>
            </div>
          </div>
          <el-form-item prop="interview_text">
            <template #label>
              <span class="field-label">面试记录文本</span>
            </template>
            <el-input
              v-model="form.interview_text"
              type="textarea"
              :rows="7"
              placeholder="请粘贴面试记录文本..."
              resize="none"
            />
            <div class="field-hint">
              <el-icon :size="14" color="#9CA3AF"><InfoFilled /></el-icon>
              <span>可以粘贴手动记录、会议转写文本或聊天记录</span>
            </div>
          </el-form-item>
        </div>

        <!-- 底部按钮 -->
        <div class="form-footer">
          <el-button size="large" @click="handleReset">重置</el-button>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
          >
            <el-icon v-if="!loading"><MagicStick /></el-icon>
            <span>{{ loading ? '分析中...' : '开始分析' }}</span>
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
import { InfoFilled, MagicStick } from '@element-plus/icons-vue'
import { analysisApi } from '../api/analysis.js'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  candidate_name: '',
  job_title: '',
  jd_text: '',
  resume_text: '',
  interview_text: ''
})

const rules = {
  candidate_name: [
    { required: true, message: '请输入候选人姓名', trigger: 'blur' }
  ],
  job_title: [
    { required: true, message: '请输入应聘岗位', trigger: 'blur' }
  ],
  jd_text: [
    { required: true, message: '请输入岗位 JD', trigger: 'blur' }
  ],
  resume_text: [
    { required: true, message: '请输入候选人简历文本', trigger: 'blur' }
  ],
  interview_text: [
    { required: true, message: '请输入面试记录文本', trigger: 'blur' }
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
    const response = await analysisApi.create(form)
    ElMessage.success('分析成功')
    router.push(`/analysis/${response.data.id}`)
  } catch (error) {
    const message = error.response?.data?.detail || '分析失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  form.candidate_name = ''
  form.job_title = ''
  form.jd_text = ''
  form.resume_text = ''
  form.interview_text = ''
}
</script>

<style scoped>
.analysis-new {
  max-width: 960px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
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

.header-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #FFFBEB;
  border: 1px solid #FEF3C7;
  border-radius: 10px;
  font-size: 13px;
  color: #92400E;
  flex-shrink: 0;
}

/* 表单卡片 */
.form-card {
  padding: 32px;
}

/* 表单分组 */
.form-section {
  margin-bottom: 32px;
}

.form-section:last-of-type {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #F3F4F6;
}

.section-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.section-title h3 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 2px 0;
}

.section-title p {
  font-size: 13px;
  color: #9CA3AF;
  margin: 0;
}

/* 字段标签 */
.field-label {
  font-weight: 500;
  color: #374151;
}

/* 字段提示 */
.field-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: #9CA3AF;
}

/* 底部按钮 */
.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #F3F4F6;
  margin-top: 8px;
}

/* 文本框样式优化 */
:deep(.el-textarea__inner) {
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
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

/* 响应式 */
@media (max-width: 768px) {
  .form-card {
    padding: 20px;
  }

  .page-header {
    flex-direction: column;
  }

  .header-tip {
    width: 100%;
  }
}
</style>
