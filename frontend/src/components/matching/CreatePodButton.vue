<template>
  <div class="mt-8 text-center">
    <p v-if="selectedCount < 2" class="text-gray-600 mb-4">
      Select {{ 2 - selectedCount }} more {{ selectedCount === 1 ? 'person' : 'people' }} to create your clique
    </p>
    <Button
      variant="primary"
      size="lg"
      :disabled="selectedCount !== 2 || loading"
      :loading="loading"
      @click="$emit('create')"
    >
      Create Pod
    </Button>
  </div>
</template>

<script setup>
import Button from '@/components/common/Button.vue'

defineProps({
  selectedCount: {
    type: Number,
    default: 0,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['create'])
</script>

