<template>
  <div class="border-t border-gray-200 bg-white px-3 sm:px-4 py-3 sm:py-4 shrink-0">
    <form @submit.prevent="handleSend" class="flex flex-col gap-2">
      <div class="flex gap-2 sm:gap-3 items-center">
        <textarea
          v-model="messageText"
          :placeholder="placeholder"
          :maxlength="5000"
          rows="2"
          class="flex-1 min-w-0 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.exact="messageText += '\n'"
        ></textarea>
        <Button
          type="submit"
          variant="primary"
          :disabled="!canSend || sending"
          :loading="sending"
          class="shrink-0"
        >
          Send
        </Button>
      </div>
      <div class="flex justify-between items-center text-xs text-gray-500">
        <span>{{ characterCount }}/5000 characters</span>
        <span class="hidden sm:inline text-gray-400">Press Enter to send, Shift+Enter for new line</span>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Type your message...',
  },
})

const emit = defineEmits(['send'])

const messageText = ref('')
const sending = ref(false)

const characterCount = computed(() => messageText.value.length)

const canSend = computed(() => {
  return messageText.value.trim().length > 0 && characterCount.value <= 5000
})

async function handleSend() {
  if (!canSend.value || sending.value) {
    return
  }

  const text = messageText.value.trim()
  messageText.value = ''
  sending.value = true

  try {
    await emit('send', text)
  } finally {
    sending.value = false
  }
}
</script>

