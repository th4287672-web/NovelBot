<template>
  <div class="flex flex-col items-center justify-center h-full text-gray-500">
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
    <p class="mt-4 text-lg">正在查找会话并跳转...</p>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import { storeToRefs } from 'pinia';

const sessionStore = useSessionStore();
const settingsStore = useSettingsStore();

const { activeSessionId } = storeToRefs(sessionStore);
const { isReady } = storeToRefs(settingsStore);

watch(
  () => [isReady.value, activeSessionId.value],
  async ([ready, sessionId]) => {
    // [优化] 增加一个检查，确保 sessionId 存在才跳转
    if (ready && sessionId) {
      await nextTick();
      await navigateTo(`/chat/${sessionId}`, { replace: true });
    }
  }, 
  { immediate: true }
);
</script>