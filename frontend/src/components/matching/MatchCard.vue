<template>
  <Card
    :class="[
      'relative overflow-hidden transition-all',
      isSelected ? 'ring-4 ring-primary bg-primary/5' : 'hover:shadow-lg'
    ]"
  >
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <h3 class="text-xl font-bold text-gray-800 mb-1">{{ match.username }}</h3>
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium text-primary">
            {{ similarityPercentage }}% match
          </span>
          <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-300"
              :style="{ width: `${similarityPercentage}%` }"
            ></div>
          </div>
        </div>
      </div>
      <label class="flex items-center cursor-pointer ml-4">
        <input
          type="checkbox"
          :checked="isSelected"
          @change="$emit('toggle')"
          class="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
        />
      </label>
    </div>

    <div class="mt-4">
      <p class="text-sm text-gray-600 line-clamp-3">
        {{ match.matching_preferences?.current_focus_text || 'No focus text available' }}
      </p>
    </div>

    <div
      v-if="isSelected"
      class="absolute top-2 right-2 bg-primary text-white rounded-full p-1"
    >
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
          clip-rule="evenodd"
        />
      </svg>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card from '@/components/common/Card.vue'

const props = defineProps({
  match: {
    type: Object,
    required: true,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle'])

const similarityPercentage = computed(() => {
  const score = props.match.similarity_score || 0
  return Math.round(score * 100)
})
</script>

