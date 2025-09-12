<template>
  <div class="mt-4 border-t border-gray-700 pt-4 space-y-3">
    <h4 class="text-base font-semibold text-gray-300">实时预览</h4>
    <div>
      <label for="previewSource" class="text-xs text-gray-400">源文本</label>
      <textarea 
        id="previewSource"
        v-model="sourceText"
        rows="4"
        class="archive-textarea font-mono text-sm"
        placeholder="在这里输入文本来测试你的规则..."
      ></textarea>
    </div>
    <div>
      <label class="text-xs text-gray-400">效果预览</label>
      <div class="mt-1 p-3 min-h-[8rem] bg-gray-900 rounded-md border border-gray-600">
        <!-- 使用 ContentRenderer 来显示最终效果 -->
        <ContentRenderer :content="previewContent" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue';
import type { RegexRule } from '~/types/api';
// [FIX] 更新导入路径以指向新的 .client.vue 文件
import ContentRenderer from '~/components/chat/ContentRenderer.client.vue';

const props = defineProps<{
  rule: RegexRule;
}>();

const sourceText = ref('');

// [核心修复] 创建一个示例映射表
const exampleTextMap: Record<string, string> = {
  '折叠思维链': '<think_internal>\n这是AI的思考过程。\n1. 分析用户意图。\n2. 制定回复策略。\n</think_internal>',
  '渲染剧情选项': '现在你有两个选择：\n[选项1]接受挑战，勇往直前。[/选项1]\n[选项2]保持沉默，静观其变。[/选项2]',
  '加粗 **文本**': '这段话里有 **非常重要** 的内容。',
  '斜体 *文本*': '她 *轻声地* 说了一句话。',
  '高亮 ==文本==': '警告：==核心区域即将过载==！',
  '剧透 ||文本||': '那个角色的真实身份其实是||一个机器人||。',
  '渲染表格 (JSON)': '<Table>\n<!--\n[\n  {"ID": 1, "姓名": "爱丽丝", "职业": "法师"},\n  {"ID": 2, "姓名": "鲍勃", "职业": "战士"}\n]\n-->\n</Table>',
  '渲染表格 (快捷JSON)': '|||table\n[\n  {"ID": 3, "姓名": "查理", "职业": "盗贼"}\n]\n|||',
  '渲染ECharts图表 (JSON)': '<ECharts>\n<!--\n{\n  "title": { "text": "伤害统计" },\n  "series": [{ "type": "pie", "data": [{"value":10, "name":"A"}, {"value":20, "name":"B"}] }]\n}\n-->\n</ECharts>',
  // [核心新增] 为平面图规则添加示例
  '渲染平面图 (JSON)': '<FloorPlan>\n<!--\n{\n  "rooms": [\n    {"id": "lr", "name": "客厅", "rect": [0, 0, 6, 4]},\n    {"id": "br", "name": "卧室", "rect": [6, 0, 4, 4]}\n  ],\n  "doors": [\n    {"pos": [6, 2], "width": 0.2, "height": 1}\n  ]\n}\n-->\n</FloorPlan>',
  '渲染进度条': '任务进度：<progress value="60" max="100" label="文件下载"></progress>',
  '渲染地图 (Base64)': '我们在地图上的位置：<map lat="31.23" lng="121.47" markers-base64="W3sibGF0IjozMS4yMywibG5nIjoxMjEuNDcsInBvcHVwIjoi5LiT5Z2h55yB5Lit5b+DIn1d"></map>',
  '信息卡片': '<card title="任务简报">\n这是本次任务的核心目标和注意事项。\n</card>',
  '骰子结果': '你的攻击检定结果是 [骰子: 1d20+5 = 18]。',
};

// [核心修复] 使用 watchEffect 动态更新示例文本
watchEffect(() => {
  sourceText.value = exampleTextMap[props.rule.name] || '请在这里输入您自己的测试文本...';
});

const previewContent = computed(() => {
  if (!props.rule.pattern || !sourceText.value) {
    return sourceText.value;
  }
  try {
    const regex = new RegExp(props.rule.pattern, 'gs');
    return sourceText.value.replace(regex, props.rule.template);
  } catch (e) {
    if (e instanceof Error) {
      return `[正则表达式错误: ${e.message}]`;
    }
    return '[正则表达式错误: 未知错误类型]';
  }
});
</script>