<template>
  <div class="h-full w-full flex flex-col overflow-hidden">
    <ChatHeader />
    <main class="flex-grow min-h-0 flex">
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
          <OnboardingModal v-if="!settingsStore.hasCompletedOnboarding && !settingsStore.isAnonymous" />
        </ClientOnly>
        <NuxtPage />
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useBootstrapQuery as useAllDataQuery } from '~/composables/useAllData';
import { useSettingsStore } from '~/stores/settings';
import ChatHeader from '~/components/chat/ChatHeader.vue';

const settingsStore = useSettingsStore();
const allData = useAllDataQuery();
</script>