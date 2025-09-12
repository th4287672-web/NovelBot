<template>
  <div class="absolute bottom-full left-0 right-0 mb-2 p-4 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-20">
    <div class="flex flex-col space-y-3">
      <label for="guidance-input" class="text-sm font-medium text-gray-300">
        引导AI回复的方向 (可选)
      </label>
      <div class="flex space-x-2">
        <input
          id="guidance-input"
          v-model="guidance"
          type="text"
          :disabled="suggestionState.isLoading"
          placeholder="例如：让他表现得更强硬一些"
          class="flex-grow bg-gray-700 text-white p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
          @keydown.enter.prevent="handleGenerate"
        />
        <button
          @click="handleGenerate"
          :disabled="suggestionState.isLoading"
          class="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-4 rounded-md transition-colors disabled:bg-gray-500 disabled:cursor-wait"
        >
          {{ suggestionState.isLoading ? '生成中...' : '生成建议' }}
        </button>
      </div>

      <div v-if="suggestionState.suggestions.length > 0" class="pt-3 border-t border-gray-700 space-y-2">
        <p class="text-sm text-gray-400">点击以使用：</p>
        <div 
          v-for="(suggestion, index) in suggestionState.suggestions" 
          :key="index"
          @click="handleSelect(suggestion)"
          class="p-3 bg-gray-800 hover:bg-gray-700 rounded-md cursor-pointer transition-colors text-gray-200 text-sm"
        >
          {{ suggestion }}
        </div>
      </div>
    </div>
    <button @click="emit('close')" class="absolute top-2 right-2 text-gray-500 hover:text-white">&times;</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { PropType } from 'vue';

interface SuggestionState {
    isLoading: boolean;
    suggestions: string[];
}

defineProps({
    suggestionState: {
        type: Object as PropType<SuggestionState>,
        required: true
    }
});

const emit = defineEmits<{
  (e: 'select-suggestion', text: string): void;
  (e: 'close'): void;
  (e: 'generate', guidance: string): void;
}>();

const guidance = ref('');

function handleGenerate() {
  emit('generate', guidance.value);
}

function handleSelect(suggestion: string) {
  emit('select-suggestion', suggestion);
}
</script>