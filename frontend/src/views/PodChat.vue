<template>
  <div class="min-h-screen bg-gray-50">
    <div v-if="loading && !pod" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-gray-600">Loading pod...</p>
      </div>
    </div>

    <div v-else-if="errorMessage" class="flex items-center justify-center min-h-screen px-4">
      <Card class="max-w-md w-full text-center">
        <p class="text-red-600 mb-4">{{ errorMessage }}</p>
        <Button variant="primary" @click="$router.push('/dashboard')">
          Go to Dashboard
        </Button>
      </Card>
    </div>

    <div v-else-if="pod" class="max-w-4xl mx-auto bg-white min-h-screen flex flex-col">
      <PodView
        :pod="pod"
        :messages="messages"
        :pod-members="podMembers"
        :loading="loadingMessages"
        @send="handleSendMessage"
        @leave="handleLeavePod"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePodStore } from '@/stores/pod'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { useInterval } from '@vueuse/core'
import PodView from '@/components/messaging/PodView.vue'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

const route = useRoute()
const router = useRouter()
const podStore = usePodStore()
const authStore = useAuthStore()

const pod = ref(null)
const messages = ref([])
const podMembers = ref([])
const loading = ref(true)
const loadingMessages = ref(false)
const errorMessage = ref('')
const podId = route.params.pod_id

// Poll messages every 4 seconds (paused until mounted, cleared on unmount)
const { pause: pausePolling, resume: resumePolling } = useInterval(4000, {
  callback: async () => {
    if (route.params.pod_id) await fetchMessages()
  },
  controls: true,
  immediate: false,
})

onMounted(async () => {
  await fetchPod()
  await fetchMessages()
  resumePolling()
})

onUnmounted(() => {
  pausePolling()
  pod.value = null
})

async function fetchPod() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await api.get(`/pods/${podId}`)
    pod.value = response.data.pod
    podStore.setActivePod(pod.value)
    
    // Extract member IDs
    if (pod.value.members) {
      podMembers.value = pod.value.members
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to load pod'
    console.error('Failed to fetch pod:', error)
  } finally {
    loading.value = false
  }
}

async function fetchMessages() {
  loadingMessages.value = true

  try {
    const response = await api.get(`/messages/${podId}`)
    messages.value = response.data.messages || []
  } catch (error) {
    console.error('Failed to fetch messages:', error)
    // Don't show error for polling failures, just log them
  } finally {
    loadingMessages.value = false
  }
}

async function handleSendMessage(content) {
  try {
    const response = await api.post('/messages/send', {
      pod_id: podId,
      content: content,
    })

    // Add new message to list
    if (response.data.message) {
      messages.value.push(response.data.message)
    } else {
      // If message not returned, refresh messages
      await fetchMessages()
    }
  } catch (error) {
    console.error('Failed to send message:', error)
    alert(error.response?.data?.error || error.message || 'Failed to send message')
  }
}

async function handleLeavePod() {
  if (!confirm('Are you sure you want to leave this pod? This action cannot be undone.')) {
    return
  }

  try {
    await podStore.leavePod(podId)
    router.push('/matching')
  } catch (error) {
    console.error('Failed to leave pod:', error)
    alert(error.response?.data?.error || error.message || 'Failed to leave pod')
  }
}
</script>

