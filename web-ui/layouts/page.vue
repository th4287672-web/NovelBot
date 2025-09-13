<template>
  <div class="h-full w-full p-6 flex flex-col">
    <header class="flex justify-between items-center shrink-0 mb-6 border-b border-gray-700 pb-4">
      <h1 class="text-2xl font-bold">
        <slot name="title" />
      </h1>
      <div class="flex items-center gap-4">
        <slot name="actions" />
      </div>
    </header>
    <main class="flex-grow min-h-0">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
// 这是一个真正的Nuxt布局，用于提供一致的页眉和内容区域结构。
</script>