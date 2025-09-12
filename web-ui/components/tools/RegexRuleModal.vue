<template>
  <CommonBaseModal :title="modalTitle" theme-color="indigo" @close="emit('close')" max-width="80rem">
    <div class="space-y-4">
      <div>
        <label for="ruleName" class="archive-label">规则名称 (必填)</label>
        <input id="ruleName" v-model="localRule.name" type="text" placeholder="例如：折叠思维链" class="archive-input focus:border-indigo-500" />
      </div>
      <div>
        <label for="rulePattern" class="archive-label">正则表达式 (Pattern)</label>
        <textarea id="rulePattern" v-model="localRule.pattern" rows="3" class="archive-textarea font-mono text-sm focus:border-indigo-500" placeholder="<think_internal>([\\s\\S]*?)<\\/think_internal>"></textarea>
      </div>
      <div>
        <label for="ruleTemplate" class="archive-label">替换模板 (Template)</label>
        <textarea id="ruleTemplate" v-model="localRule.template" rows="3" class="archive-textarea font-mono text-sm focus:border-indigo-500" placeholder="<Foldable title='思维链'>$1</Foldable>"></textarea>
         <p class="text-xs text-gray-500 mt-1">
          使用 `$1`, `$2` 等来引用正则表达式中的捕获组。
        </p>
      </div>
      <div class="pt-2">
        <label class="flex items-center cursor-pointer">
          <input type="checkbox" v-model="localRule.enabled" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-indigo-500 focus:ring-indigo-600" />
          <span class="ml-2 text-sm text-gray-300">启用此规则</span>
        </label>
      </div>

      <!-- [新增] 集成预览组件 -->
      <RegexPreview :rule="localRule" />

    </div>

    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button @click="handleSave" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500">保存规则</button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, type PropType } from 'vue';
import type { RegexRule } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import CommonBaseModal from '~/components/common/BaseModal.vue';
// [新增] 导入预览组件
import RegexPreview from './RegexPreview.vue';

const props = defineProps({
  rule: {
    type: Object as PropType<RegexRule | null>,
    required: true,
  },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', rule: RegexRule): void;
}>();

const localRule = ref<RegexRule>({ id: '', name: '', pattern: '', template: '', enabled: true });

watch(() => props.rule, (newRule) => {
  if (newRule) {
    localRule.value = deepClone(newRule);
  }
}, { immediate: true });

const modalTitle = computed(() => (localRule.value && localRule.value.name) ? `编辑规则: ${localRule.value.name}` : '创建新规则');

function handleSave() {
  if (!localRule.value.name.trim() || !localRule.value.pattern.trim()) {
    alert('规则名称和正则表达式不能为空！');
    return;
  }
  emit('save', localRule.value);
}
</script>