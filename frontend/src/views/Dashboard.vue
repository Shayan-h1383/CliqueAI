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

      <div v-else-if="pods.length > 0" class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">Your cliques</h2>
        <div
          v-for="pod in pods"
          :key="pod._id"
          class="space-y-4"
        >
          <Card>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-gray-600">
                  Type: <span class="font-semibold capitalize">{{ pod.pod_type }}</span>
                </p>
                <p class="text-sm text-gray-500 mt-2">
                  Created: {{ formatDate(pod.created_at) }}
                </p>
              </div>
              <Button variant="primary" size="lg" @click="goToPod(pod)">
                Open Pod
              </Button>
            </div>
            <div v-if="pod.gemini_icebreaker" class="mt-4 p-4 rounded-lg bg-gradient-to-br from-accent/10 to-secondary/10">
              <h3 class="text-lg font-bold text-gray-800 mb-2">Why you matched</h3>
              <p class="text-gray-700">{{ pod.gemini_icebreaker }}</p>
            </div>
          </Card>
        </div>
      </div>

      <div v-else class="text-center space-y-6">
        <Card class="max-w-md mx-auto">
          <div class="py-8">
            <div class="text-6xl mb-4">👥</div>
            <h2 class="text-2xl font-bold text-gray-800 mb-4">No cliques yet</h2>
            <p class="text-gray-600 mb-6">
              Submit a clique application or check your suggestions.
            </p>
            <div class="flex flex-col sm:flex-row gap-3 justify-center">
              <Button variant="primary" size="lg" @click="goToFindMatch">
                Find your clique
              </Button>
              <Button variant="outline" size="lg" @click="goToSuggestions">
                View suggestions
              </Button>
            </div>
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

const pods = ref([])
const loading = ref(true)

onMounted(async () => {
  await fetchMyPods()
})

async function fetchMyPods() {
  loading.value = true
  try {
    pods.value = await podStore.fetchMyPods()
  } catch (error) {
    console.error('Failed to fetch pods:', error)
    pods.value = []
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

function goToPod(pod) {
  const podId = pod?._id || pod?.id
  if (podId) router.push(`/pod/${podId}`)
}

function goToFindMatch() {
  router.push('/find-match')
}
function goToSuggestions() {
  router.push('/suggestions')
}
</script>

