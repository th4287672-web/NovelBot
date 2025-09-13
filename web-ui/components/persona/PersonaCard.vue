<template>
  <div 
    class="archive-card group transform hover:-translate-y-1 transition-transform duration-200"
    :class="isActive ? 'border-purple-500/50' : 'hover:border-gray-500 cursor-pointer'"
    @click="emit('select', persona.filename)"
  >
    <div class="h-48 relative rounded-t-md overflow-hidden bg-gray-700 flex items-center justify-center">
      <img v-if="getResourceUrl(persona)" 
           :key="getResourceUrl(persona) || persona.filename" 
           :src="getResourceUrl(persona)!" 
           class="w-full h-full object-cover" 
           :alt="`${persona.displayName} Image`">
      <svg v-else class="w-24 h-24 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    </div>
    <div class="p-4 flex-grow">
      <h2 class="text-lg font-semibold truncate pr-2" :class="isActive ? 'text-purple-300' : 'text-white group-hover:text-purple-400'">
        {{ persona.displayName }}
      </h2>
      <p class="text-sm text-gray-400 mt-2 h-24 overflow-hidden text-ellipsis leading-relaxed">
        {{ persona.description || '暂无描述' }}
      </p>
    </div>
    <div class="p-3 border-t border-gray-600/80 flex justify-end space-x-2">
      <button @click.stop="emit('edit', persona)" class="btn btn-secondary !px-3 !py-1 text-xs">编辑</button>
      <button @click.stop="emit('delete', persona)" class="btn btn-danger !px-3 !py-1 text-xs">删除</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { Character, Filename } from '~/types/api';
import { getResourceUrl } from '~/utils/urlBuilder';

const props = defineProps({
  persona: {
    type: Object as PropType<Character>,
    required: true,
  },
  isActive: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits<{
  (e: 'select', filename: Filename): void;
  (e: 'edit', persona: Character): void;
  (e: 'delete', persona: Character): void;
}>();
</script>