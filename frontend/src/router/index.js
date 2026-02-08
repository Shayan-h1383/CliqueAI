import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: (to) => {
        const authStore = useAuthStore()
        return authStore.isAuthenticated ? '/dashboard' : '/login'
      },
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/onboarding',
      name: 'Onboarding',
      component: () => import('@/views/Onboarding.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/suggestions',
      name: 'Suggestions',
      component: () => import('@/views/Suggestions.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/invitations',
      name: 'Invitations',
      component: () => import('@/views/Invitations.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/matching',
      name: 'Matching',
      component: () => import('@/views/Matching.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/pod/:pod_id',
      name: 'PodChat',
      component: () => import('@/views/PodChat.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/Profile.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // If route requires auth
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    // Try to load user if not already loaded
    if (!authStore.user && authStore.token) {
      try {
        await authStore.loadUser()
      } catch (error) {
        // If loading user fails, redirect to login
        next({ name: 'Login' })
        return
      }
    }
  }

  // If route requires guest (not authenticated)
  if (to.meta.requiresGuest) {
    if (authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router

