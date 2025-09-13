<template>
  <div class="h-full w-full p-6 flex flex-col">
    <header class="flex justify-between items-center shrink-0 mb-6 border-b border-gray-700 pb-4">
      <h1 class="text-2xl font-bold truncate min-w-0">
        <slot name="title">页面标题</slot>
      </h1>
      <div class="flex items-center gap-4 shrink-0">
        <slot name="actions"></slot>
      </div>
    </header>
    <main class="flex-grow min-h-0">
      <slot></slot>
    </main>
  </div>
</template>

<script setup lang="ts">
</script>