<template>
  <div id="app" class="min-h-screen">
    <template v-if="showNavigation">
      <aside
        class="app-sidebar fixed left-0 top-0 bottom-0 w-[25%] bg-white border-r border-gray-200 shadow-sm flex flex-col z-10"
      >
        <div class="p-6 border-b border-gray-100 shrink-0">
          <router-link to="/dashboard" class="text-2xl font-bold text-primary">
            cliqueAI
          </router-link>
        </div>
        <div class="flex-1 flex flex-col min-h-0 overflow-y-auto">
          <nav class="flex flex-col p-4 gap-1 shrink-0">
            <router-link
              v-if="authStore.isAuthenticated"
              to="/dashboard"
              class="nav-link rounded-lg px-4 py-3 text-gray-700 hover:bg-primary/10 hover:text-primary font-medium transition-colors"
              :class="{ 'bg-primary/10 text-primary': $route.path === '/dashboard' }"
            >
              Dashboard
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/suggestions"
              class="nav-link rounded-lg px-4 py-3 text-gray-700 hover:bg-primary/10 hover:text-primary font-medium transition-colors"
              :class="{ 'bg-primary/10 text-primary': $route.path === '/suggestions' }"
            >
              Suggestions
            </router-link>
          </nav>
          <div v-if="authStore.isAuthenticated" class="px-4 pb-4 shrink-0">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 mb-2">
              Chats
            </h3>
            <div v-if="chatsLoading" class="px-4 py-2">
              <span class="text-sm text-gray-500">Loading...</span>
            </div>
            <template v-else>
              <router-link
                v-for="pod in displayedChats"
                :key="pod._id"
                :to="`/pod/${pod._id}`"
                class="chat-link flex flex-col gap-0.5 rounded-lg px-4 py-2.5 text-gray-700 hover:bg-primary/10 hover:text-primary text-sm font-medium transition-colors min-w-0"
                :class="{ 'bg-primary/10 text-primary': $route.params.pod_id === pod._id }"
                :title="chatDisplayName(pod)"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <span class="shrink-0 text-base" aria-hidden="true">💬</span>
                  <span class="truncate min-w-0">{{ chatDisplayName(pod) }}</span>
                </div>
                <span v-if="pod.created_at" class="text-xs text-gray-500 font-normal pl-6">{{ formatChatDate(pod.created_at) }}</span>
              </router-link>
              <button
                v-if="hasMoreChats"
                type="button"
                class="w-full mt-2 rounded-lg px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 transition-colors text-left"
                @click="loadMoreChats"
              >
                Load more
              </button>
            </template>
          </div>
        </div>
        <div class="p-4 border-t border-gray-100 shrink-0">
          <Button
            v-if="authStore.isAuthenticated"
            variant="outline"
            size="sm"
            class="w-full justify-center"
            @click="handleLogout"
          >
            Logout
          </Button>
        </div>
      </aside>
      <main class="app-main min-h-screen ml-[25%] min-w-0">
        <router-view :key="$route.fullPath" />
      </main>
    </template>
    <template v-else>
      <router-view :key="$route.fullPath" />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePodStore } from '@/stores/pod'
import Button from '@/components/common/Button.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const podStore = usePodStore()

const chats = ref([])
const chatsLoading = ref(false)
const visibleChatCount = ref(4)

const showNavigation = computed(() => {
  const noNavRoutes = ['/login', '/register']
  return !noNavRoutes.includes(route.path)
})

const displayedChats = computed(() => chats.value.slice(0, visibleChatCount.value))

const hasMoreChats = computed(() => chats.value.length > visibleChatCount.value)

function chatDisplayName(pod) {
  const names = pod.member_usernames ?? pod.memberUsernames
  if (Array.isArray(names) && names.length > 0) {
    return names.join(', ')
  }
  return pod.pod_type ? String(pod.pod_type).charAt(0).toUpperCase() + pod.pod_type.slice(1) : 'Clique'
}

function formatChatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const opts = { month: 'short', day: 'numeric' }
  if (date.getFullYear() !== new Date().getFullYear()) {
    opts.year = 'numeric'
  }
  return date.toLocaleDateString('en-US', opts)
}

async function fetchChats() {
  if (!authStore.isAuthenticated) return
  chatsLoading.value = true
  try {
    chats.value = await podStore.fetchMyPods()
  } catch {
    chats.value = []
  } finally {
    chatsLoading.value = false
  }
}

function loadMoreChats() {
  visibleChatCount.value = Math.min(visibleChatCount.value + 4, chats.value.length)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth && showNavigation.value) {
      fetchChats()
    } else {
      chats.value = []
      visibleChatCount.value = 4
    }
  }
)

onMounted(() => {
  if (authStore.isAuthenticated && showNavigation.value) {
    fetchChats()
  }
})
</script>

