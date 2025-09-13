<template>
  <div 
    :class="[
      'flex flex-col text-white h-full',
      !isContained && 'p-6 bg-gray-900'
    ]"
  >
    <header 
      v-if="!isContained"
      class="flex justify-between items-center shrink-0 mb-6"
    >
      <h1 class="text-2xl font-bold">
        <slot name="title">管理页面</slot>
      </h1>
      <div @click="emit('create')">
        <slot name="create-button-content">
          <button class="btn btn-primary">创建新的</button>
        </slot>
      </div>
    </header>
    
    <main 
      class="flex-grow overflow-y-auto min-h-0"
      :class="{ 'mt-6': !isContained, 'pr-2 -mr-2': !isContained }"
    >
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-cyan-500"></div>
      </div>
      
      <div v-else-if="!isEmpty">
        <slot></slot>
      </div>

      <div v-else class="text-center py-20 bg-gray-800/50 rounded-lg">
        <slot name="empty-state">
          <p class="text-gray-400 text-lg">这里什么都没有。</p>
          <p class="text-gray-500 mt-2">点击右上角的按钮来创建第一个项目吧！</p>
        </slot>
      </div>
    </main>

    <footer v-if="!isLoading && !isEmpty && !isContained" class="shrink-0 pt-4">
        <slot name="footer"></slot>
    </footer>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isLoading: boolean;
  isEmpty: boolean;
  isContained?: boolean;
}>();

const emit = defineEmits<{
  (e: 'create'): void;
}>();
</script>