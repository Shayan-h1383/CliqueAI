<template>
  <div id="app" class="min-h-screen">
    <nav v-if="showNavigation" class="bg-white shadow-md">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <router-link to="/dashboard" class="text-2xl font-bold text-primary">
              cliqueAI
            </router-link>
          </div>
          
          <div class="hidden md:flex items-center space-x-4">
            <router-link
              v-if="authStore.isAuthenticated"
              to="/dashboard"
              class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
            >
              Dashboard
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/matching"
              class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
            >
              Find Matches
            </router-link>
            <Button
              v-if="authStore.isAuthenticated"
              variant="outline"
              size="sm"
              @click="handleLogout"
            >
              Logout
            </Button>
          </div>

          <!-- Mobile menu button -->
          <div class="md:hidden">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="text-gray-700 hover:text-primary focus:outline-none"
            >
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  v-if="!mobileMenuOpen"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
                <path
                  v-else
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Mobile menu -->
        <div v-if="mobileMenuOpen" class="md:hidden pb-4 space-y-2">
          <router-link
            v-if="authStore.isAuthenticated"
            to="/dashboard"
            class="block text-gray-700 hover:text-primary px-3 py-2 rounded-md text-base font-medium"
            @click="mobileMenuOpen = false"
          >
            Dashboard
          </router-link>
          <router-link
            v-if="authStore.isAuthenticated"
            to="/matching"
            class="block text-gray-700 hover:text-primary px-3 py-2 rounded-md text-base font-medium"
            @click="mobileMenuOpen = false"
          >
            Find Matches
          </router-link>
          <button
            v-if="authStore.isAuthenticated"
            @click="handleLogout"
            class="block w-full text-left text-gray-700 hover:text-primary px-3 py-2 rounded-md text-base font-medium"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/common/Button.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const mobileMenuOpen = ref(false)

const showNavigation = computed(() => {
  const noNavRoutes = ['/login', '/register']
  return !noNavRoutes.includes(route.path)
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
  mobileMenuOpen.value = false
}
</script>

