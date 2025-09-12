<template>
  <span class="inline-flex items-center gap-2 bg-gray-900/50 border border-gray-600 rounded-full px-3 py-1 text-sm font-semibold text-cyan-300 mx-1">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h.5a1.5 1.5 0 010 3H14a1 1 0 00-1 1v.5a1.5 1.5 0 01-3 0V8a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H8a1 1 0 001-1v-.5a1.5 1.5 0 011.5-1.5zM5.5 10a1.5 1.5 0 013 0V14a1 1 0 001 1h.5a1.5 1.5 0 010 3H9a1 1 0 00-1 1v.5a1.5 1.5 0 01-3 0V16a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1v-.5z" /></svg>
    <span>{{ result }}</span>
    <span class="text-gray-500 text-xs">({{ expression }})</span>
  </span>
</template>

<script setup lang="ts">
defineProps({
  result: { type: String, required: true },
  expression: { type: String, required: true },
});
</script>