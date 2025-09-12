<template>
  <div class="my-2 p-2 bg-gray-800 border border-gray-700 rounded-lg">
    <div v-if="parseError" class="text-xs text-red-400 p-2 bg-red-900/30 rounded">
      [ECharts渲染错误: {{ parseError }}]
    </div>
    <div v-else ref="chartContainer" class="w-full h-80"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect, useSlots } from 'vue';
import { useEcharts } from '~/composables/useEcharts';

const chartContainer = ref<HTMLElement | null>(null);
const { setOption } = useEcharts(chartContainer);
const parseError = ref<string | null>(null);
const slots = useSlots();

const chartOption = computed(() => {
  parseError.value = null;
  const defaultSlot = slots.default?.();
  const rawContent = defaultSlot?.[0]?.children?.toString() || '';

  // 1. 提取HTML注释中的内容
  const commentMatch = rawContent.match(/<!--([\s\S]*)-->/);
  const jsonString = commentMatch?.[1]?.trim();

  if (!jsonString) {
    parseError.value = "在 <ECharts> 标签内未找到有效的JSON注释块。";
    return null;
  }

  // 2. 解析JSON
  try {
    const jsonData = JSON.parse(jsonString);
    if (typeof jsonData !== 'object' || jsonData === null) {
      parseError.value = "解析出的内容不是一个有效的JSON对象。";
      return null;
    }
    
    // [核心修复] 为 yAxis 提供默认值
    if (jsonData.series?.some((s: any) => ['bar', 'line'].includes(s.type)) && !jsonData.yAxis) {
        jsonData.yAxis = { type: 'value' };
    }

    return jsonData;
  } catch (e) {
    console.error("解析ECharts配置失败:", e);
    parseError.value = e instanceof Error ? e.message : "未知的JSON解析错误";
    return null;
  }
});

watchEffect(() => {
  if (chartOption.value && chartContainer.value) {
    setOption(chartOption.value, true);
  }
});
</script>