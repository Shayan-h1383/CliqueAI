<template>
  <div class="min-h-screen bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 py-8">
    <div class="max-w-4xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">Your clique applications</h1>
        <p class="text-gray-600">Click an application to see your suggested matches</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="applications.length === 0" class="text-center py-12">
        <p class="text-gray-600 mb-4">You haven't submitted any clique applications yet.</p>
        <router-link
          to="/find-match"
          class="inline-block py-3 px-6 rounded-lg font-semibold text-white bg-primary hover:bg-primary/90"
        >
          Find your clique
        </router-link>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="app in applications"
          :key="app._id"
          class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
        >
          <button
            type="button"
            class="w-full text-left px-6 py-4 flex items-center justify-between hover:bg-gray-50"
            @click="selectedId = selectedId === app._id ? null : app._id"
          >
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ goalIcon(app.filter?.goal) }}</span>
              <div>
                <span class="font-semibold text-gray-800 capitalize">{{ app.filter?.goal }}</span>
                <span class="text-gray-500 text-sm ml-2">· {{ app.filter?.city }} · {{ app.payload?.area }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'text-sm font-medium px-2 py-1 rounded',
                  app.status === 'matched' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                ]"
              >
                {{ app.status }}
              </span>
              <svg
                class="w-5 h-5 text-gray-400 transition-transform"
                :class="{ 'rotate-180': selectedId === app._id }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>

          <div v-if="selectedId === app._id" class="border-t border-gray-200 px-6 py-4 bg-gray-50/50">
            <!-- Full application payload -->
            <div class="mb-4 p-4 bg-white rounded-lg border border-gray-200">
              <p class="text-sm font-medium text-gray-700 mb-2">Your application</p>
              <p class="text-sm text-gray-600"><span class="font-medium">Goal:</span> {{ app.payload?.goal || app.filter?.goal }}</p>
              <p class="text-sm text-gray-600"><span class="font-medium">Area:</span> {{ app.payload?.area }}</p>
              <p class="text-sm text-gray-600"><span class="font-medium">Details:</span> {{ app.payload?.details }}</p>
              <p class="text-sm text-gray-600"><span class="font-medium">Summary:</span> {{ app.payload?.third_field }}</p>
              <p class="text-sm text-gray-600"><span class="font-medium">City:</span> {{ app.payload?.city || app.filter?.city }}</p>
            </div>
            <div v-if="!app.linked_applications || app.linked_applications.length === 0" class="py-8 text-center text-gray-600">
              <p class="font-medium">No matches found</p>
              <p class="text-sm mt-1">No other applications in your goal and city matched above the similarity threshold. Try different details or check back when more people apply.</p>
            </div>
            <div v-else>
              <p class="text-sm font-medium text-gray-700 mb-3">Why these people were selected for you:</p>
              <div class="grid gap-4 sm:grid-cols-2">
                <div
                  v-for="(link, idx) in app.linked_applications"
                  :key="link.application_id || idx"
                  class="bg-white rounded-lg p-4 border border-gray-200 flex items-start gap-3"
                >
                  <label class="flex items-start gap-3 flex-1 cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="selectedForPod.includes(link.application_id)"
                      :disabled="selectedForPod.length >= 2 && !selectedForPod.includes(link.application_id)"
                      class="mt-1 rounded border-gray-300 text-primary focus:ring-primary"
                      @change="toggleForPod(link.application_id)"
                    />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <img
                          v-if="link.profile_pic_url"
                          :src="link.profile_pic_url"
                          alt=""
                          class="w-10 h-10 rounded-full object-cover"
                        />
                        <div
                          v-else
                          class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold"
                        >
                          {{ (link.username || '?')[0].toUpperCase() }}
                        </div>
                        <span class="font-semibold text-gray-800">{{ link.username || 'Unknown' }}</span>
                        <span class="text-sm text-primary font-medium">{{ Math.round((link.similarity_score || 0) * 100) }}% match</span>
                      </div>
                      <div v-if="link.payload" class="mt-2 p-3 rounded bg-gray-50 text-sm text-gray-700 space-y-1">
                        <p><span class="font-medium">Goal:</span> {{ link.payload.goal }}</p>
                        <p><span class="font-medium">Area:</span> {{ link.payload.area }}</p>
                        <p><span class="font-medium">Details:</span> {{ link.payload.details }}</p>
                        <p><span class="font-medium">Summary:</span> {{ link.payload.third_field }}</p>
                        <p><span class="font-medium">City:</span> {{ link.payload.city }}</p>
                      </div>
                      <p v-else class="text-sm text-gray-600 mt-2">{{ link.why_selected || 'Good match based on your profile.' }}</p>
                    </div>
                  </label>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-4">
                <button
                  v-if="selectedForPod.length === 2"
                  type="button"
                  class="py-2 px-4 rounded-lg font-medium text-white bg-primary hover:bg-primary/90"
                  @click="sendInvitations(app)"
                >
                  Send clique invitation to selected 2
                </button>
                <p v-else class="text-sm text-gray-500">Select 2 people to invite to your clique (you'll be the 3rd).</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="applications.length > 0" class="mt-8 text-center">
        <router-link to="/find-match" class="text-primary font-medium hover:underline">Submit another application</router-link>
      </div>

      <div v-if="invitationError" class="mt-4 text-red-600 text-sm">{{ invitationError }}</div>
      <div v-if="invitationSuccess" class="mt-4 text-green-600 text-sm">{{ invitationSuccess }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const applications = ref([])
const loading = ref(true)
const selectedId = ref(null)
const selectedForPod = ref([])
const invitationError = ref('')
const invitationSuccess = ref('')

const goalIcons = { evolve: '🌱', enjoy: '🎯', support: '💙' }
function goalIcon(goal) {
  return goalIcons[goal] || '•'
}

watch(selectedId, (newVal) => {
  selectedForPod.value = []
})

async function fetchApplications() {
  loading.value = true
  try {
    const res = await api.get('/applications')
    applications.value = res.data || []
  } catch (err) {
    applications.value = []
  } finally {
    loading.value = false
  }
}

function toggleForPod(applicationId) {
  const idx = selectedForPod.value.indexOf(applicationId)
  if (idx >= 0) {
    selectedForPod.value.splice(idx, 1)
  } else if (selectedForPod.value.length < 2) {
    selectedForPod.value.push(applicationId)
  }
}

async function sendInvitations(app) {
  if (selectedForPod.value.length !== 2) return
  invitationError.value = ''
  invitationSuccess.value = ''
  const currentUserId = authStore.user?._id || authStore.user?.id
  if (!currentUserId) {
    invitationError.value = 'User not found'
    return
  }
  const selectedApps = app.linked_applications.filter((l) => selectedForPod.value.includes(l.application_id))
  const inviteeIds = [selectedApps[0].user_id, selectedApps[1].user_id]
  if (inviteeIds.some((id) => id === currentUserId)) {
    invitationError.value = 'You cannot invite yourself.'
    return
  }
  try {
    await api.post('/invitations', {
      invitee_ids: inviteeIds,
      match_type: app.filter?.goal || 'evolve',
      application_id: app._id,
    })
    invitationSuccess.value = 'Invitations sent! The invited users will see them in their Invitations page.'
    selectedForPod.value = []
  } catch (err) {
    invitationError.value = err.response?.data?.error || err.message || 'Failed to send invitations.'
  }
}

onMounted(fetchApplications)
</script>
