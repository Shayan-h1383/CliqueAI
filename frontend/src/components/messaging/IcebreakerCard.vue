<template>
  <Card class="bg-gradient-to-br from-accent/10 to-secondary/10 border-2 border-accent/30">
    <div class="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4">
      <div class="text-4xl flex-shrink-0">💡</div>
      <div class="flex-1">
        <h3 class="text-lg font-bold text-gray-800 mb-2">Why you matched</h3>
        <p class="text-gray-700 leading-relaxed">{{ icebreaker }}</p>
      </div>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/common/Card.vue'

defineProps({
  icebreaker: {
    type: String,
    default: 'You all share common interests and goals!',
  },
})
</script>

