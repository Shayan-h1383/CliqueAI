<template>
  <div class="text-center space-y-4 sm:space-y-6">
    <h1 class="text-3xl sm:text-4xl md:text-5xl font-bold text-primary mb-4">cliqueAI</h1>
    <p class="text-xl sm:text-2xl text-gray-700 font-medium">Stop Broadcasting. Start Connecting.</p>
    <p class="text-gray-600 max-w-md mx-auto text-sm sm:text-base px-2">
      Find your perfect clique of 3 people who share your interests, goals, or challenges. 
      Connect in focused 48-hour pods designed for meaningful conversations.
    </p>
    <Button
      variant="primary"
      size="lg"
      @click="$emit('next')"
      class="mt-8"
    >
      Get Started
    </Button>
  </div>
</template>

<script setup>
import Button from '@/components/common/Button.vue'

defineEmits(['next'])
</script>

