<template>
  <div class="flex flex-col flex-1 min-h-0">
    <!-- Header with Leave Pod button -->
    <div class="flex items-center justify-between px-3 sm:px-4 py-3 bg-white border-b border-gray-200 shrink-0">
      <h2 class="text-lg sm:text-xl font-bold text-gray-800">Pod Chat</h2>
      <Button
        variant="outline"
        size="sm"
        @click="$emit('leave')"
      >
        Leave Pod
      </Button>
    </div>

    <!-- Icebreaker -->
    <div class="px-3 sm:px-4 pb-4 shrink-0">
      <IcebreakerCard :icebreaker="pod.gemini_icebreaker || 'You all share common interests!'" />
    </div>

    <!-- Messages -->
    <MessageList
      :messages="messages"
      :loading="loading"
      :pod-members="podMembers"
    />

    <!-- Input -->
    <MessageInput
      placeholder="Type your message..."
      @send="handleSendMessage"
    />
  </div>
</template>

<script setup>
import IcebreakerCard from './IcebreakerCard.vue'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  pod: {
    type: Object,
    required: true,
  },
  messages: {
    type: Array,
    default: () => [],
  },
  podMembers: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['send', 'leave'])

function handleSendMessage(content) {
  emit('send', content)
}
</script>

