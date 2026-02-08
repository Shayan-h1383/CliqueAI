<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 sm:px-6 py-6 sm:py-8">
    <Card class="w-full max-w-md mx-2">
      <div class="text-center mb-6 sm:mb-8">
        <h1 class="text-3xl sm:text-4xl font-bold text-primary mb-2">cliqueAI</h1>
        <p class="text-gray-600">Stop Broadcasting. Start Connecting.</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <Input
          v-model="email"
          type="email"
          label="Email"
          placeholder="Enter your email"
          :error="errors.email"
          required
        />

        <Input
          v-model="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          :error="errors.password"
          required
        />

        <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {{ errorMessage }}
        </div>

        <Button
          type="submit"
          variant="primary"
          class="w-full"
          :loading="loading"
        >
          Login
        </Button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-gray-600">
          Don't have an account?
          <router-link to="/register" class="text-primary hover:underline font-medium">
            Register here
          </router-link>
        </p>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Card from '@/components/common/Card.vue'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const errors = ref({})
const errorMessage = ref('')
const loading = ref(false)

function validateForm() {
  errors.value = {}
  
  if (!email.value) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    errors.value.email = 'Email is invalid'
  }
  
  if (!password.value) {
    errors.value.password = 'Password is required'
  }
  
  return Object.keys(errors.value).length === 0
}

async function handleLogin() {
  errorMessage.value = ''
  
  if (!validateForm()) {
    return
  }
  
  loading.value = true
  
  try {
    await authStore.login(email.value, password.value)
    
    // Redirect to intended page or dashboard
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (error) {
    errorMessage.value = error.message || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

