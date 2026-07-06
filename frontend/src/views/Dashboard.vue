<template>
  <div class="dashboard">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">招聘工作台</h2>
        <p class="page-subtitle">查看当前招聘进度，快速处理待筛选简历、待约面候选人和待评估面试记录</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="large" @click="goToJobNew">
          <el-icon><Plus /></el-icon>
          新建岗位
        </el-button>
        <el-button size="large" @click="goToCandidateNew">
          <el-icon><Plus /></el-icon>
          新增候选人
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon stat-icon-blue">
          <el-icon><OfficeBuilding /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.open_jobs }}</div>
          <div class="stat-label">在招岗位</div>
          <div class="stat-desc">当前正在招聘的岗位数量</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-indigo">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_candidates }}</div>
          <div class="stat-label">候选人总数</div>
          <div class="stat-desc">系统内所有候选人</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-yellow">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.pending_screening }}</div>
          <div class="stat-label">待筛选简历</div>
          <div class="stat-desc">已导入但未完成 AI 筛选的候选人</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-orange">
          <el-icon><ChatLineRound /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.pending_first_interview }}</div>
          <div class="stat-label">待约初试</div>
          <div class="stat-desc">简历通过，等待 HR 约面</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-purple">
          <el-icon><List /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.pending_second_interview }}</div>
          <div class="stat-label">待复试</div>
          <div class="stat-desc">初试通过，等待复试安排</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-red">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.high_risk }}</div>
          <div class="stat-label">高风险候选人</div>
          <div class="stat-desc">AI 建议"不建议"的候选人</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="page-card quick-actions-card">
      <div class="section-header">
        <h3 class="section-title">快捷操作</h3>
      </div>
      <div class="quick-actions">
        <div class="action-item" @click="goToQuickJD">
          <div class="action-icon action-icon-blue">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="action-text">
            <span class="action-title">粘贴 JD 创建岗位</span>
            <span class="action-desc">粘贴 JD 文本，AI 自动解析</span>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="action-item" @click="goToCandidateNew">
          <div class="action-icon action-icon-green">
            <el-icon :size="24"><User /></el-icon>
          </div>
          <div class="action-text">
            <span class="action-title">导入候选人简历</span>
            <span class="action-desc">粘贴简历，AI 自动提取信息</span>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="action-item" @click="goToPendingScreening">
          <div class="action-icon action-icon-yellow">
            <el-icon :size="24"><Search /></el-icon>
          </div>
          <div class="action-text">
            <span class="action-title">处理待筛选简历</span>
            <span class="action-desc">{{ stats.pending_screening }} 位候选人待筛选</span>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 待处理事项 -->
    <div class="page-card pending-card">
      <div class="section-header">
        <h3 class="section-title">待处理事项</h3>
      </div>
      <div v-if="pendingItems.length === 0" class="empty-pending">
        <el-icon :size="40" color="#D1D5DB"><CircleCheck /></el-icon>
        <p>暂无待处理事项，当前招聘进展顺利</p>
      </div>
      <div v-else class="pending-list">
        <div v-for="item in pendingItems" :key="item.id" class="pending-item" @click="handlePendingClick(item)">
          <div class="pending-icon" :class="`pending-${item.type}`">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <div class="pending-info">
            <span class="pending-title">{{ item.title }}</span>
            <span class="pending-desc">{{ item.desc }}</span>
          </div>
          <el-tag :type="item.tagType" effect="light" size="small">{{ item.action }}</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, OfficeBuilding, User, Clock, ChatLineRound, List, Warning, Document,
  ArrowRight, CircleCheck, Search, Odometer, Aim, MagicStick
} from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

const stats = reactive({
  open_jobs: 0,
  total_candidates: 0,
  pending_screening: 0,
  pending_first_interview: 0,
  pending_second_interview: 0,
  high_risk: 0
})

const pendingItems = ref([])

const fetchStats = async () => {
  try {
    const response = await axios.get('/api/dashboard/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('获取 Dashboard 统计失败:', error)
  }
}

const buildPendingItems = () => {
  const items = []
  if (stats.pending_screening > 0) {
    items.push({
      id: 'screening',
      type: 'screening',
      icon: 'Search',
      title: `${stats.pending_screening} 位候选人待筛选`,
      desc: '简历已导入，请进行 AI 简历筛选',
      action: '开始筛选',
      tagType: 'warning',
      link: '/candidates?status=RESUME_PENDING'
    })
  }
  if (stats.pending_first_interview > 0) {
    items.push({
      id: 'first_interview',
      type: 'interview',
      icon: 'ChatLineRound',
      title: `${stats.pending_first_interview} 位候选人待约初试`,
      desc: '简历已通过，等待安排初试',
      action: '约初试',
      tagType: 'primary',
      link: '/candidates?status=RESUME_PASSED'
    })
  }
  if (stats.pending_second_interview > 0) {
    items.push({
      id: 'second_interview',
      type: 'interview',
      icon: 'List',
      title: `${stats.pending_second_interview} 位候选人待复试`,
      desc: '初试已通过，等待安排复试',
      action: '安排复试',
      tagType: 'primary',
      link: '/candidates?status=FIRST_INTERVIEW_PASSED'
    })
  }
  if (stats.high_risk > 0) {
    items.push({
      id: 'high_risk',
      type: 'risk',
      icon: 'Warning',
      title: `${stats.high_risk} 位候选人存在高风险`,
      desc: 'AI 建议不建议录用，请人工复核',
      action: '查看',
      tagType: 'danger',
      link: '/candidates?risk=high'
    })
  }
  pendingItems.value = items
}

const goToJobNew = () => router.push('/jobs/new')
const goToQuickJD = () => router.push('/jobs/new')
const goToCandidateNew = () => router.push('/candidates/new')
const goToPendingScreening = () => router.push('/candidates?status=RESUME_PENDING')

const handlePendingClick = (item) => {
  if (item.link) router.push(item.link)
}

onMounted(async () => {
  await fetchStats()
  buildPendingItems()
})
</script>

<style scoped>
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
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

.header-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

/* 统计卡片 6 列 */
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

.stat-icon-blue { background: #e8f1ff; color: var(--color-blue); }
.stat-icon-indigo { background: #eef2ff; color: #4f46e5; }
.stat-icon-yellow { background: #fff7db; color: var(--color-amber); }
.stat-icon-orange { background: #fff0e1; color: #ea580c; }
.stat-icon-purple { background: #f1edff; color: #7c3aed; }
.stat-icon-red { background: #feecec; color: var(--color-red); }

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
  font-weight: 600;
}

.stat-desc {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 4px;
  line-height: 1.3;
}

/* 快捷操作 */
.quick-actions-card {
  padding: 20px;
  margin-bottom: 20px;
}

.section-header {
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  cursor: pointer;
  transition: all 0.2s;
}

.action-item:hover {
  background: #fff;
  border-color: var(--color-primary);
  box-shadow: 0 8px 20px rgba(15, 118, 110, 0.08);
}

.action-icon {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-icon-blue { background: #e8f1ff; color: var(--color-blue); }
.action-icon-green { background: #e7f4f2; color: var(--color-primary); }
.action-icon-yellow { background: #fff7db; color: var(--color-amber); }

.action-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.action-desc {
  font-size: 12px;
  color: var(--color-text-muted);
}

.action-arrow {
  color: #c6d0dd;
  flex-shrink: 0;
}

.action-item:hover .action-arrow {
  color: var(--color-primary);
}

/* 待处理事项 */
.pending-card {
  padding: 20px;
}

.empty-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--color-text-muted);
}

.empty-pending p {
  font-size: 14px;
  margin: 0;
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pending-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 14px;
  border-radius: var(--radius-card);
  background: var(--color-surface-soft);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.pending-item:hover {
  background: #fff;
  border-color: var(--color-primary);
}

.pending-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.pending-screening { background: #fff7db; color: var(--color-amber); }
.pending-interview { background: #e8f1ff; color: var(--color-blue); }
.pending-risk { background: #feecec; color: var(--color-red); }

.pending-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pending-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.pending-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 响应式 */
@media (max-width: 1200px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }

  .header-actions {
    flex-direction: column;
  }
}
</style>
