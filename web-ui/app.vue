<template>
  <ClientOnly>
    <NuxtLayout />
    
    <template #fallback>
      <div class="flex items-center justify-center h-screen w-screen bg-gray-900 text-white">
        <div class="flex flex-col items-center">
          <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-cyan-500"></div>
          <p class="mt-4 text-lg text-gray-400">正在加载应用...</p>
        </div>
      </div>
    </template>
  </ClientOnly>
</template>

<script setup lang="ts">
import { useSettingsStore } from '~/stores/settings';
import { storeToRefs } from 'pinia';

const settingsStore = useSettingsStore();
const { isReady, isAnonymous } = storeToRefs(settingsStore);
</script>