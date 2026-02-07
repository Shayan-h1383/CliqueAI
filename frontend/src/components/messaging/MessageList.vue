<template>
  <div
    ref="messagesContainer"
    class="flex-1 overflow-y-auto space-y-4 px-4 py-6"
    style="max-height: calc(100vh - 400px);"
  >
    <div v-if="loading && messages.length === 0" class="text-center text-gray-500 py-8">
      Loading messages...
    </div>

    <div v-else-if="messages.length === 0" class="text-center text-gray-500 py-8">
      No messages yet. Start the conversation!
    </div>

    <div
      v-for="message in messages"
      :key="message._id || message.id"
      :class="[
        'flex',
        isOwnMessage(message) ? 'justify-end' : 'justify-start'
      ]"
    >
      <div
        :class="[
          'max-w-xs md:max-w-md px-4 py-2 rounded-lg',
          isOwnMessage(message) 
            ? 'bg-primary text-white rounded-br-none' 
            : 'bg-gray-200 text-gray-800 rounded-bl-none'
        ]"
      >
        <div v-if="!isOwnMessage(message)" class="text-xs font-semibold mb-1 opacity-75">
          {{ getSenderName(message) }}
        </div>
        <div class="text-sm whitespace-pre-wrap break-words">{{ message.content }}</div>
        <div :class="['text-xs mt-1', isOwnMessage(message) ? 'opacity-75' : 'text-gray-500']">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  podMembers: {
    type: Array,
    default: () => [],
  },
})

const authStore = useAuthStore()
const messagesContainer = ref(null)

function isOwnMessage(message) {
  const currentUserId = authStore.user?._id || authStore.user?.id
  const senderId = message.sender_id?._id || message.sender_id || message.sender_id
  return String(senderId) === String(currentUserId)
}

function getSenderName(message) {
  // Try to get username from podMembers or message
  if (message.sender_username) {
    return message.sender_username
  }
  // For now, just return "User" if we can't find the name
  return 'User'
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) {
    return 'Just now'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}m ago`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}h ago`
  } else {
    return date.toLocaleDateString()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, () => {
  scrollToBottom()
})

onMounted(() => {
  scrollToBottom()
})
</script>

