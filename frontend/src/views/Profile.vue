<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 sm:px-6 py-8 sm:py-12">
    <Card class="w-full max-w-md mx-2">
      <div class="text-center mb-6 sm:mb-8">
        <h1 class="text-2xl sm:text-3xl font-bold text-primary mb-2">Profile</h1>
        <p class="text-gray-600">Manage your account settings</p>
      </div>

      <form @submit.prevent="handleUpdateUsername" class="space-y-6">
        <Input
          v-model="username"
          type="text"
          label="Username"
          placeholder="Enter your username"
          :error="errors.username"
          required
          maxlength="50"
        />

        <div v-if="successMessage" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {{ errorMessage }}
        </div>

        <Button
          type="submit"
          variant="primary"
          class="w-full"
          :loading="loading"
        >
          Update username
        </Button>
      </form>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Card from '@/components/common/Card.vue'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'

const authStore = useAuthStore()

const username = ref('')
const errors = ref({})
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)

function syncUsername() {
  if (authStore.user?.username && !username.value) {
    username.value = authStore.user.username
  }
}

onMounted(syncUsername)

watch(() => authStore.user?.username, (val) => {
  if (val) username.value = val
})

function validateForm() {
  errors.value = {}

  const trimmed = (username.value || '').trim()
  if (!trimmed) {
    errors.value.username = 'Username is required'
  } else if (trimmed.length > 50) {
    errors.value.username = 'Username must be at most 50 characters'
  }

  return Object.keys(errors.value).length === 0
}

async function handleUpdateUsername() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!validateForm()) {
    return
  }

  const newUsername = username.value.trim()
  if (newUsername === authStore.user?.username) {
    successMessage.value = 'Your username is already set to this value.'
    return
  }

  loading.value = true

  try {
    await authStore.updateUsername(newUsername)
    successMessage.value = 'Username updated successfully.'
  } catch (error) {
    errorMessage.value = error.message || 'Failed to update username.'
  } finally {
    loading.value = false
  }
}
</script>
