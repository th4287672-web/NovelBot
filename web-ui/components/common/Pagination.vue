<template>
  <nav v-if="totalPages > 1" class="flex items-center justify-center space-x-2 text-sm">
    <button
      @click="goToPage(currentPage - 1)"
      :disabled="currentPage === 1"
      class="px-3 py-1 rounded-md bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      &lt;
    </button>
    <template v-for="page in pages" :key="page">
      <span v-if="page === '...'" class="px-3 py-1 text-gray-400">...</span>
      <button
        v-else
        @click="goToPage(page as number)"
        class="px-3 py-1 rounded-md"
        :class="page === currentPage
          ? 'bg-cyan-600 text-white font-bold'
          : 'bg-gray-700 hover:bg-gray-600'"
      >
        {{ page }}
      </button>
    </template>
    <button
      @click="goToPage(currentPage + 1)"
      :disabled="currentPage === totalPages"
      class="px-3 py-1 rounded-md bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      &gt;
    </button>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  maxVisibleButtons: { type: Number, default: 7 }
});

const emit = defineEmits(['page-change']);

const pages = computed<(number | string)[]>(() => {
  if (props.totalPages <= props.maxVisibleButtons) {
    return Array.from({ length: props.totalPages }, (_, i) => i + 1);
  }

  const pagesArray: (number | string)[] = [];
  const half = Math.floor(props.maxVisibleButtons / 2);

  pagesArray.push(1);

  let start = Math.max(2, props.currentPage - half + 1);
  let end = Math.min(props.totalPages - 1, props.currentPage + half - 1);

  if (props.currentPage <= half) {
    end = props.maxVisibleButtons - 2;
  }
  if (props.currentPage > props.totalPages - half) {
    start = props.totalPages - props.maxVisibleButtons + 3;
  }
  
  if (start > 2) {
    pagesArray.push('...');
  }
  for (let i = start; i <= end; i++) {
    pagesArray.push(i);
  }
  if (end < props.totalPages - 1) {
    pagesArray.push('...');
  }

  pagesArray.push(props.totalPages);
  return pagesArray;
});

function goToPage(page: number) {
  if (page >= 1 && page <= props.totalPages) {
    emit('page-change', page);
  }
}
</script>