<template>
  <CommonBaseModal :title="`分享您的${dataTypeName}`" theme-color="indigo" max-width="80rem" @close="emit('close')">
    <div class="space-y-4">
      <div>
        <label class="archive-label">分享项目</label>
        <p class="font-semibold text-white p-2 bg-gray-700/50 rounded-md">{{ itemToShare.displayName || itemToShare.name }}</p>
      </div>
      <div>
        <label for="share-description" class="archive-label">描述 (必填)</label>
        <textarea 
          id="share-description" 
          v-model="description" 
          rows="4" 
          class="archive-textarea focus:border-indigo-500"
          placeholder="简单介绍一下它的特点、用途或背景故事..."
          maxlength="500"
        ></textarea>
        <p class="text-xs text-right text-gray-500">{{ description.length }} / 500</p>
      </div>
      <div>
        <label for="share-tags" class="archive-label">标签 (可选, 用逗号分隔)</label>
        <input 
          id="share-tags" 
          v-model="tagsInput" 
          type="text" 
          class="archive-input focus:border-indigo-500"
          placeholder="例如: 科幻, 赛博朋克, 侦探"
        />
      </div>
    </div>
    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button 
        @click="handleShare" 
        :disabled="!description.trim() || communityStore.isSharing" 
        class="btn btn-primary bg-indigo-600 hover:bg-indigo-500"
      >
        <span v-if="communityStore.isSharing" class="animate-pulse">分享中...</span>
        <span v-else>确认并分享</span>
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import { useCommunityStore } from '~/stores/communityStore';
import type { CommunityItemType } from '~/types/api';

interface ShareableItem {
  filename: string;
  name: string;
  displayName?: string;
}

const props = defineProps({
  itemToShare: {
    type: Object as PropType<ShareableItem>,
    required: true,
  },
  dataType: {
    type: String as PropType<CommunityItemType>,
    required: true,
  }
});

const emit = defineEmits(['close']);

const communityStore = useCommunityStore();
const description = ref('');
const tagsInput = ref('');

const dataTypeName = computed(() => {
  const names = {
    'character': '角色',
    'preset': '预设',
    'world_info': '世界书',
  };
  return names[props.dataType] || '内容';
});

async function handleShare() {
  const success = await communityStore.shareContent({
    data_type: props.dataType,
    filename: props.itemToShare.filename,
    description: description.value,
    tags: tagsInput.value.split(',').map(t => t.trim()).filter(Boolean),
  });
  if (success) {
    emit('close');
  }
}
</script>