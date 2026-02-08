<template>
  <div id="app" class="min-h-screen">
    <template v-if="showNavigation">
      <!-- Mobile menu button -->
      <button
        type="button"
        class="lg:hidden fixed top-4 left-4 z-20 p-2 rounded-lg bg-white border border-gray-200 shadow-sm text-gray-700 hover:bg-gray-50"
        aria-label="Toggle menu"
        @click="sidebarOpen = !sidebarOpen"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!sidebarOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Sidebar overlay for mobile -->
      <div
        v-if="sidebarOpen"
        class="lg:hidden fixed inset-0 bg-black/30 z-[9]"
        aria-hidden="true"
        @click="sidebarOpen = false"
      />

      <aside
        :class="[
          'app-sidebar fixed left-0 top-0 bottom-0 bg-white border-r border-gray-200 shadow-sm flex flex-col z-10 transition-transform duration-200 ease-out',
          'w-72 max-w-[85vw]',
          'lg:w-[280px] lg:max-w-none lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
      >
        <div class="p-4 sm:p-6 border-b border-gray-100 shrink-0 pt-14 lg:pt-6">
          <router-link to="/dashboard" class="text-xl sm:text-2xl font-bold text-primary" @click="sidebarOpen = false">
            cliqueAI
          </router-link>
        </div>
        <div class="flex-1 flex flex-col min-h-0 overflow-y-auto">
          <nav class="flex flex-col p-3 sm:p-4 gap-1 shrink-0">
            <router-link
              v-if="authStore.isAuthenticated"
              to="/dashboard"
              class="nav-link rounded-lg px-4 py-3 text-gray-700 hover:bg-primary/10 hover:text-primary font-medium transition-colors"
              :class="{ 'bg-primary/10 text-primary': $route.path === '/dashboard' }"
              @click="sidebarOpen = false"
            >
              Dashboard
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/suggestions"
              class="nav-link rounded-lg px-4 py-3 text-gray-700 hover:bg-primary/10 hover:text-primary font-medium transition-colors"
              :class="{ 'bg-primary/10 text-primary': $route.path === '/suggestions' }"
              @click="sidebarOpen = false"
            >
              Suggestions
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/profile"
              class="nav-link rounded-lg px-4 py-3 text-gray-700 hover:bg-primary/10 hover:text-primary font-medium transition-colors"
              :class="{ 'bg-primary/10 text-primary': $route.path === '/profile' }"
              @click="sidebarOpen = false"
            >
              Profile
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
                @click="sidebarOpen = false"
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
      <main class="app-main min-h-screen min-w-0 pl-0 lg:pl-[280px] pt-14 lg:pt-0">
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
const sidebarOpen = ref(false)

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

