<template>
  <div class="my-2">
    <label v-if="label" class="text-sm font-medium text-gray-300 mb-1 block">{{ label }}</label>
    <div class="flex items-center gap-2">
      <progress
        class="w-full h-4 rounded-full overflow-hidden [&::-webkit-progress-bar]:bg-gray-700 [&::-webkit-progress-value]:bg-cyan-500 [&::-moz-progress-bar]:bg-cyan-500"
        :value="numericValue"
        :max="numericMax"
      ></progress>
      <span class="text-sm font-mono text-gray-400 shrink-0">{{ percentage }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  value: { type: [String, Number], default: 0 },
  max: { type: [String, Number], default: 100 },
  label: { type: String, default: '' },
});

const numericValue = computed(() => Number(props.value));
const numericMax = computed(() => Number(props.max));

const percentage = computed(() => {
  if (numericMax.value === 0) return 0;
  return Math.round((numericValue.value / numericMax.value) * 100);
});
</script>