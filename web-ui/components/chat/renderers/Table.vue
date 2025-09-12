<template>
  <div v-if="parseError" class="my-2 text-xs text-red-400 p-2 bg-red-900/30 rounded">
    [表格渲染错误: {{ parseError }}]
  </div>
  <div v-else class="overflow-x-auto my-2">
    <table class="min-w-full border-collapse border border-gray-600 text-sm">
      <thead v-if="tableData.headers.length > 0">
        <tr class="bg-gray-700">
          <th
            v-for="(header, index) in tableData.headers"
            :key="index"
            class="border border-gray-600 px-4 py-2 text-left font-semibold text-gray-200"
          >
            {{ header }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in tableData.rows"
          :key="rowIndex"
          :class="rowIndex % 2 === 0 ? 'bg-gray-800/50' : 'bg-gray-900/50'"
        >
          <td
            v-for="(cell, cellIndex) in row"
            :key="cellIndex"
            class="border border-gray-600 px-4 py-2 text-gray-300"
          >
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue';

const slots = useSlots();
const parseError = ref<string | null>(null);

const tableData = computed(() => {
  parseError.value = null;
  const defaultSlot = slots.default?.();
  const rawContent = defaultSlot?.[0]?.children?.toString() || '';

  // 1. 提取HTML注释中的内容
  const commentMatch = rawContent.match(/<!--([\s\S]*)-->/);
  const jsonString = commentMatch?.[1]?.trim();

  if (!jsonString) {
    parseError.value = "在 <Table> 标签内未找到有效的JSON注释块。";
    return { headers: [], rows: [] };
  }

  // 2. 解析JSON
  try {
    const jsonData = JSON.parse(jsonString);
    if (!Array.isArray(jsonData) || jsonData.length === 0) {
      parseError.value = "JSON数据不是一个有效的非空数组。";
      return { headers: [], rows: [] };
    }

    const firstItem = jsonData[0];
    if (typeof firstItem !== 'object' || firstItem === null) {
      parseError.value = "JSON数组中的项目不是有效的对象。";
      return { headers: [], rows: [] };
    }

    const headers = Object.keys(firstItem);
    const rows = jsonData.map(item => headers.map(header => item[header] ?? ''));
    
    return { headers, rows };
  } catch (e) {
    console.error('解析表格JSON失败:', e);
    parseError.value = e instanceof Error ? e.message : "未知的JSON解析错误";
    return { headers: [], rows: [] };
  }
});
</script>