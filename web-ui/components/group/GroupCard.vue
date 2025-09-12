<template>
  <div class="archive-card group transform hover:-translate-y-1 transition-transform duration-200">
    <div class="p-4 flex-grow flex flex-col">
      <h2 class="text-lg font-bold truncate text-indigo-300 group-hover:text-indigo-200">
        {{ group.name }}
      </h2>
      <p class="text-sm text-gray-400 mt-2 flex-grow h-20 overflow-hidden text-ellipsis">
        {{ group.description || '暂无描述' }}
      </p>
       <p class="text-xs text-gray-500 mt-2">
        {{ group.character_filenames.length }} 个角色
      </p>
    </div>
    
    <div class="p-3 border-t border-gray-600/80 flex justify-end space-x-2">
      <button @click.stop="emit('edit', group)" class="btn btn-secondary !px-3 !py-1 text-xs">编辑</button>
      <button @click.stop="emit('delete', group)" class="btn btn-danger !px-3 !py-1 text-xs">删除</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { Group } from '@/types/api';

defineProps({
  group: {
    type: Object as PropType<Group>,
    required: true,
  }
});

const emit = defineEmits<{
  (e: 'edit', group: Group): void;
  (e: 'delete', group: Group): void;
}>();
</script>
