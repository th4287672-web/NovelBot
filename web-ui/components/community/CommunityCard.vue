<template>
  <div class="archive-card justify-between group">
    <div class="p-4 flex-grow flex flex-col">
      <h3 class="font-semibold truncate text-indigo-300 group-hover:text-indigo-200">
        {{ item.name }}
      </h3>
      <p class="text-sm text-gray-400 mt-2 flex-grow h-20 overflow-hidden text-ellipsis">
        {{ item.description || '暂无描述' }}
      </p>
      <div class="text-xs text-gray-500 mt-2 flex items-center justify-between">
        <span>作者: {{ item.user_id.substring(0, 8) }}...</span>
        <div class="flex items-center gap-2">
            <span>↓ {{ item.downloads }}</span>
            <span>❤ {{ item.rating.toFixed(1) }}</span>
        </div>
      </div>
    </div>
    <div class="p-3 border-t border-gray-600/80 flex justify-between gap-2">
      <!-- 操作按钮组 -->
      <div class="flex gap-1">
        <button @click.stop="showPlaceholder" class="btn btn-secondary !px-2 !py-1 text-base" title="收藏">⭐</button>
        <button @click.stop="showPlaceholder" class="btn btn-secondary !px-2 !py-1 text-base" title="点赞">❤</button>
        <button @click.stop="showPlaceholder" class="btn btn-secondary !px-2 !py-1 text-base" title="评论">💬</button>
      </div>
      <button 
        @click="emit('import', item)" 
        class="flex-1 btn btn-primary bg-indigo-600 hover:bg-indigo-500 text-sm"
      >
        导入
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import { computed } from 'vue';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { CommunityItem } from '~/types/api';

const props = defineProps({
  item: {
    type: Object as PropType<CommunityItem>,
    required: true,
  }
});

const emit = defineEmits<{
  (e: 'import', item: CommunityItem): void;
}>();

const settingsStore = useSettingsStore();
const uiStore = useUIStore();

function showPlaceholder() {
    uiStore.setGlobalError("该功能正在开发中！");
}
</script>