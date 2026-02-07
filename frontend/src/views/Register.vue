<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4">
    <Card class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-primary mb-2">cliqueAI</h1>
        <p class="text-gray-600">Stop Broadcasting. Start Connecting.</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-6">
        <Input
          v-model="username"
          type="text"
          label="Username"
          placeholder="Choose a username"
          :error="errors.username"
          required
        />

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
          placeholder="Enter your password (min 6 characters)"
          :error="errors.password"
          required
        />

        <Input
          v-model="confirmPassword"
          type="password"
          label="Confirm Password"
          placeholder="Confirm your password"
          :error="errors.confirmPassword"
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
          Create Account
        </Button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-gray-600">
          Already have an account?
          <router-link to="/login" class="text-primary hover:underline font-medium">
            Login here
          </router-link>
        </p>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Card from '@/components/common/Card.vue'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const errors = ref({})
const errorMessage = ref('')
const loading = ref(false)

function validateForm() {
  errors.value = {}
  
  if (!username.value) {
    errors.value.username = 'Username is required'
  } else if (username.value.length < 1) {
    errors.value.username = 'Username must be at least 1 character'
  }
  
  if (!email.value) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    errors.value.email = 'Email is invalid'
  }
  
  if (!password.value) {
    errors.value.password = 'Password is required'
  } else if (password.value.length < 6) {
    errors.value.password = 'Password must be at least 6 characters'
  }
  
  if (!confirmPassword.value) {
    errors.value.confirmPassword = 'Please confirm your password'
  } else if (password.value !== confirmPassword.value) {
    errors.value.confirmPassword = 'Passwords do not match'
  }
  
  return Object.keys(errors.value).length === 0
}

async function handleRegister() {
  errorMessage.value = ''
  
  if (!validateForm()) {
    return
  }
  
  loading.value = true
  
  try {
    await authStore.register(username.value, email.value, password.value)
    
    // After registration, redirect to onboarding
    router.push('/onboarding')
  } catch (error) {
    errorMessage.value = error.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

