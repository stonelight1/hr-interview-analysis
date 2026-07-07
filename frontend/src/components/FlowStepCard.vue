<template>
  <div class="flow-step-card" :class="stepClass">
    <div class="step-indicator">
      <!-- pending: 灰色数字 -->
      <template v-if="status === 'pending'">
        <span class="step-number">{{ index }}</span>
      </template>
      <!-- active: 脉冲数字 -->
      <template v-if="status === 'active'">
        <span class="step-number step-number-active">{{ index }}</span>
        <div class="step-pulse-ring"></div>
      </template>
      <!-- done: 确认标记 -->
      <template v-if="status === 'done'">
        <span class="step-check">✓</span>
      </template>
    </div>
    <div class="step-content">
      <strong class="step-title">{{ title }}</strong>
      <p class="step-desc">{{ desc }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  index: { type: Number, required: true },
  title: { type: String, required: true },
  desc: { type: String, default: '' },
  status: { type: String, default: 'pending', validator: v => ['pending', 'active', 'done'].includes(v) }
})

const stepClass = computed(() => ({
  [`step-${props.status}`]: true
}))
</script>

<style scoped>
.flow-step-card {
  min-height: 126px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  border: 1px solid var(--color-border);
  transition: border-color 0.4s ease, background-color 0.4s ease, transform 0.3s var(--ease-out-expo);
}

/* ============ 步骤指示器 ============ */
.step-indicator {
  position: relative;
  width: 28px;
  height: 28px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-number {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--color-gray-100);
  color: var(--color-gray-700);
  font-weight: var(--font-bold);
  font-size: 13px;
  z-index: 1;
}

.step-number-active {
  background: var(--ai-pulse-color);
  color: var(--color-surface);
  animation: ai-pulse 2.4s ease-in-out infinite;
}

.step-pulse-ring {
  position: absolute;
  inset: -4px;
  border-radius: 999px;
  border: 2px solid var(--ai-pulse-color);
  opacity: 0.3;
  animation: ai-pulse 2.4s ease-in-out infinite;
  animation-delay: 0.12s;
}

.step-check {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--ai-pulse-color);
  color: var(--color-surface);
  font-weight: var(--font-bold);
  font-size: 14px;
  animation: check-pop 0.5s var(--ease-spring);
}

/* ============ 内容 ============ */
.step-content strong {
  display: block;
  font-size: 14px;
  color: var(--color-text);
  transition: color 0.3s ease;
}

.step-content p {
  margin: 7px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
  transition: color 0.3s ease;
}

/* ============ 三态样式 ============ */

/* pending */
.step-pending {
  border-color: var(--color-border);
  background: var(--color-gray-50);
}

/* active */
.step-active {
  border-color: var(--color-primary-300);
  background: var(--color-primary-50);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.12);
}

.step-active .step-content strong {
  color: var(--ai-pulse-color);
}

/* done */
.step-done {
  border-color: var(--color-primary-300);
  background: var(--color-primary-50);
}

.step-done .step-content strong {
  color: var(--color-text);
}

@media (prefers-reduced-motion: reduce) {
  .step-number-active,
  .step-pulse-ring {
    animation: none;
  }
  .step-check {
    animation: none;
  }
  .flow-step-card {
    transition: none;
  }
}
</style>
