<template>
  <div class="space-y-6">
    <div class="text-center mb-8">
      <h2 class="text-3xl font-bold text-gray-800 mb-2">What are you looking for?</h2>
      <p class="text-gray-600">Choose the type of connection you want to make</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'friendship' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('friendship')"
      >
        <div class="text-5xl mb-4">🤝</div>
        <h3 class="text-xl font-bold text-gray-800 mb-2">Friendship</h3>
        <p class="text-gray-600">Connect over shared interests</p>
      </Card>

      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'goal' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('goal')"
      >
        <div class="text-5xl mb-4">🎯</div>
        <h3 class="text-xl font-bold text-gray-800 mb-2">Goal</h3>
        <p class="text-gray-600">Find accountability partners</p>
      </Card>

      <Card
        :clickable="true"
        :hover="true"
        :class="[
          'text-center p-8 cursor-pointer transition-all',
          selectedType === 'issues' ? 'ring-4 ring-primary bg-primary/5' : ''
        ]"
        @click="selectType('issues')"
      >
        <div class="text-5xl mb-4">✨</div>
        <h3 class="text-xl font-bold text-gray-800 mb-2">Issues</h3>
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

