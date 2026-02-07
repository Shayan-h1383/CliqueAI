<template>
  <div class="min-h-screen bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-8">
    <div class="max-w-4xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">
          Welcome{{ authStore.user?.username ? `, ${authStore.user.username}` : '' }}!
        </h1>
        <p class="text-gray-600">Your cliqueAI dashboard</p>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p class="text-gray-600">Loading...</p>
        </div>
      </div>

      <div v-else-if="activePod" class="space-y-6">
        <Card>
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-2xl font-bold text-gray-800 mb-2">Active Pod</h2>
              <p class="text-gray-600">
                Type: <span class="font-semibold capitalize">{{ activePod.pod_type }}</span>
              </p>
              <p class="text-sm text-gray-500 mt-2">
                Created: {{ formatDate(activePod.created_at) }}
              </p>
            </div>
            <Button variant="primary" size="lg" @click="goToPod">
              Open Pod
            </Button>
          </div>
        </Card>

        <Card v-if="activePod.gemini_icebreaker" class="bg-gradient-to-br from-accent/10 to-secondary/10">
          <h3 class="text-lg font-bold text-gray-800 mb-2">Why you matched</h3>
          <p class="text-gray-700">{{ activePod.gemini_icebreaker }}</p>
        </Card>
      </div>

      <div v-else class="text-center space-y-6">
        <Card class="max-w-md mx-auto">
          <div class="py-8">
            <div class="text-6xl mb-4">👥</div>
            <h2 class="text-2xl font-bold text-gray-800 mb-4">No Active Pod</h2>
            <p class="text-gray-600 mb-6">
              Start connecting with others by finding your perfect clique!
            </p>
            <Button variant="primary" size="lg" @click="goToMatching">
              Find Your Clique
            </Button>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePodStore } from '@/stores/pod'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const authStore = useAuthStore()
const podStore = usePodStore()

const activePod = ref(null)
const loading = ref(true)

onMounted(async () => {
  await fetchActivePod()
})

async function fetchActivePod() {
  loading.value = true
  try {
    const pod = await podStore.fetchActivePod()
    activePod.value = pod
  } catch (error) {
    console.error('Failed to fetch active pod:', error)
    activePod.value = null
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function goToPod() {
  if (activePod.value?._id || activePod.value?.id) {
    const podId = activePod.value._id || activePod.value.id
    router.push(`/pod/${podId}`)
  }
}

function goToMatching() {
  router.push('/matching')
}
</script>

