<template>
  <div class="space-y-6">
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div
        v-for="i in 4"
        :key="i"
        class="bg-gray-200 animate-pulse rounded-lg h-48"
      ></div>
    </div>

    <div v-else-if="matches.length === 0" class="text-center py-12">
      <p class="text-gray-600 text-lg">No matches found. Try adjusting your focus text.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <MatchCard
        v-for="match in matches"
        :key="match.user_id"
        :match="match"
        :is-selected="selectedMatches.includes(match.user_id)"
        @toggle="$emit('toggle', match.user_id)"
      />
    </div>
  </div>
</template>

<script setup>
import MatchCard from './MatchCard.vue'

defineProps({
  matches: {
    type: Array,
    default: () => [],
  },
  selectedMatches: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle'])
</script>

