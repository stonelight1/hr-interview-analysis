<template>
  <div class="analysis-new">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">新建面试分析</h2>
        <p class="page-subtitle">录入岗位、简历和面试记录，生成候选人评估报告</p>
      </div>
      <el-button plain @click="goToList">
        历史报告
      </el-button>
    </div>

    <div class="analysis-layout">
      <div class="page-card form-card">
        <el-steps :active="currentStep" finish-status="success" align-center class="form-steps">
          <el-step title="基础信息" />
          <el-step title="JD 与简历" />
          <el-step title="面试记录" />
        </el-steps>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          class="analysis-form"
        >
          <section v-show="currentStep === 0" class="step-panel">
            <div class="section-header">
              <div class="section-number">1</div>
              <div>
                <h3>基础信息</h3>
                <p>确定候选人和应聘岗位</p>
              </div>
            </div>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12">
                <el-form-item label="候选人姓名" prop="candidate_name">
                  <el-input
                    v-model="form.candidate_name"
                    placeholder="请输入候选人姓名"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="应聘岗位" prop="job_title">
                  <el-input
                    v-model="form.job_title"
                    placeholder="例如：电商客服"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </section>

          <section v-show="currentStep === 1" class="step-panel">
            <div class="section-header">
              <div class="section-number">2</div>
              <div>
                <h3>JD 与简历</h3>
                <p>补充岗位要求和候选人背景</p>
              </div>
            </div>

            <el-form-item label="岗位 JD / 岗位要求" prop="jd_text">
              <el-input
                v-model="form.jd_text"
                type="textarea"
                :rows="8"
                placeholder="粘贴岗位职责、任职要求、薪资范围、工作时间等"
                resize="none"
              />
            </el-form-item>

            <el-form-item label="候选人简历文本" prop="resume_text">
              <el-input
                v-model="form.resume_text"
                type="textarea"
                :rows="8"
                placeholder="粘贴候选人的简历正文"
                resize="none"
              />
            </el-form-item>
          </section>

          <section v-show="currentStep === 2" class="step-panel">
            <div class="section-header">
              <div class="section-number">3</div>
              <div>
                <h3>面试记录</h3>
                <p>补充对话记录并确认生成</p>
              </div>
            </div>

            <el-form-item label="面试记录文本" prop="interview_text">
              <el-input
                v-model="form.interview_text"
                type="textarea"
                :rows="11"
                placeholder="粘贴手动记录、会议转写或聊天记录"
                resize="none"
              />
            </el-form-item>

            <div class="confirm-strip">
              <div>
                <span>候选人</span>
                <strong>{{ form.candidate_name || '待填写' }}</strong>
              </div>
              <div>
                <span>应聘岗位</span>
                <strong>{{ form.job_title || '待填写' }}</strong>
              </div>
              <div>
                <span>资料完整度</span>
                <strong>{{ completedCount }} / {{ completionItems.length }}</strong>
              </div>
            </div>
          </section>
        </el-form>

        <div class="form-footer">
          <el-button @click="handleReset">重置</el-button>
          <el-button v-if="currentStep > 0" @click="currentStep -= 1">上一步</el-button>
          <el-button v-if="currentStep < 2" type="primary" @click="handleNext">
            下一步
          </el-button>
          <el-button
            v-else
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            <el-icon v-if="!loading"><MagicStick /></el-icon>
            <span>{{ loading ? '生成中...' : '开始分析' }}</span>
          </el-button>
        </div>
      </div>

      <aside class="side-panel">
        <div class="page-card assist-card">
          <h3>输入完整度</h3>
          <div class="completion-list">
            <div v-for="item in completionItems" :key="item.key" class="completion-item">
              <div>
                <span>{{ item.label }}</span>
                <em>{{ item.count }} 字</em>
              </div>
              <el-tag :type="item.done ? 'success' : 'info'" size="small" effect="light">
                {{ item.done ? '已填写' : '待填写' }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="page-card assist-card progress-card" v-if="loading">
          <h3>生成进度</h3>
          <div class="progress-list">
            <div
              v-for="(item, index) in progressSteps"
              :key="item"
              :class="['progress-item', index <= progressStep ? 'active' : '']"
            >
              <span class="progress-dot">
                <el-icon v-if="index < progressStep"><CircleCheck /></el-icon>
              </span>
              <p>{{ item }}</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, CircleCheck } from '@element-plus/icons-vue'
import { analysisApi } from '../api/analysis.js'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const currentStep = ref(0)
const progressStep = ref(0)
let progressTimer = null

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

const stepFields = [
  ['candidate_name', 'job_title'],
  ['jd_text', 'resume_text'],
  ['interview_text']
]

const progressSteps = ['资料解析', '岗位匹配', '风险识别', '报告生成']

const getTextCount = (value) => (value || '').trim().length

const completionItems = computed(() => [
  { key: 'candidate_name', label: '候选人', count: getTextCount(form.candidate_name), done: !!form.candidate_name.trim() },
  { key: 'job_title', label: '岗位', count: getTextCount(form.job_title), done: !!form.job_title.trim() },
  { key: 'jd_text', label: '岗位 JD', count: getTextCount(form.jd_text), done: !!form.jd_text.trim() },
  { key: 'resume_text', label: '简历文本', count: getTextCount(form.resume_text), done: !!form.resume_text.trim() },
  { key: 'interview_text', label: '面试记录', count: getTextCount(form.interview_text), done: !!form.interview_text.trim() }
])

const completedCount = computed(() => completionItems.value.filter(item => item.done).length)

const validateStep = async () => {
  if (!formRef.value) return false
  const fields = stepFields[currentStep.value]
  try {
    await Promise.all(fields.map(field => formRef.value.validateField(field)))
    return true
  } catch (error) {
    return false
  }
}

const handleNext = async () => {
  const valid = await validateStep()
  if (!valid) return
  currentStep.value += 1
}

const startProgress = () => {
  progressStep.value = 0
  progressTimer = window.setInterval(() => {
    progressStep.value = Math.min(progressStep.value + 1, progressSteps.length - 1)
  }, 1400)
}

const stopProgress = () => {
  if (progressTimer) {
    window.clearInterval(progressTimer)
    progressTimer = null
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    const firstInvalidStep = stepFields.findIndex(fields => fields.some(field => {
      const value = form[field]
      return !value || !String(value).trim()
    }))
    currentStep.value = Math.max(0, firstInvalidStep)
    return
  }

  loading.value = true
  startProgress()

  try {
    const response = await analysisApi.create(form)
    progressStep.value = progressSteps.length - 1
    ElMessage.success('分析成功')
    router.push(`/analysis/${response.data.id}`)
  } catch (error) {
    const message = error.response?.data?.detail || '分析失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    stopProgress()
    loading.value = false
  }
}

const handleReset = () => {
  form.candidate_name = ''
  form.job_title = ''
  form.jd_text = ''
  form.resume_text = ''
  form.interview_text = ''
  currentStep.value = 0
  formRef.value?.clearValidate()
}

const goToList = () => {
  router.push('/analysis/list')
}
</script>

<style scoped>
.analysis-new {
  max-width: 1180px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  gap: 16px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
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

.analysis-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: start;
}

.form-card {
  padding: 24px;
}

.form-steps {
  padding: 4px 0 24px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--color-border);
}

.analysis-form {
  min-height: 460px;
}

.step-panel {
  animation: fade-in 0.18s ease;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.section-number {
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.section-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 2px;
}

.section-header p {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.confirm-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-surface-soft);
}

.confirm-strip div {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-right: 1px solid var(--color-border);
  min-width: 0;
}

.confirm-strip div:last-child {
  border-right: 0;
}

.confirm-strip span {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 700;
}

.confirm-strip strong {
  font-size: 14px;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.side-panel {
  position: sticky;
  top: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assist-card {
  padding: 18px;
}

.assist-card h3 {
  font-size: 16px;
  color: var(--color-text);
  margin: 0 0 14px;
}

.completion-list,
.progress-list {
  display: flex;
  flex-direction: column;
}

.completion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.completion-item:last-child {
  border-bottom: 0;
}

.completion-item div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.completion-item span {
  font-size: 13px;
  color: var(--color-text);
  font-weight: 700;
}

.completion-item em {
  font-style: normal;
  font-size: 12px;
  color: var(--color-text-muted);
}

.progress-card {
  border-color: #bfe4df;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  color: var(--color-text-muted);
}

.progress-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.progress-item.active {
  color: var(--color-primary);
}

.progress-item.active .progress-dot {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.progress-item p {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
}

:deep(.el-step__title) {
  font-size: 13px;
  font-weight: 700;
}

:deep(.el-textarea__inner) {
  border-radius: var(--radius-control);
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.65;
  resize: none;
}

:deep(.el-input__inner) {
  height: 44px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: var(--color-text);
  font-weight: 700;
  margin-bottom: 8px;
}

@media (max-width: 1024px) {
  .analysis-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .form-card {
    padding: 20px;
  }

  .form-footer {
    flex-wrap: wrap;
  }

  .form-footer .el-button {
    flex: 1;
  }

  .confirm-strip {
    grid-template-columns: 1fr;
  }

  .confirm-strip div {
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .confirm-strip div:last-child {
    border-bottom: 0;
  }
}
</style>
