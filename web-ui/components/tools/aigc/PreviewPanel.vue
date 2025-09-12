<template>
  <div class="bg-gray-900/50 rounded-lg flex items-center justify-center border border-gray-700 relative overflow-hidden">
    <div v-if="isGenerating" class="text-center text-gray-400">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500 mx-auto"></div>
        <p class="mt-4">AI 正在努力绘画中...</p>
    </div>
    <img v-else-if="imageUrl" :src="imageUrl" alt="Generated Image" class="max-h-full max-w-full object-contain">
    <p v-else class="text-gray-500">生成的图片将在这里显示</p>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';

defineProps({
    imageUrl: {
        type: String as PropType<string | null>,
        default: null
    },
    isGenerating: Boolean,
});
</script>