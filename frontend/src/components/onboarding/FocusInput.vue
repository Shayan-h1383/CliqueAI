<template>
  <div class="space-y-6">
    <div class="text-center mb-6 sm:mb-8">
      <h2 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">Tell us about yourself</h2>
      <p class="text-gray-600">Help us find your perfect clique</p>
    </div>

    <div class="max-w-2xl mx-auto">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        {{ placeholderLabel }}
      </label>
      <textarea
        v-model="focusText"
        :placeholder="placeholder"
        :maxlength="500"
        rows="6"
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none text-lg"
        @input="handleInput"
      ></textarea>
      <div class="flex justify-between items-center mt-2">
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <p v-else class="text-sm text-gray-500">
          {{ characterCount }}/500 characters
        </p>
      </div>
    </div>

    <div class="flex justify-center mt-8">
      <Button
        variant="primary"
        size="lg"
        :disabled="!isValid"
        :loading="loading"
        @click="handleSubmit"
      >
        Find My Clique
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  matchType: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit'])

const focusText = ref('')
const error = ref('')

const placeholders = {
  evolve: "What are you working towards? (e.g., 'Building my first SaaS to $10k MRR')",
  enjoy: "What are you passionate about? (e.g., 'I love indie music and hiking')",
  support: "What are you struggling with? (e.g., 'Feeling overwhelmed by job search')",
}

const placeholder = computed(() => placeholders[props.matchType] || 'Tell us about yourself...')

const placeholderLabel = computed(() => {
  const labels = {
    evolve: 'What are you working towards?',
    enjoy: 'What are you passionate about?',
    support: 'What are you struggling with?',
  }
  return labels[props.matchType] || 'Tell us about yourself'
})

const characterCount = computed(() => focusText.value.length)

const isValid = computed(() => {
  return focusText.value.trim().length >= 10 && focusText.value.length <= 500
})

function handleInput() {
  error.value = ''
  
  if (focusText.value.length > 500) {
    error.value = 'Maximum 500 characters allowed'
  } else if (focusText.value.trim().length > 0 && focusText.value.trim().length < 10) {
    error.value = 'Please provide at least 10 characters'
  }
}

function handleSubmit() {
  if (!isValid.value) {
    if (focusText.value.trim().length < 10) {
      error.value = 'Please provide at least 10 characters'
    }
    return
  }
  
  emit('submit', focusText.value.trim())
}
</script>

