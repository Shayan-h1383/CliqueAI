<template>
  <div class="min-h-screen bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-8">
    <div class="max-w-4xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">Clique invitations</h1>
        <p class="text-gray-600">Accept or reject clique invitations from others</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="invitations.length === 0" class="text-center py-12">
        <p class="text-gray-600 mb-4">You have no pending invitations.</p>
        <router-link
          to="/dashboard"
          class="inline-block py-3 px-6 rounded-lg font-semibold text-white bg-primary hover:bg-primary/90"
        >
          Find your clique
        </router-link>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="inv in invitations"
          :key="inv._id"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div class="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p class="font-semibold text-gray-800">{{ inv.inviter_username || 'Someone' }} wants to form a clique with you</p>
              <p class="text-sm text-gray-500 mt-1 capitalize">{{ inv.match_type }}</p>
            </div>
            <div class="flex gap-2">
              <button
                type="button"
                class="py-2 px-4 rounded-lg font-medium text-white bg-primary hover:bg-primary/90"
                :disabled="loadingAction === inv._id"
                @click="accept(inv)"
              >
                {{ loadingAction === inv._id ? 'Accepting...' : 'Accept' }}
              </button>
              <button
                type="button"
                class="py-2 px-4 rounded-lg font-medium text-gray-700 bg-gray-200 hover:bg-gray-300"
                :disabled="loadingAction === inv._id"
                @click="reject(inv)"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="errorMessage" class="mt-4 text-red-600 text-sm">{{ errorMessage }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const invitations = ref([])
const loading = ref(true)
const loadingAction = ref(null)
const errorMessage = ref('')

async function fetchInvitations() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/invitations')
    invitations.value = res.data?.invitations || []
  } catch (err) {
    invitations.value = []
    errorMessage.value = err.response?.data?.error || err.message || 'Failed to load invitations'
  } finally {
    loading.value = false
  }
}

async function accept(inv) {
  loadingAction.value = inv._id
  errorMessage.value = ''
  try {
    const res = await api.post(`/invitations/${inv._id}/accept`)
    if (res.data?.pod) {
      router.push(`/pod/${res.data.pod._id}`)
    } else {
      await fetchInvitations()
    }
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || 'Failed to accept'
  } finally {
    loadingAction.value = null
  }
}

async function reject(inv) {
  loadingAction.value = inv._id
  errorMessage.value = ''
  try {
    await api.post(`/invitations/${inv._id}/reject`)
    await fetchInvitations()
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || 'Failed to reject'
  } finally {
    loadingAction.value = null
  }
}

onMounted(fetchInvitations)
</script>
