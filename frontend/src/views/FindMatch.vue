<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-12">
    <div class="w-full max-w-2xl">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Find your clique</h1>
        <p class="text-gray-600">I want to find my clique to:</p>
      </div>

      <!-- Goal selection -->
      <div class="grid grid-cols-3 gap-4 mb-8">
        <button
          v-for="g in goals"
          :key="g.id"
          type="button"
          :class="[
            'py-4 px-4 rounded-xl border-2 text-center transition-all',
            goal === g.id
              ? 'border-primary bg-primary/10 text-primary font-semibold'
              : 'border-gray-200 hover:border-primary/50 text-gray-700'
          ]"
          @click="goal = g.id"
        >
          <span class="text-2xl block mb-1">{{ g.icon }}</span>
          <span class="capitalize">{{ g.label }}</span>
        </button>
      </div>

      <form v-if="goal" class="space-y-6" @submit.prevent="submit">
        <!-- Area dropdown -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ areaLabel }}</label>
          <select
            v-model="area"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="">Select...</option>
            <option v-for="opt in areaOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <!-- Details -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Details</label>
          <textarea
            v-model="details"
            :placeholder="detailsPlaceholder"
            required
            maxlength="500"
            rows="4"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary resize-none"
          />
          <p class="text-sm text-gray-500 mt-1">{{ details.length }}/500</p>
        </div>

        <!-- Third field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ thirdFieldLabel }}</label>
          <input
            v-model="thirdField"
            type="text"
            :placeholder="thirdFieldPlaceholder"
            required
            maxlength="100"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          />
          <p class="text-sm text-gray-500 mt-1">{{ thirdField.length }}/100</p>
          <p v-if="descriptionWordCount < minDescriptionWords" class="text-sm text-amber-600 mt-1">
            Add a bit more detail ({{ descriptionWordCount }}/{{ minDescriptionWords }} words in details + summary) so we can find better matches.
          </p>
        </div>

        <!-- City -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">City</label>
          <input
            v-model="city"
            type="text"
            placeholder="e.g. New York"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          />
        </div>

        <div v-if="errorMessage" class="text-red-600 text-sm">{{ errorMessage }}</div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-lg font-semibold text-white bg-primary hover:bg-primary/90 disabled:opacity-50"
        >
          {{ loading ? 'Submitting...' : 'Submit application' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const goals = [
  { id: 'evolve', label: 'Evolve', icon: '🌱' },
  { id: 'enjoy', label: 'Enjoy', icon: '🎯' },
  { id: 'support', label: 'Support', icon: '💙' },
]

const minDescriptionWords = 15

const goal = ref('')
const area = ref('')
const details = ref('')
const thirdField = ref('')
const city = ref('')
const loading = ref(false)
const errorMessage = ref('')

const descriptionWordCount = computed(() => {
  const combined = `${(details.value || '').trim()} ${(thirdField.value || '').trim()}`
  return combined ? combined.split(/\s+/).filter(Boolean).length : 0
})

const evolveAreas = ['studies', 'business', 'arts development', 'sports', 'general']
const enjoyAreas = ['gaming', 'content', 'humour', 'hiking', 'camping', 'sports']
const supportAreas = ['addiction', 'relationship', 'grief', 'illness', 'general depression', 'other']

const areaOptions = computed(() => {
  if (goal.value === 'evolve') return evolveAreas
  if (goal.value === 'enjoy') return enjoyAreas
  if (goal.value === 'support') return supportAreas
  return []
})

const areaLabel = computed(() => {
  if (goal.value === 'evolve') return 'Specify the area of your development'
  if (goal.value === 'enjoy') return "Specify your number 1 area of interests / hobbies"
  if (goal.value === 'support') return 'Specify the area of your struggles'
  return 'Area'
})

const detailsPlaceholder = computed(() => {
  if (goal.value === 'evolve') {
    const m = {
      studies: 'What are you studying, and at which level? Be specific.',
      business: 'How are you providing value to the world?',
      'arts development': "What is the art (e.g. music, painting) and what are the topics (genres) you're focused on?",
      sports: "What is the one sport you're the most focused on?",
      general: "Just write what you have to evolve in.",
    }
    return m[area.value] || 'Tell us about your development area.'
  }
  if (goal.value === 'enjoy') return 'Share a bit about your interests and how you like to spend time (up to 500 characters).'
  if (goal.value === 'support') {
    const m = {
      addiction: 'Specify what you are battling (e.g. gambling, drugs, alcoholism).',
      relationship: 'e.g. cheating, toxicity, or something else.',
      grief: 'Share what you feel comfortable sharing.',
      illness: 'Share what you feel comfortable sharing.',
      'general depression': 'Share what you feel comfortable sharing.',
      other: 'Describe your situation.',
    }
    return m[area.value] || 'Explain your struggles (up to 500 characters).'
  }
  return 'Details'
})

const thirdFieldLabel = computed(() => {
  if (goal.value === 'evolve') return 'Your goal'
  if (goal.value === 'enjoy') return 'How do you plan to enjoy your time together?'
  if (goal.value === 'support') return 'Resolution / Redemption'
  return 'Summary'
})

const thirdFieldPlaceholder = computed(() => {
  if (goal.value === 'evolve') return 'A specific goal connected to your area of development (max 100 characters)'
  if (goal.value === 'enjoy') return 'e.g. gaming, hiking (max 100 characters)'
  if (goal.value === 'support') return 'How are you hoping to resolve your issues or what do you hope to get comfortable with? (max 100 characters)'
  return ''
})

watch(goal, () => {
  area.value = ''
  details.value = ''
  thirdField.value = ''
})

async function submit() {
  if (!goal.value || !area.value || !details.value.trim() || !thirdField.value.trim() || !city.value.trim()) {
    errorMessage.value = 'Please fill all fields.'
    return
  }
  if (descriptionWordCount.value < minDescriptionWords) {
    errorMessage.value = 'Please add a bit more detail about your situation and goal so we can find better matches.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await api.post('/applications', {
      goal: goal.value,
      area: area.value,
      details: details.value.trim(),
      third_field: thirdField.value.trim(),
      city: city.value.trim(),
    })
    router.push('/suggestions')
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || 'Submission failed.'
  } finally {
    loading.value = false
  }
}
</script>
