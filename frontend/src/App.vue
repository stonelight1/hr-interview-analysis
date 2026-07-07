<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand" @click="goHome">
          <div class="brand-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="brand-text">
            <h1 class="brand-title">HR Interview AI</h1>
            <span class="brand-subtitle">招聘筛选与面试评估</span>
          </div>
        </div>

        <nav class="top-nav" aria-label="顶部导航">
          <button
            type="button"
            :class="['top-link', isActive('screening') ? 'top-link-active' : '']"
            @click="navigate('/screening')"
          >
            岗位初筛
          </button>
          <button
            type="button"
            :class="['top-link', isActive('candidates') ? 'top-link-active' : '']"
            @click="navigate('/candidates')"
          >
            候选人库
          </button>
          <button
            type="button"
            :class="['top-link', isActive('interviews') ? 'top-link-active' : '']"
            @click="navigate('/interviews')"
          >
            面试管理
          </button>

          <el-dropdown trigger="click" @command="navigate">
            <button type="button" :class="['top-link more-trigger', isActive('more') ? 'top-link-active' : '']">
              更多功能
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/reports">报告中心</el-dropdown-item>
                <el-dropdown-item command="/jobs">岗位库</el-dropdown-item>
                <el-dropdown-item command="/resume-records">简历解析记录</el-dropdown-item>
                <el-dropdown-item command="/settings?section=job-types">岗位类型配置</el-dropdown-item>
                <el-dropdown-item command="/settings?section=prompts">AI 提示词配置</el-dropdown-item>
                <el-dropdown-item command="/settings">系统设置</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <button type="button" class="user-avatar" aria-label="用户头像">HR</button>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown, Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const navigate = (to) => {
  if (!to) return
  router.push(to)
}

const isActive = (section) => {
  if (section === 'screening') return route.path === '/screening' || route.path === '/dashboard'
  if (section === 'candidates') return route.path.startsWith('/candidates')
  if (section === 'interviews') return route.path.startsWith('/interviews')
  if (section === 'more') {
    return route.path.startsWith('/reports') ||
      route.path.startsWith('/analysis') ||
      route.path.startsWith('/jobs') ||
      route.path.startsWith('/resume-records') ||
      route.path.startsWith('/settings')
  }
  return false
}

const goHome = () => {
  router.push('/screening')
}
</script>

<style>
:root {
  /* ====== 主色色阶 ====== */
  --color-primary-900: #064e3b;
  --color-primary-700: #047857;
  --color-primary: #0f766e;
  --color-primary-hover: #0b5f59;
  --color-primary-300: #6ee7b7;
  --color-primary-soft: #e7f4f2;
  --color-primary-50: #f0fdfa;

  /* ====== 语义色彩 ====== */
  --color-blue: #2563eb;
  --color-blue-soft: #e8f1ff;
  --color-green: #10b981;
  --color-green-soft: #ecfdf5;
  --color-amber: #f59e0b;
  --color-amber-soft: #fff7db;
  --color-red: #ef4444;
  --color-red-soft: #feecec;

  /* ====== 中性色阶（6级）====== */
  --color-gray-900: #0f172a;
  --color-gray-700: #334155;
  --color-gray-500: #64748b;
  --color-gray-300: #94a3b8;
  --color-gray-100: #e2e8f0;
  --color-gray-50: #f8fafc;

  /* ====== 语义映射 ====== */
  --color-bg: var(--color-gray-50);
  --color-surface: #ffffff;
  --color-surface-soft: var(--color-gray-50);
  --color-border: var(--color-gray-100);
  --color-border-strong: #cbd5e1;
  --color-text: var(--color-gray-900);
  --color-text-secondary: var(--color-gray-500);
  --color-text-muted: var(--color-gray-300);

  /* ====== 圆角（3级）====== */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-control: var(--radius-sm);
  --radius-card: var(--radius-md);

  /* ====== 阴影（3级）====== */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.10);
  --shadow-card: var(--shadow-sm), var(--shadow-md);

  /* ====== 间距（8px基础单位）====== */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  /* ====== 字号（7级）====== */
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 16px;
  --text-lg: 18px;
  --text-xl: 24px;
  --text-2xl: 32px;

  /* ====== 字重 ====== */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* ====== 响应式断点 ====== */
  --breakpoint-sm: 640px;
  --breakpoint-md: 900px;
  --breakpoint-lg: 1080px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  background: var(--color-bg);
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
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(14px);
}

.topbar-inner {
  max-width: 1320px;
  margin: 0 auto;
  height: 72px;
  padding: 0 var(--space-8);
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(360px, 1fr);
  align-items: center;
  gap: var(--space-6);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  user-select: none;
  min-width: 0;
}

.brand-icon {
  width: 38px;
  height: 38px;
  background: var(--color-primary);
  border-radius: var(--radius-sm);
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
  font-size: var(--text-md);
  font-weight: var(--font-bold);
  color: var(--color-text);
  line-height: 1.2;
  margin: 0;
  letter-spacing: 0;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.2;
  white-space: nowrap;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
}

.top-link {
  height: 36px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.top-link:hover,
.more-trigger:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.top-link-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: 800;
  cursor: default;
}

.app-main {
  min-height: calc(100vh - 72px);
  padding: var(--space-8) var(--space-8) 48px;
  max-width: 1320px;
  width: 100%;
  margin: 0 auto;
}

.page-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

/* ====== Element Plus 全局覆盖 ====== */

.el-tag {
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
}

.el-button {
  border-radius: var(--radius-control);
  font-weight: var(--font-semibold);
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
  font-weight: var(--font-bold);
}

.el-table .el-table__cell {
  padding: var(--space-3) 0;
}

.el-progress-bar__outer {
  background-color: var(--color-gray-100);
}

/* ====== 响应式 ====== */

@media (max-width: 920px) {
  .topbar-inner {
    height: auto;
    min-height: 72px;
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 14px 18px;
  }

  .top-nav {
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .top-link {
    flex: 0 0 auto;
  }

  .app-main {
    padding: var(--space-6) var(--space-4) 36px;
  }
}

@media (max-width: 640px) {
  .brand-subtitle {
    display: none;
  }

  .user-avatar {
    display: none;
  }
}
</style>
