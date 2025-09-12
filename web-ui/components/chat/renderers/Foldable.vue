<template>
  <details class="mb-3 border-l-2 border-yellow-500/30 pl-3">
    <summary class="text-xs text-yellow-400/60 cursor-pointer select-none">
      {{ title }} <span class="italic opacity-50">(点击展开/折叠)</span>
    </summary>
    <div class="mt-1 p-2 bg-black/20 rounded text-sm text-gray-300 whitespace-pre-wrap font-mono">
      <!-- [核心修复] 使用 <component :is=".."> 来渲染插槽内容 -->
      <component :is="() => $slots.default ? $slots.default() : null" />
    </div>
  </details>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
}>();
</script>