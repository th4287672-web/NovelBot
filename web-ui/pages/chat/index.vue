<template>
  <div class="flex flex-col items-center justify-center h-full w-full text-gray-500">
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
    <p class="mt-4 text-lg">正在准备聊天环境...</p>
  </div>
</template>

<script setup lang="ts">
// 这个页面的唯一职责就是存在，以便中间件可以拦截到 /chat 路由。
// 所有的跳转逻辑现在都在 middleware/chat-redirect.global.ts 中处理。
</script>