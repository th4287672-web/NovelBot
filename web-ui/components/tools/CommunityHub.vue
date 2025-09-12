<template>
  <div class="h-full w-full flex flex-col">
    <CommonTabbedContent 
      :tabs="tabs" 
      :initial-tab="communityStore.activeTab"
      @update:active-tab="communityStore.activeTab = $event"
      theme-color="indigo" 
      class="flex-grow min-h-0"
    >
      <template v-for="tab in tabs" :key="tab.id" #[tab.id]>
        <div class="h-full w-full p-4 overflow-y-auto">
          <div v-if="communityStore.isLoading" class="flex items-center justify-center h-full">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-400"></div>
          </div>
          <div v-else-if="communityStore.items.length === 0" class="text-center py-20 text-gray-500">
            <p>社区还没有人分享{{ tab.label }}。</p>
            <p class="text-sm">去成为第一个分享的人吧！</p>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            <CommunityCard 
              v-for="item in communityStore.items" 
              :key="item.id" 
              :item="item"
              @import="handleImport"
            />
          </div>
        </div>
      </template>
    </CommonTabbedContent>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useCommunityStore } from '~/stores/communityStore';
import CommonTabbedContent from '~/components/common/TabbedContent.vue';
import CommunityCard from '~/components/community/CommunityCard.vue';
import type { CommunityItem } from '~/types/api';

const communityStore = useCommunityStore();

const tabs = [
    { id: 'character', label: '角色' },
    { id: 'preset', label: '预设' },
    { id: 'world_info', label: '世界书' },
];

onMounted(() => {
    communityStore.browseContent();
});

watch(() => communityStore.activeTab, () => {
    communityStore.browseContent();
});

function handleImport(item: CommunityItem) {
    communityStore.importContent(item.id);
}
</script>