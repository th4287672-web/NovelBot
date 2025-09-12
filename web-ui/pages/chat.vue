<template>
  <div class="h-screen w-screen bg-gray-900 text-gray-200 flex flex-col overflow-hidden">
    <!-- 
      [核心修改] 此处不再需要 ChatHeader，因为它被移入了 default 布局或更高层的组件中。
      此页面现在只专注于 chat 区域的布局。
    -->
    <main class="flex-grow min-h-0 flex">
      <!-- 
        [核心优化] 此处的加载状态也直接由 useBootstrapQuery 驱动，
        确保了与 default.vue 布局的逻辑一致性。
      -->
      <div v-if="allData.isLoading.value" class="w-full flex items-center justify-center">
        <div class="flex flex-col items-center gap-4">
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
          <p class="text-lg text-gray-400">正在加载您的数据...</p>
        </div>
      </div>
      <div v-else-if="allData.isError.value" class="w-full flex items-center justify-center">
        <div class="flex flex-col items-center gap-4 text-center p-4">
          <span class="text-5xl">😢</span>
          <p class="text-lg text-red-400">加载数据失败</p>
          <p class="text-sm text-gray-500 max-w-md">{{ allData.error.value?.message || '未知错误，请检查网络连接或API设置。' }}</p>
          <button @click="() => allData.refetch()" class="btn btn-primary mt-4">重试</button>
        </div>
      </div>
      <template v-else-if="allData.isSuccess.value">
        <ClientOnly>
          <!-- 
            [代码注释] OnboardingModal 依赖于 settingsStore 的 hasCompletedOnboarding 状态，
            而这个状态又依赖于 bootstrapQuery 的成功返回，所以这里的逻辑是安全的。
          -->
          <OnboardingModal v-if="!settingsStore.hasCompletedOnboarding && !settingsStore.isAnonymous" />
        </ClientOnly>
        <!-- 
          [核心修改] 此处是 Nuxt 的页面路由出口。
          /chat/index.vue 或 /chat/[session_id].vue 将在这里被渲染。
        -->
        <NuxtPage />
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
// [核心修改] 页面元数据，指定使用空白布局，因为它现在是顶层路由
definePageMeta({
  layout: 'blank', 
});

import { useBootstrapQuery as useAllDataQuery } from '~/composables/useAllData';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import { watch } from 'vue';
import { useCharacterStore } from '~/stores/characterStore';
import { useGroupStore } from '~/stores/groupStore';
import { usePresetStore } from '~/stores/presetStore';
import { useWorldStore } from '~/stores/worldStore';
// [代码注释] 导入并实例化所有数据相关的 store，确保它们在 chat 页面加载时被初始化。
const settingsStore = useSettingsStore();
const sessionStore = useSessionStore();
useCharacterStore();
useGroupStore();
usePresetStore();
useWorldStore();

// [代码注释] 在页面级别获取 bootstrap query 的状态。
const allData = useAllDataQuery();

watch(() => allData.data.value, (newData) => {
    // [代码注释] 当 bootstrap 数据成功加载后，触发加载当前激活角色的会话列表。
    // 这是确保数据流按正确顺序初始化的关键一步。
    if (newData && newData.user_config && newData.user_config.active_character) {
        sessionStore.loadSessionsForCharacter(newData.user_config.active_character);
    }
}, { immediate: true });
</script>