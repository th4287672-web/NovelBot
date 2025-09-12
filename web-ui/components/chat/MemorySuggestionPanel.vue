<template>
  <div class="absolute bottom-full left-0 right-0 mb-2 p-4 bg-gray-900 border border-yellow-500/50 rounded-lg shadow-xl z-20">
    <div class="flex flex-col space-y-3">
      <h4 class="text-sm font-semibold text-yellow-300">记忆建议</h4>
      <p class="text-xs text-gray-400">AI从刚才的对话中提取了以下关键信息，是否要保存到角色的长期记忆中？</p>
      
      <div class="max-h-40 overflow-y-auto space-y-2 border-t border-b border-gray-700 py-2">
        <div 
          v-for="(suggestion, index) in suggestions" 
          :key="index"
          class="p-2 bg-gray-800 rounded-md text-gray-200 text-sm"
        >
          - {{ suggestion }}
        </div>
      </div>
      
      <div class="flex justify-end space-x-2">
        <button @click="emit('dismiss')" class="btn btn-secondary text-xs">忽略</button>
        <button @click="emit('accept', suggestions)" class="btn btn-primary bg-yellow-600 hover:bg-yellow-500 text-xs">全部保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';

defineProps({
    suggestions: {
        type: Array as PropType<string[]>,
        required: true
    }
});

const emit = defineEmits<{
  (e: 'accept', suggestions: string[]): void;
  (e: 'dismiss'): void;
}>();
</script>