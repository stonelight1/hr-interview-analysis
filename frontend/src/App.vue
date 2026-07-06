<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="brand" @click="goHome">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="brand-text">
            <h1 class="brand-title">HR 面试分析系统</h1>
            <span class="brand-subtitle">候选人匹配度与面试复盘助手</span>
          </div>
        </div>
        <nav class="app-nav">
          <router-link to="/jobs" class="nav-link" activeClass="nav-link-active">
            <el-icon><OfficeBuilding /></el-icon>
            <span>岗位管理</span>
          </router-link>
          <router-link to="/candidates" class="nav-link" activeClass="nav-link-active">
            <el-icon><User /></el-icon>
            <span>候选人管理</span>
          </router-link>
          <router-link to="/analysis/list" class="nav-link" activeClass="nav-link-active">
            <el-icon><Document /></el-icon>
            <span>历史记录</span>
          </router-link>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { OfficeBuilding, User, Document } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/jobs')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  background-color: #F5F7FB;
  color: #374151;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #E5E7EB;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.header-content {
  max-width: 1180px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.brand-icon svg {
  width: 20px;
  height: 20px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-title {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
  line-height: 1.2;
  margin: 0;
}

.brand-subtitle {
  font-size: 12px;
  color: #9CA3AF;
  line-height: 1.2;
}

.app-nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #6B7280;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #2563EB;
  background-color: #EFF6FF;
}

.nav-link-active {
  color: #2563EB;
  background-color: #EFF6FF;
}

.app-main {
  flex: 1;
  padding: 24px;
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
}

/* 全局卡片样式 */
.page-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid #F3F4F6;
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
  border-radius: 8px;
  font-weight: 500;
}

.el-button--primary {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border: none;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
}
</style>
