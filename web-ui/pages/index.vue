<template>
  <div class="flex flex-col items-center justify-center h-full text-gray-500">
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
    <p class="mt-4 text-lg">正在导航...</p>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '~/stores/sessionStore';
import { storeToRefs } from 'pinia';

onMounted(() => {
  const sessionStore = useSessionStore();
  const { activeSessionId } = storeToRefs(sessionStore);

  const route = activeSessionId.value ? `/chat/${activeSessionId.value}` : '/chat/new';
  navigateTo(route, { replace: true });
});
</script>