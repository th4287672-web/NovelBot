<template>
  <div v-if="isEnabled && rect" class="fixed bottom-4 right-4 bg-gray-900/80 backdrop-blur-sm border border-yellow-500 rounded-lg shadow-2xl p-4 text-xs font-mono text-white w-72 z-[9999]">
    <h4 class="font-bold text-yellow-300 mb-2">// Actions Wrapper Diagnosis</h4>
    <div class="grid grid-cols-2 gap-x-4 gap-y-1">
      <span>x:</span> <span class="text-cyan-300">{{ rect.x.toFixed(2) }}</span>
      <span>y:</span> <span class="text-cyan-300">{{ rect.y.toFixed(2) }}</span>
      <span>width:</span> <span class="text-cyan-300">{{ rect.width.toFixed(2) }}</span>
      <span>height:</span> <span class="text-cyan-300">{{ rect.height.toFixed(2) }}</span>
      <span>top:</span> <span class="text-cyan-300">{{ rect.top.toFixed(2) }}</span>
      <span>right:</span> <span class="text-cyan-300">{{ rect.right.toFixed(2) }}</span>
      <span>bottom:</span> <span class="text-cyan-300">{{ rect.bottom.toFixed(2) }}</span>
      <span>left:</span> <span class="text-cyan-300">{{ rect.left.toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';

defineProps({
  rect: {
    type: Object as PropType<DOMRect | null>,
    required: true,
  },
  isEnabled: {
    type: Boolean,
    required: true,
  }
});
</script>