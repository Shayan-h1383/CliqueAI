<template>
  <div class="min-h-screen bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 sm:px-6 py-6 sm:py-8">
    <div class="max-w-4xl mx-auto">
      <div class="text-center mb-6 sm:mb-8">
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-800 mb-2">Your clique applications</h1>
        <p class="text-gray-600">Click an application to see your suggested matches</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="applications.length === 0" class="text-center py-12">
        <p class="text-gray-600 mb-4">You haven't submitted any clique applications yet.</p>
        <router-link
          to="/dashboard"
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
            class="w-full text-left px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 hover:bg-gray-50"
            @click="selectedId = selectedId === app._id ? null : app._id"
          >
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-xl sm:text-2xl shrink-0">{{ goalIcon(app.filter?.goal) }}</span>
              <div class="min-w-0">
                <span class="font-semibold text-gray-800 capitalize">{{ app.filter?.goal }}</span>
                <span class="text-gray-500 text-sm sm:ml-2 block sm:inline">· {{ app.filter?.city }} · {{ app.payload?.area }}</span>
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

          <div v-if="selectedId === app._id" class="border-t border-gray-200 px-4 sm:px-6 py-4 bg-gray-50/50">
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
              <p class="text-sm font-medium text-gray-700 mb-3">Suggestions — accept or reject each to form your clique (chat starts when 3+ connect):</p>
              <div class="grid gap-4 sm:grid-cols-2">
                <div
                  v-for="(link, idx) in app.linked_applications"
                  :key="link.application_id || idx"
                  class="bg-white rounded-lg p-4 border border-gray-200 flex items-start gap-3"
                >
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="font-semibold text-gray-800">Suggestion</span>
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
                    <div class="mt-3 flex items-center gap-2 flex-wrap">
                      <span
                        v-if="link.invitation_status === 'pending_them'"
                        class="text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded"
                      >
                        They invited you
                      </span>
                      <span
                        v-else-if="link.invitation_status === 'pending_me'"
                        class="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded"
                      >
                        Waiting for them
                      </span>
                      <span
                        v-else-if="link.invitation_status === 'accepted'"
                        class="text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded"
                      >
                        Connected
                      </span>
                      <span
                        v-else-if="link.invitation_status === 'rejected'"
                        class="text-xs text-gray-500"
                      >
                        Rejected
                      </span>
                      <template v-if="!link.invitation_status || link.invitation_status === 'none' || link.invitation_status === 'pending_them'">
                        <button
                          type="button"
                          class="p-2 rounded-lg font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                          :disabled="loadingRespond === linkKey(link)"
                          aria-label="Accept suggestion"
                          @click="respond(app, link, true)"
                        >
                          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                          </svg>
                        </button>
                        <button
                          v-if="link.invitation_status !== 'rejected'"
                          type="button"
                          class="p-2 rounded-lg font-medium text-white bg-red-500 hover:bg-red-600 disabled:opacity-50"
                          :disabled="loadingRespond === linkKey(link)"
                          aria-label="Reject suggestion"
                          @click="respond(app, link, false)"
                        >
                          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                          </svg>
                        </button>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="applications.length > 0" class="mt-8 text-center">
        <router-link to="/dashboard" class="text-primary font-medium hover:underline">Submit another application</router-link>
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
const loadingRespond = ref(null)
const invitationError = ref('')
const invitationSuccess = ref('')

const goalIcons = { evolve: '🎯', enjoy: '💙', support: '🤝' }
function goalIcon(goal) {
  return goalIcons[goal] || '•'
}

function linkKey(link) {
  return link.application_id + '-' + (link.user_id || '')
}

async function respond(app, link, accept) {
  const key = linkKey(link)
  loadingRespond.value = key
  invitationError.value = ''
  invitationSuccess.value = ''
  if (!link.user_id) {
    invitationError.value = 'Cannot respond: user not found.'
    loadingRespond.value = null
    return
  }
  try {
    const res = await api.post('/invitations/respond', {
      other_user_id: link.user_id,
      accept,
      match_type: app.filter?.goal || 'evolve',
      application_id: app._id,
    })
    if (accept && res.data?.pod) {
      invitationSuccess.value = 'Connected! Opening group chat...'
      router.push(`/pod/${res.data.pod._id}`)
      return
    }
    if (accept && res.data?.pending_them) {
      invitationSuccess.value = 'Invitation sent. They’ll see it on their Suggestions page.'
    } else if (accept) {
      invitationSuccess.value = 'You’re connected. Group chat will open when 3+ are in the clique.'
    } else {
      invitationSuccess.value = 'Rejected.'
    }
    await fetchApplications()
  } catch (err) {
    invitationError.value = err.response?.data?.error || err.message || 'Request failed.'
  } finally {
    loadingRespond.value = null
  }
}

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


onMounted(fetchApplications)
</script>
