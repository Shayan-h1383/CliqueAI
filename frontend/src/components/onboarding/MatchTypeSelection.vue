<template>
  <div class="space-y-6">
    <div class="text-center mb-6 sm:mb-8">
      <h2 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">What are you looking for?</h2>
      <p class="text-gray-600">Choose the type of connection you want to make</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'evolve' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('evolve')"
      >
        <div class="text-4xl sm:text-5xl mb-4">🎯</div>
        <h3 class="text-lg sm:text-xl font-bold text-gray-800 mb-2">Evolve</h3>
        <p class="text-gray-600">Grow and develop together</p>
      </Card>

      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'enjoy' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('enjoy')"
      >
        <div class="text-4xl sm:text-5xl mb-4">💙</div>
        <h3 class="text-lg sm:text-xl font-bold text-gray-800 mb-2">Enjoy</h3>
        <p class="text-gray-600">Connect over shared interests</p>
      </Card>

      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'support' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('support')"
      >
        <div class="text-4xl sm:text-5xl mb-4">🤝</div>
        <h3 class="text-lg sm:text-xl font-bold text-gray-800 mb-2">Support</h3>
        <p class="text-gray-600">Get support for challenges</p>
      </Card>
    </div>

    <div class="flex justify-center mt-8">
      <Button
        variant="primary"
        size="lg"
        :disabled="!selectedType"
        @click="handleNext"
      >
        Continue
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'next'])

const selectedType = ref(props.modelValue)

function selectType(type) {
  selectedType.value = type
  emit('update:modelValue', type)
}

function handleNext() {
  if (selectedType.value) {
    emit('next')
  }
}
</script>

