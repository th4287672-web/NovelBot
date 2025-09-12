<template>
  <div
    class="archive-card justify-between group"
    :class="isActive ? 'border-green-500/50' : 'hover:border-gray-500'"
  >
    <div class="p-4">
      <h3 class="text-lg font-semibold truncate" :class="isActive ? 'text-green-300' : 'text-white'">
        {{ preset.displayName }}
      </h3>
      <div v-if="!preset.is_private" class="absolute top-2 right-2 text-xs bg-gray-600 text-gray-300 px-2 py-0.5 rounded-sm">公共</div>
      <p class="text-sm text-gray-400 mt-2">
        {{ preset.prompts?.length ?? 0 }} 个模块
      </p>
    </div>
    <div class="p-3 border-t border-gray-600/80 flex space-x-2">
      <button 
        @click="emit('select', preset.filename)" 
        class="flex-1 btn text-sm"
        :class="isActive ? 'bg-green-600 text-white cursor-default' : 'btn-secondary'"
        :disabled="isActive"
      >
        {{ isActive ? '已激活' : '激活' }}
      </button>
      <button 
        @click="emit('manage', preset)" 
        class="btn btn-secondary !p-2 text-sm" 
        title="管理预设"
      >
        ⚙️
      </button>
       <button 
        v-if="preset.is_private"
        @click="emit('share', preset)"
        class="btn btn-secondary !p-2 text-sm bg-indigo-600/20 hover:bg-indigo-500/30 border-indigo-500/50 text-indigo-300"
        title="分享预设"
       >
        🔗
       </button>
       <button 
        v-if="preset.is_private"
        @click="emit('delete', preset)" 
        class="btn btn-danger !p-2 text-sm" 
        title="删除预设"
      >
        🗑️
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { Preset, Filename } from '~/types/api';

defineProps({
  preset: {
    type: Object as PropType<Preset>,
    required: true,
  },
  isActive: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: 'select', filename: Filename): void;
  (e: 'manage', preset: Preset): void;
  (e: 'delete', preset: Preset): void;
  (e: 'share', preset: Preset): void;
}>();
</script>