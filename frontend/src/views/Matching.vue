<template>
  <div class="min-h-screen bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-8">
    <div class="max-w-6xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">Your Suggested Clique</h1>
        <p class="text-gray-600">Select 2 people to create your pod (you'll be the 3rd member)</p>
      </div>

      <MatchResults
        :matches="matches"
        :selected-matches="selectedMatches"
        :loading="loading"
        @toggle="toggleMatch"
      />

      <CreatePodButton
        :selected-count="selectedMatches.length"
        :loading="creatingPod"
        @create="handleCreatePod"
      />

      <div v-if="errorMessage" class="mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import MatchResults from '@/components/matching/MatchResults.vue'
import CreatePodButton from '@/components/matching/CreatePodButton.vue'

const router = useRouter()
const authStore = useAuthStore()

const matches = ref([])
const selectedMatches = ref([])
const loading = ref(false)
const creatingPod = ref(false)
const errorMessage = ref('')
const matchType = ref('')
const focusText = ref('')

onMounted(async () => {
  // Check if we have onboarding data
  const storedMatchType = sessionStorage.getItem('onboarding_match_type')
  const storedFocusText = sessionStorage.getItem('onboarding_focus_text')

  if (storedMatchType && storedFocusText) {
    matchType.value = storedMatchType
    focusText.value = storedFocusText
    await fetchMatches()
    // Clear session storage
    sessionStorage.removeItem('onboarding_match_type')
    sessionStorage.removeItem('onboarding_focus_text')
  } else {
    // If no onboarding data, redirect to onboarding
    router.push('/onboarding')
  }
})

async function fetchMatches() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await api.post('/matching/find', {
      match_type: matchType.value,
      focus_text: focusText.value,
    })

    matches.value = response.data.matches || []
  } catch (error) {
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to fetch matches. Please try again.'
  } finally {
    loading.value = false
  }
}

function toggleMatch(userId) {
  const index = selectedMatches.value.indexOf(userId)
  if (index > -1) {
    selectedMatches.value.splice(index, 1)
  } else {
    if (selectedMatches.value.length < 2) {
      selectedMatches.value.push(userId)
    }
  }
}

async function handleCreatePod() {
  if (selectedMatches.value.length !== 2) {
    return
  }

  creatingPod.value = true
  errorMessage.value = ''

  try {
    // API expects exactly 3 member_ids including the requester
    // So we need: current user + 2 selected matches = 3 total
    const currentUserId = authStore.user?._id || authStore.user?.id
    if (!currentUserId) {
      throw new Error('User not found')
    }

    // Take first 2 selected matches (current user makes 3rd)
    const selectedMemberIds = selectedMatches.value.slice(0, 2)
    const memberIds = [...selectedMemberIds, currentUserId]

    const response = await api.post('/matching/create-pod', {
      match_type: matchType.value,
      member_ids: memberIds,
    })

    const podId = response.data.pod?._id || response.data.pod?.id
    if (podId) {
      router.push(`/pod/${podId}`)
    } else {
      throw new Error('Pod created but ID not found')
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to create pod. Please try again.'
  } finally {
    creatingPod.value = false
  }
}
</script>

