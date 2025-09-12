<template>
  <div
    class="bg-gray-800/60 p-3 rounded-sm flex items-center border border-gray-600/50 transition-all group"
    :class="{ 'border-purple-500/50': isActive, 'cursor-pointer': !isActive }"
    @click="emit('select', persona.filename)"
  >
    <div class="drag-handle cursor-grab text-gray-500 hover:text-white mr-3 shrink-0">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
    </div>
    <img v-if="getResourceUrl(persona)" :key="persona.image || persona.filename" :src="getResourceUrl(persona)!" class="w-12 h-12 object-cover rounded-md shrink-0" alt="Persona Image">
    <div v-else class="w-12 h-12 bg-gray-700 rounded-md flex items-center justify-center shrink-0">
      <svg class="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    </div>

    <div class="ml-4 flex-grow min-w-0">
      <h3 class="font-semibold truncate" :class="isActive ? 'text-purple-300' : 'text-white'">
        {{ persona.displayName }}
      </h3>
      <p class="text-xs text-gray-400 truncate">{{ persona.description || '暂无描述' }}</p>
    </div>

    <div class="flex items-center space-x-2 ml-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
      <button @click.stop="emit('edit', persona)" class="btn btn-secondary !px-2 !py-1 text-xs" title="编辑">✏️</button>
      <button @click.stop="emit('delete', persona)" class="btn btn-danger !px-2 !py-1 text-xs" title="删除">🗑️</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { Character, Filename } from '~/types/api';
import { getResourceUrl } from '~/utils/urlBuilder';

defineProps({
  persona: { type: Object as PropType<Character>, required: true },
  isActive: { type: Boolean, default: false }
});

const emit = defineEmits<{
  (e: 'select', filename: Filename): void;
  (e: 'edit', persona: Character): void;
  (e: 'delete', persona: Character): void;
}>();
</script>