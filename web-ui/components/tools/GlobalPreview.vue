<template>
  <div class="h-full flex flex-col bg-gray-800/50 rounded-lg border border-gray-700">
    <header class="p-3 border-b border-gray-700 shrink-0">
      <h3 class="font-semibold text-gray-200">全局实时预览</h3>
    </header>
    
    <div class="flex-grow p-4 space-y-3 overflow-y-auto">
      <div>
        <div class="flex justify-between items-center mb-1">
          <label for="global-source" class="text-xs text-gray-400">源文本 (包含所有规则的测试用例)</label>
          <button @click="resetSourceText" class="text-xs text-cyan-400 hover:underline">重置为默认</button>
        </div>
        <textarea 
          id="global-source"
          v-model="sourceText"
          rows="8"
          class="archive-textarea font-mono text-sm"
        ></textarea>
      </div>
      <div>
        <label class="text-xs text-gray-400">最终渲染效果</label>
        <div class="mt-1 p-3 min-h-[12rem] bg-gray-900 rounded-md border border-gray-600">
          <ContentRenderer :content="previewContent" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import type { RegexRule } from '~/types/api';
import ContentRenderer from '~/components/chat/ContentRenderer.client.vue';

const props = defineProps<{
  rules: RegexRule[];
}>();

// [核心修复] 更新默认示例文本，加入校园平面图
const defaultSourceText = `<think_internal>
AI思考：用户需要一个复杂的校园平面图来测试新功能。
</think_internal>

这是一个校园的平面图：
<FloorPlan>
<!--
{
  "areas": [
    {"id": "lawn", "rect": [0, 0, 50, 30], "fill": "#2F855A"}
  ],
  "rooms": [
    {"id": "lib", "name": "图书馆", "rect": [5, 5, 15, 10], "fill": "#B794F4"},
    {"id": "gym", "name": "体育馆", "rect": [30, 15, 15, 10], "fill": "#F56565"}
  ],
  "paths": [
    {"d": "M 20 10 L 30 10 L 35 15", "stroke": "#A0AEC0", "strokeWidth": 0.5}
  ],
  "objects": [
    {"shape": "circle", "pos": [3, 3], "size": [1.5, 1.5], "fill": "#48BB78"},
    {"shape": "circle", "pos": [45, 10], "size": [2, 2], "fill": "#48BB78"}
  ],
  "labels": [
    {"text": "校园中心广场", "pos": [25, 20], "fontSize": 1.5, "fill": "#F7FAFC"}
  ]
}
-->
</FloorPlan>

这是一个ECharts图表示例：
<ECharts>
<!--
{
  "title": { "text": "笔使图谱" },
  "xAxis": { "data": ["话证板", "美每证板", "集网证板"] },
  "yAxis": {},
  "series": [{ "name": "产出量", "type": "bar", "data": [5, 20, 36] }]
}
-->
</ECharts>
`;

const sourceText = ref(defaultSourceText);

function resetSourceText() {
  sourceText.value = defaultSourceText;
}

const previewContent = computed(() => {
  let tempContent = sourceText.value;
  const enabledRules = props.rules.filter(rule => rule.enabled && rule.pattern);

  if (!enabledRules.length) {
    return tempContent;
  }

  for (const rule of enabledRules) {
    try {
      const regex = new RegExp(rule.pattern, 'gs');
      tempContent = tempContent.replace(regex, rule.template);
    } catch (e) {
      console.warn(`Skipping invalid regex for rule "${rule.name}":`, e);
    }
  }
  return tempContent;
});
</script>