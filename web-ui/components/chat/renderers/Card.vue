<template>
  <div class="my-2 p-4 bg-gray-800 border-l-4 rounded" :style="{ borderColor: color }">
    <h4 v-if="title" class="font-bold text-gray-200 mb-2">{{ title }}</h4>
    <div class="text-sm text-gray-300">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: { type: String, default: '' },
  color: { type: String, default: '#4f46e5' } // indigo-600
});
</script>