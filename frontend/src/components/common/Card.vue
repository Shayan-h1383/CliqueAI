<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="px-4 sm:px-6 py-4 border-b border-gray-200">
      <slot name="header"></slot>
    </div>
    <div :class="bodyClasses">
      <slot></slot>
    </div>
    <div v-if="$slots.footer" class="px-4 sm:px-6 py-4 border-t border-gray-200">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value),
  },
  hover: {
    type: Boolean,
    default: false,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
})

const cardClasses = computed(() => {
  const base = 'bg-white rounded-lg shadow-md transition-all'
  const hoverEffect = props.hover || props.clickable
    ? 'hover:shadow-lg cursor-pointer'
    : ''
  return `${base} ${hoverEffect}`
})

const bodyClasses = computed(() => {
  const paddings = {
    none: '',
    sm: 'p-3 sm:p-4',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  }
  return paddings[props.padding]
})
</script>

