<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-12">
    <div class="w-full max-w-4xl">
      <WelcomeScreen
        v-if="currentStep === 1"
        @next="currentStep = 2"
      />
      
      <MatchTypeSelection
        v-if="currentStep === 2"
        v-model="matchType"
        @next="currentStep = 3"
      />
      
      <FocusInput
        v-if="currentStep === 3"
        :match-type="matchType"
        :loading="loading"
        @submit="handleFindMatches"
      />

      <div v-if="errorMessage" class="mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import WelcomeScreen from '@/components/onboarding/WelcomeScreen.vue'
import MatchTypeSelection from '@/components/onboarding/MatchTypeSelection.vue'
import FocusInput from '@/components/onboarding/FocusInput.vue'

const router = useRouter()

const currentStep = ref(1)
const matchType = ref('')
const focusText = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleFindMatches(text) {
  focusText.value = text
  loading.value = true
  errorMessage.value = ''

  try {
    // Call matching API
    const response = await api.post('/matching/find', {
      match_type: matchType.value,
      focus_text: focusText.value,
    })

    // Store matches in sessionStorage or pass via route state
    // For now, we'll navigate to matching page which will fetch matches
    // The matching page can use the stored match_type and focus_text
    sessionStorage.setItem('onboarding_match_type', matchType.value)
    sessionStorage.setItem('onboarding_focus_text', focusText.value)

    // Navigate to matching page
    router.push('/matching')
  } catch (error) {
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to find matches. Please try again.'
    loading.value = false
  }
}
</script>

