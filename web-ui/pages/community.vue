<template>
  <div class="h-full w-full p-6 flex flex-col">
    <header class="flex justify-between items-center shrink-0 mb-6">
      <h1 class="text-2xl font-bold text-indigo-300">// 社区内容中心</h1>
      <div class="flex gap-4">
        <!-- 搜索和排序功能未来实现 -->
      </div>
    </header>
    
    <div class="flex-grow min-h-0">
      <CommonTabbedContent :tabs="tabs" initial-tab="characters" theme-color="indigo" class="h-full">
        <template v-for="tab in tabs" :key="tab.id" #[tab.id]>
          <div class="h-full w-full p-4 overflow-y-auto">
            <p class="text-center text-gray-500 py-20">社区内容中心正在建设中...</p>
          </div>
        </template>
      </CommonTabbedContent>
    </div>
  </div>
</template>

<script setup lang="ts">
import CommonTabbedContent from '~/components/common/TabbedContent.vue';

const tabs = [
    { id: 'characters', label: '角色卡' },
    { id: 'presets', label: '预设' },
    { id: 'worlds', label: '世界书' },
];
</script>