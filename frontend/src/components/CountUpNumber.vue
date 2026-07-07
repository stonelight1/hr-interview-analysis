<template>
  <span class="count-up-number" :style="{ color: finalColor }">{{ displayValue }}</span>
</template>

<script setup>
import { ref, watch, onMounted, computed, onUnmounted } from 'vue'

const props = defineProps({
  /** 目标数值 */
  target: { type: Number, default: 0 },
  /** 动画持续时间（毫秒） */
  duration: { type: Number, default: 1200 },
  /** 小数位数 */
  decimals: { type: Number, default: 0 },
  /** 颜色映射函数，传入 (value, target) 返回颜色字符串 */
  colorFn: { type: Function, default: null },
  /** 是否立即开始（否则等 start 触发） */
  autoStart: { type: Boolean, default: true }
})

const displayValue = ref(0)
const isRunning = ref(false)
let animationFrame = null

const finalColor = computed(() => {
  if (!props.colorFn) return undefined
  return props.colorFn(props.target, props.target)
})

const currentColor = computed(() => {
  if (!props.colorFn) return undefined
  return props.colorFn(displayValue.value, props.target)
})

const startAnimation = () => {
  if (isRunning.value) return
  isRunning.value = true

  const startTime = performance.now()
  const startValue = displayValue.value
  const targetValue = props.target
  const durationMs = props.duration

  const animate = (now) => {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / durationMs, 1)

    // ease-out-expo 缓动
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)

    const current = startValue + (targetValue - startValue) * eased
    displayValue.value = Number(current.toFixed(props.decimals))

    if (progress < 1) {
      animationFrame = requestAnimationFrame(animate)
    } else {
      displayValue.value = targetValue
      isRunning.value = false
    }
  }

  animationFrame = requestAnimationFrame(animate)
}

const stopAnimation = () => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
    animationFrame = null
  }
  isRunning.value = false
  displayValue.value = props.target
}

watch(() => props.target, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    stopAnimation()
    if (props.autoStart) {
      displayValue.value = 0
      startAnimation()
    }
  }
})

onMounted(() => {
  if (props.autoStart) {
    displayValue.value = 0
    // 短暂延迟让页面先渲染
    const timer = setTimeout(startAnimation, 200)
    onUnmounted(() => clearTimeout(timer))
  } else {
    displayValue.value = 0
  }
})

onUnmounted(() => {
  stopAnimation()
})

// 暴露方法供父组件手动触发
defineExpose({ start: startAnimation, stop: stopAnimation })
</script>

<style scoped>
.count-up-number {
  display: inline-block;
  transition: color 0.3s ease;
}
</style>
