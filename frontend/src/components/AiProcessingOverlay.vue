<template>
  <Transition name="ai-overlay">
    <div v-if="visible" class="ai-processing-overlay" @click.self="$emit('clickOutside')">
      <div class="ai-overlay-card">
        <!-- AI 图标 + 旋转光环 -->
        <div class="ai-icon-wrapper">
          <div class="ai-ring"></div>
          <div class="ai-icon-inner">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="ai-svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>

        <!-- 标题 -->
        <p class="ai-overlay-title">{{ title || 'AI 正在分析' }}</p>

        <!-- 动态阶段文字 -->
        <p class="ai-overlay-stage" :key="currentStageText">{{ currentStageText }}</p>

        <!-- 进度条 -->
        <div class="ai-overlay-progress" v-if="showProgress">
          <div class="ai-progress-bar" :style="{ width: progressPercent + '%' }">
            <div class="ai-progress-shimmer"></div>
          </div>
        </div>

        <!-- 底部提示 -->
        <p class="ai-overlay-hint" v-if="hint">{{ hint }}</p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  stages: { type: Array, default: () => [] },
  progress: { type: Number, default: 0 },
  showProgress: { type: Boolean, default: true },
  hint: { type: String, default: '' }
})

defineEmits(['clickOutside'])

const currentStageIndex = ref(0)
let stageTimer = null

const currentStageText = computed(() => {
  if (props.stages.length === 0) return '处理中...'
  return props.stages[currentStageIndex.value] || props.stages[props.stages.length - 1]
})

const progressPercent = computed(() => {
  return Math.min(100, Math.max(0, props.progress))
})

watch(() => props.visible, (val) => {
  if (val && props.stages.length > 1) {
    currentStageIndex.value = 0
    startStageRotation()
  } else {
    stopStageRotation()
  }
})

watch(() => props.progress, (val) => {
  // 进度到100时停止阶段轮换
  if (val >= 100) {
    stopStageRotation()
  }
})

const startStageRotation = () => {
  stopStageRotation()
  stageTimer = setInterval(() => {
    if (currentStageIndex.value < props.stages.length - 1) {
      currentStageIndex.value++
    }
  }, 3000)
}

const stopStageRotation = () => {
  if (stageTimer) {
    clearInterval(stageTimer)
    stageTimer = null
  }
}

onUnmounted(() => {
  stopStageRotation()
})
</script>

<style scoped>
.ai-processing-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.36);
  backdrop-filter: blur(6px);
}

.ai-overlay-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 48px 32px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  min-width: 320px;
  max-width: 420px;
}

/* AI 图标区域 */
.ai-icon-wrapper {
  position: relative;
  width: 72px;
  height: 72px;
  margin-bottom: 20px;
}

.ai-icon-inner {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: var(--radius-lg);
  background: var(--ai-pulse-color);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ai-pulse 2.4s ease-in-out infinite;
  z-index: 1;
}

.ai-svg {
  width: 36px;
  height: 36px;
  color: #ffffff;
}

/* 旋转光环 */
.ai-ring {
  position: absolute;
  inset: -6px;
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  border-top-color: var(--ai-pulse-color);
  border-right-color: var(--ai-pulse-color);
  animation: ai-ring-spin 1.6s linear infinite;
  opacity: 0.45;
}

/* 标题 */
.ai-overlay-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: 0;
}

/* 动态阶段文字 */
.ai-overlay-stage {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: opacity 0.3s ease;
  text-align: center;
}

/* 进度条 */
.ai-overlay-progress {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--color-gray-100);
  overflow: hidden;
  margin-bottom: 14px;
}

.ai-progress-bar {
  height: 100%;
  border-radius: 2px;
  background: var(--ai-pulse-color);
  transition: width 0.5s var(--ease-out-expo);
  position: relative;
  overflow: hidden;
}

.ai-progress-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: progress-shimmer 1.8s infinite;
}

/* 底部提示 */
.ai-overlay-hint {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ============ 过渡动画 ============ */
.ai-overlay-enter-active {
  transition: opacity 0.3s ease;
}
.ai-overlay-enter-active .ai-overlay-card {
  transition: opacity 0.3s ease, transform 0.3s var(--ease-out-expo);
}

.ai-overlay-leave-active {
  transition: opacity 0.25s ease;
}
.ai-overlay-leave-active .ai-overlay-card {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.ai-overlay-enter-from {
  opacity: 0;
}
.ai-overlay-enter-from .ai-overlay-card {
  opacity: 0;
  transform: scale(0.92) translateY(8px);
}

.ai-overlay-leave-to {
  opacity: 0;
}
.ai-overlay-leave-to .ai-overlay-card {
  opacity: 0;
  transform: scale(0.96) translateY(4px);
}

@media (prefers-reduced-motion: reduce) {
  .ai-icon-inner {
    animation: none;
  }
  .ai-ring {
    animation: none;
    opacity: 0;
  }
  .ai-overlay-enter-active,
  .ai-overlay-leave-active,
  .ai-overlay-enter-active .ai-overlay-card,
  .ai-overlay-leave-active .ai-overlay-card {
    transition: none;
  }
}
</style>
