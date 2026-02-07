<template>
  <div class="bg-gradient-to-r from-primary to-secondary text-white px-6 py-4 rounded-lg shadow-lg">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm opacity-90">Pod expires in</p>
        <p class="text-2xl font-bold">{{ formattedTime }}</p>
      </div>
      <div class="text-4xl">⏰</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  expiresAt: {
    type: String,
    required: true,
  },
})

const formattedTime = ref('')
let intervalId = null

function updateTimer() {
  const now = new Date()
  const expires = new Date(props.expiresAt)
  const diff = expires - now

  if (diff <= 0) {
    formattedTime.value = 'Expired'
    if (intervalId) {
      clearInterval(intervalId)
    }
    return
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  const parts = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  if (parts.length === 0) parts.push(`${seconds}s`)

  formattedTime.value = parts.join(' ')
}

onMounted(() => {
  updateTimer()
  intervalId = setInterval(updateTimer, 1000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

