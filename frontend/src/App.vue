<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand" @click="goHome">
        <div class="brand-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="brand-text">
          <h1 class="brand-title">HR Interview AI</h1>
          <span class="brand-subtitle">招聘筛选与面试评估</span>
        </div>
      </div>

      <nav class="app-nav" aria-label="主导航">
        <button
          v-for="item in navItems"
          :key="item.label"
          type="button"
          :class="['nav-link', isActive(item) ? 'nav-link-active' : '']"
          @click="navigate(item.to)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </aside>

    <div class="app-workspace">
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import {
  Odometer, OfficeBuilding, User, Search, ChatLineRound, Document
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 导航项：match 函数手动比较 path 和 query.status，做到精确高亮
const navItems = [
  { label: '工作台', icon: Odometer, to: '/dashboard',
    match: () => route.path === '/dashboard' },
  { label: '岗位管理', icon: OfficeBuilding, to: '/jobs',
    match: () => route.path.startsWith('/jobs') },
  { label: '候选人管理', icon: User, to: '/candidates',
    match: () => route.path.startsWith('/candidates') && !route.query.status },
  { label: '简历筛选', icon: Search, to: '/candidates?status=RESUME_PENDING',
    match: () => route.path === '/candidates' && route.query.status === 'RESUME_PENDING' },
  { label: '面试评估', icon: ChatLineRound, to: '/candidates?status=FIRST_INTERVIEW_PASSED',
    match: () => route.path === '/candidates' && route.query.status === 'FIRST_INTERVIEW_PASSED' },
  { label: '历史报告', icon: Document, to: '/analysis/list',
    match: () => route.path.startsWith('/analysis') }
]

const isActive = (item) => item.match()

const navigate = (to) => {
  router.push(to)
}

const goHome = () => {
  router.push('/dashboard')
}
</script>

<style>
:root {
  --color-bg: #f4f6f8;
  --color-surface: #ffffff;
  --color-surface-soft: #f8fafc;
  --color-border: #e3e8ef;
  --color-border-strong: #cfd8e3;
  --color-text: #172033;
  --color-text-secondary: #5f6f86;
  --color-text-muted: #91a0b5;
  --color-primary: #0f766e;
  --color-primary-hover: #0b5f59;
  --color-primary-soft: #e7f4f2;
  --color-blue: #2563eb;
  --color-green: #059669;
  --color-amber: #d97706;
  --color-red: #dc2626;
  --shadow-card: 0 1px 2px rgba(16, 24, 40, 0.04), 0 10px 24px rgba(16, 24, 40, 0.04);
  --radius-card: 8px;
  --radius-control: 8px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

button,
input,
textarea,
select {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr);
}

.app-sidebar {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px 16px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.brand-icon {
  width: 40px;
  height: 40px;
  background: #0f766e;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
  margin: 0;
  letter-spacing: 0;
}

.brand-subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.2;
  white-space: nowrap;
}

.app-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;
  text-align: left;
}

.nav-link:hover {
  color: var(--color-text);
  background: var(--color-surface-soft);
}

.nav-link-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.app-workspace {
  min-width: 0;
}

.app-main {
  min-height: 100vh;
  padding: 28px 32px 40px;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
}

/* 全局卡片样式 */
.page-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.page-card + .page-card {
  margin-top: 20px;
}

/* 全局标签样式覆盖 */
.el-tag {
  border-radius: 6px;
  font-weight: 500;
}

/* 按钮样式微调 */
.el-button {
  border-radius: var(--radius-control);
  font-weight: 500;
}

.el-button--primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.el-button--primary:hover,
.el-button--primary:focus {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.el-button.is-plain:hover,
.el-button.is-plain:focus {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner,
.el-input-number .el-input__wrapper {
  border-radius: var(--radius-control);
  box-shadow: 0 0 0 1px var(--color-border) inset;
}

.el-input__wrapper:hover,
.el-select__wrapper:hover,
.el-textarea__inner:hover {
  box-shadow: 0 0 0 1px var(--color-border-strong) inset;
}

.el-input__wrapper.is-focus,
.el-select__wrapper.is-focused,
.el-textarea__inner:focus {
  box-shadow: 0 0 0 1px var(--color-primary) inset, 0 0 0 3px var(--color-primary-soft);
}

.el-table {
  --el-table-header-bg-color: var(--color-surface-soft);
  --el-table-header-text-color: var(--color-text);
  --el-table-text-color: var(--color-text-secondary);
  --el-table-border-color: var(--color-border);
  color: var(--color-text-secondary);
}

.el-table th.el-table__cell {
  font-weight: 700;
}

.el-table .el-table__cell {
  padding: 11px 0;
}

.el-progress-bar__outer {
  background-color: #e8edf3;
}

@media (max-width: 1080px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    position: sticky;
    height: auto;
    gap: 14px;
    padding: 14px 16px 12px;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .app-nav {
    flex-direction: row;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .nav-link {
    width: auto;
    flex: 0 0 auto;
    height: 38px;
    padding: 0 12px;
    white-space: nowrap;
  }

  .nav-link-active {
    box-shadow: inset 0 -3px 0 var(--color-primary);
  }

  .app-main {
    padding: 22px 18px 32px;
  }
}

@media (max-width: 640px) {
  .brand-subtitle {
    display: none;
  }

  .app-sidebar {
    gap: 12px;
  }

  .app-main {
    padding: 18px 14px 28px;
  }
}
</style>
