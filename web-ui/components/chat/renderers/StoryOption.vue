<template>
  <div class="mt-2">
    <button @click="handleClick" class="w-full text-left p-2 bg-gray-600 hover:bg-cyan-700 rounded-md transition-colors text-gray-200 text-sm">
      <slot></slot>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '~/stores/chat';
const chatStore = useChatStore();
const slots = useSlots();

function handleClick() {
    const textContent = slots.default?.()?.[0]?.children?.toString() || '';
    if (textContent) {
        chatStore.send(textContent);
    }
}
</script>