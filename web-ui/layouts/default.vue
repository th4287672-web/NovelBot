<!-- web-ui/layouts/default.vue -->
<template>
  <div class="flex h-screen w-screen bg-gray-900 text-white overflow-hidden">
    <!-- 
      [核心优化] 使用 v-if/v-else-if/v-else 结构来处理不同的加载状态。
      这比原先单一的 v-if="isReady" 提供了更丰富的用户反馈。
    -->
    <template v-if="bootstrapQuery.isSuccess.value">
      <AppSidebar />
      <main class="relative flex-1 h-full">
        <NuxtPage />
        
        <div 
          v-if="uiStore.isRunSettingsPanelOpen"
          @click="uiStore.toggleRunSettingsPanel"
          class="absolute inset-0 bg-black/30 z-30 transition-opacity"
        ></div>
        
        <ChatRunSettingsPanel />
      </main>
    </template>
    
    <div v-else-if="bootstrapQuery.isLoading.value" class="flex items-center justify-center h-full w-full">
      <div class="flex flex-col items-center text-center p-4">
        <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-cyan-500"></div>
        <p class="mt-4 text-lg text-gray-400">正在连接并同步数据...</p>
      </div>
    </div>

    <div v-else-if="bootstrapQuery.isError.value" class="flex items-center justify-center h-full w-full">
        <div class="flex flex-col items-center gap-4 text-center p-4">
          <span class="text-5xl">😢</span>
          <p class="text-lg text-red-400">数据加载失败</p>
          <p class="text-sm text-gray-500 max-w-md break-all">{{ bootstrapQuery.error.value?.message || '未知错误，请检查网络连接或刷新页面。' }}</p>
          <button @click="() => bootstrapQuery.refetch()" class="btn btn-primary mt-4">
            重试
          </button>
        </div>
    </div>
    
    <DevLogViewer />
    <TaskCenter />
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '~/components/AppSidebar.vue';
import DevLogViewer from '~/components/DevLogViewer.vue';
import TaskCenter from '~/components/common/TaskCenter.vue';
import ChatRunSettingsPanel from '~/components/chat/RunSettingsPanel.vue';
import { useUIStore } from '~/stores/ui';
// [核心优化] 直接在布局中使用 useBootstrapQuery 来驱动UI状态
import { useBootstrapQuery } from '~/composables/useAllData';

const uiStore = useUIStore();
const bootstrapQuery = useBootstrapQuery();
</script>