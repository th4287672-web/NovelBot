<template>
  <div 
    class="archive-card group transform hover:-translate-y-1 transition-transform duration-200"
    :class="{ 'border-cyan-500/50': isActive, 'cursor-pointer': !isActive }"
    @click="handleCardClick"
  >
    <div class="h-48 relative rounded-t-md overflow-hidden bg-gray-700 flex items-center justify-center">
      <img v-if="getResourceUrl(character)" 
           :key="getResourceUrl(character) || character.filename" 
           :src="getResourceUrl(character)!" 
           class="w-full h-full object-cover" 
           :alt="`${character.displayName} Image`">
      <svg v-else class="w-24 h-24 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
      <div v-if="!character.is_private" class="absolute bottom-2 right-2 text-xs bg-gray-600 text-gray-300 px-2 py-0.5 rounded-sm">公共</div>
    </div>

    <div class="p-4 flex-grow flex flex-col">
      <h2 
        class="text-lg font-bold truncate transition-colors"
        :class="isActive ? 'text-cyan-300' : 'text-white group-hover:text-cyan-400'"
      >
        {{ character.displayName }}
      </h2>
      <p class="text-sm text-gray-400 mt-2 flex-grow h-20 overflow-hidden text-ellipsis">
        {{ character.description || '暂无描述' }}
      </p>
    </div>
    
    <div class="p-3 border-t border-gray-600/80 flex justify-end space-x-2">
      <button v-if="character.is_private" @click.stop="emit('share', character)" class="btn btn-secondary !px-3 !py-1 text-xs bg-indigo-600/20 hover:bg-indigo-500/30 border-indigo-500/50 text-indigo-300">分享</button>
      <button v-if="character.is_private" @click.stop="emit('edit', character)" class="btn btn-secondary !px-3 !py-1 text-xs">编辑</button>
      <button @click.stop="emit('delete', character)" class="btn btn-danger !px-3 !py-1 text-xs">删除</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { Character, Filename } from '@/types/api';
import { getResourceUrl } from '~/utils/urlBuilder';

const props = defineProps({
  character: {
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
  (e: 'edit', character: Character): void;
  (e: 'delete', character: Character): void;
  (e: 'share', character: Character): void;
}>();

function handleCardClick() {
  if (!props.isActive) {
    emit('select', props.character.filename);
  }
}
</script>