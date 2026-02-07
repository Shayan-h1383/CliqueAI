<template>
  <div class="border-t border-gray-200 bg-white px-4 py-4">
    <form @submit.prevent="handleSend" class="flex items-end space-x-3">
      <div class="flex-1">
        <textarea
          v-model="messageText"
          :placeholder="placeholder"
          :maxlength="5000"
          rows="2"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.exact="messageText += '\n'"
        ></textarea>
        <div class="flex justify-between items-center mt-1">
          <p class="text-xs text-gray-500">
            {{ characterCount }}/5000 characters
          </p>
          <p class="text-xs text-gray-400">Press Enter to send, Shift+Enter for new line</p>
        </div>
      </div>
      <Button
        type="submit"
        variant="primary"
        :disabled="!canSend || sending"
        :loading="sending"
      >
        Send
      </Button>
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

