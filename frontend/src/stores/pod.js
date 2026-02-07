import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const usePodStore = defineStore('pod', () => {
  // State
  const activePod = ref(null)
  const podMembers = ref([])

  // Actions
  async function fetchActivePod() {
    try {
      const response = await api.get('/pods/active')
      if (response.data.pod) {
        activePod.value = response.data.pod
        await fetchPodMembers(response.data.pod._id)
      } else {
        activePod.value = null
        podMembers.value = []
      }
      return response.data.pod
    } catch (error) {
      console.error('Failed to fetch active pod:', error)
      activePod.value = null
      podMembers.value = []
      throw error
    }
  }

  async function fetchPod(podId) {
    try {
      const response = await api.get(`/pods/${podId}`)
      activePod.value = response.data.pod
      await fetchPodMembers(podId)
      return response.data.pod
    } catch (error) {
      console.error('Failed to fetch pod:', error)
      throw error
    }
  }

  async function fetchPodMembers(podId) {
    try {
      const pod = activePod.value || await fetchPod(podId)
      if (!pod || !pod.members) {
        podMembers.value = []
        return
      }

      // Fetch user details for each member
      const memberPromises = pod.members.map(async (memberId) => {
        try {
          // Note: We might need a GET /api/users/:id endpoint
          // For now, we'll use the member ID and fetch from pod data
          return memberId
        } catch (error) {
          console.error(`Failed to fetch member ${memberId}:`, error)
          return null
        }
      })

      const members = await Promise.all(memberPromises)
      podMembers.value = members.filter(Boolean)
    } catch (error) {
      console.error('Failed to fetch pod members:', error)
      podMembers.value = []
    }
  }

  function setActivePod(pod) {
    activePod.value = pod
  }

  function clearPod() {
    activePod.value = null
    podMembers.value = []
  }

  async function leavePod(podId) {
    try {
      await api.post(`/pods/${podId}/leave`)
      clearPod()
    } catch (error) {
      console.error('Failed to leave pod:', error)
      throw error
    }
  }

  return {
    // State
    activePod,
    podMembers,
    // Actions
    fetchActivePod,
    fetchPod,
    fetchPodMembers,
    setActivePod,
    clearPod,
    leavePod,
  }
})

