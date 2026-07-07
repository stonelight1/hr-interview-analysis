<template>
  <div class="animated-section" :class="{ 'is-visible': isVisible }" :style="sectionStyle">
    <slot />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  /** 出现延迟（秒），用于 stagger 效果 */
  delay: { type: Number, default: 0 },
  /** 动画类型 */
  animation: { type: String, default: 'slide-up', validator: v => ['slide-up', 'slide-left', 'fade'].includes(v) }
})

const isVisible = ref(false)
let observer = null

const sectionStyle = computed(() => ({
  transitionDelay: `${props.delay}s`
}))

onMounted(() => {
  // 使用 IntersectionObserver 实现滚动时可见才触发
  const el = document.querySelector('.animated-section') // fallback
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer?.disconnect()
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  )

  // 用 nextTick 确保 DOM 就绪
  const currentEl = document.querySelector(
    `.animated-section[style*="${props.delay}s"]`
  )
  if (currentEl) {
    observer.observe(currentEl)
  } else {
    // fallback：直接在挂载后短暂延迟显示
    const timer = setTimeout(() => {
      isVisible.value = true
    }, 100 + props.delay * 1000)
    onUnmounted(() => clearTimeout(timer))
  }
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.animated-section {
  opacity: 0;
  transition-property: opacity, transform;
  transition-duration: 0.6s;
  transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
}

/* slide-up（默认） */
.animated-section:not([class*="animation-"]) {
  transform: translateY(20px);
}
.animated-section:not([class*="animation-"]).is-visible {
  opacity: 1;
  transform: translateY(0);
}

/* slide-up */
.animated-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.animated-section:not(.is-visible) {
  transform: translateY(20px);
}

/* slide-left */
.animated-section[data-animation="slide-left"]:not(.is-visible) {
  transform: translateX(-16px);
}
.animated-section[data-animation="slide-left"].is-visible {
  transform: translateX(0);
}

/* fade */
.animated-section[data-animation="fade"]:not(.is-visible) {
  transform: none;
}
.animated-section[data-animation="fade"].is-visible {
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  .animated-section {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
