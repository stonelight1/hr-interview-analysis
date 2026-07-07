<template>
  <div class="question-placeholder">
    <div v-for="i in count" :key="i" class="placeholder-card" :style="{ animationDelay: `${i * 0.15}s` }">
      <div class="placeholder-icon">❓</div>
      <div class="placeholder-lines">
        <div class="placeholder-line line-long"></div>
        <div class="placeholder-line line-short"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 3 }
})
</script>

<style scoped>
.question-placeholder {
  display: grid;
  gap: 12px;
}

.placeholder-card {
  display: flex;
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  animation: blink-placeholder 1.8s ease-in-out infinite;
}

.placeholder-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-50);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.placeholder-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 4px;
}

.placeholder-line {
  height: 10px;
  border-radius: 5px;
  background: var(--color-gray-100);
}

.line-long {
  width: 80%;
}

.line-short {
  width: 50%;
}

@media (prefers-reduced-motion: reduce) {
  .placeholder-card {
    animation: none;
    opacity: 0.5;
  }
}
</style>
