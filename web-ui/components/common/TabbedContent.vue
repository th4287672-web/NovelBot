<template>
  <div class="flex flex-col h-full">
    <nav class="flex border-b border-gray-600/80 px-4 shrink-0">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="py-2.5 px-4 text-sm font-medium border-b-2 transition-colors duration-200"
        :class="activeTab === tab.id
          ? 'text-white'
          : 'border-transparent text-gray-400 hover:text-white'"
        :style="activeTab === tab.id ? { borderColor: `var(--color-theme-${themeColor})` } : {}"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>
    <div class="flex-grow min-h-0">
      <template v-for="tab in tabs" :key="tab.id">
        <div v-if="activeTab === tab.id" class="h-full">
          <slot :name="tab.id"></slot>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue';

// [核心修复] 将 'indigo' 添加到类型定义中
type ThemeColor = 'cyan' | 'purple' | 'yellow' | 'green' | 'gray' | 'indigo';

interface Tab {
  id: string;
  label: string;
}

const props = defineProps({
  tabs: {
    type: Array as PropType<Tab[]>,
    required: true,
  },
  initialTab: {
    type: String,
    required: true,
  },
  themeColor: {
    type: String as PropType<ThemeColor>,
    default: 'gray',
  },
});

const activeTab = ref<string>(props.initialTab);
</script>