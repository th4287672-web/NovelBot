<template>
  <CommonBaseModal :title="`导入默认${dataTypeName}`" :theme-color="themeColor" max-width="48rem" @close="emit('close')">
    <div class="space-y-4">
      <p class="text-sm text-gray-400">
        以下是您已删除的默认{{ dataTypeName }}。选择一项或多项来将其恢复到您的列表中。
      </p>

      <div v-if="importableItems.length > 0" class="max-h-96 overflow-y-auto space-y-2 border-t border-b border-gray-600/80 py-2">
        <label
          v-for="item in importableItems"
          :key="item[itemKey]"
          class="flex items-center p-3 bg-gray-800/60 rounded-sm cursor-pointer hover:bg-gray-700"
        >
          <input
            type="checkbox"
            :value="item[itemKey]"
            v-model="selectedItems"
            class="form-checkbox h-5 w-5 bg-gray-700 border-gray-500 rounded text-cyan-500 focus:ring-cyan-500/50"
          />
          <span class="ml-4 font-semibold text-white">{{ item[itemLabel] }}</span>
        </label>
      </div>
      <div v-else class="text-center py-10 text-gray-500">
        <p>没有可导入的默认{{ dataTypeName }}。</p>
        <p class="text-sm">您似乎没有删除任何系统自带的模板。</p>
      </div>
    </div>

    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button @click="handleImport" :disabled="selectedItems.length === 0" class="btn btn-primary" :style="{ backgroundColor: `var(--color-theme-${themeColor})` }">
        导入已选 ({{ selectedItems.length }})
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue';

type DataItem = Record<string, any>; // [核心修复] 使类型更通用
type ThemeColor = 'cyan' | 'purple' | 'yellow' | 'green' | 'gray' | 'indigo';

const props = defineProps({
  dataTypeName: { type: String, required: true },
  themeColor: { type: String as PropType<ThemeColor>, default: 'gray' },
  importableItems: { type: Array as PropType<DataItem[]>, required: true },
  // [核心修复] 新增 props 以自定义 key 和 label 字段
  itemKey: { type: String, default: 'filename' },
  itemLabel: { type: String, default: 'name' },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'import', keys: (string | number)[]): void; // [核心修复] 明确发出的是 key 的数组
}>();

const selectedItems = ref<(string | number)[]>([]);

function handleImport() {
  if (selectedItems.value.length > 0) {
    emit('import', selectedItems.value);
  }
}
</script>