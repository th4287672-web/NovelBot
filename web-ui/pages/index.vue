<template>
  <div class="flex flex-col items-center justify-center h-full text-gray-500">
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
    <p class="mt-4 text-lg">正在导航...</p>
  </div>
</template>

<script setup lang="ts">
// [核心修复] 此页面现在只负责一件事：将用户重定向到核心聊天页面。
onMounted(() => {
  navigateTo('/chat', { replace: true });
});
</script>