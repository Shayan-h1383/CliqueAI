<template>
  <div class="flex flex-col h-full">
    <!-- Header with Leave Pod button -->
    <div class="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
      <h2 class="text-xl font-bold text-gray-800">Pod Chat</h2>
      <Button
        variant="outline"
        size="sm"
        @click="$emit('leave')"
      >
        Leave Pod
      </Button>
    </div>

    <!-- Timer -->
    <div class="px-4 py-4">
      <PodTimer :expires-at="pod.expires_at" />
    </div>

    <!-- Icebreaker -->
    <div class="px-4 pb-4">
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
import PodTimer from './PodTimer.vue'
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

