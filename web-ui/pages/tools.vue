<template>
  <div class="h-full w-full flex flex-col">
    <header class="p-3 border-b border-gray-700 bg-gray-800/50 shrink-0">
      <h1 class="text-xl font-semibold text-gray-200 text-center">工具箱</h1>
    </header>
    
    <CommonTabbedContent :tabs="tabs" initial-tab="rules" theme-color="indigo" class="flex-grow min-h-0">
      
      <template #rules>
        <div class="h-full w-full p-6 flex gap-6 overflow-hidden">
          <div class="w-1/2 h-full flex flex-col">
            <ManagementLayout
              :is-loading="!isReady"
              :is-empty="false"
              @create="openModal()"
              :is-contained="true"
            >
              <template #title>// 渲染规则管理</template>
              <template #create-button-content>
                <div class="flex gap-4">
                  <button @click.stop="isImportModalOpen = true" class="btn btn-secondary">导入默认</button>
                  <button class="btn btn-primary bg-indigo-600 hover:bg-indigo-500">
                    添加新规则
                  </button>
                </div>
              </template>
              
              <div class="space-y-3 h-full overflow-y-auto pr-2">
                <div 
                  v-for="(rule, index) in localRules" 
                  :key="rule.id"
                  class="p-3 bg-gray-800/60 rounded-md border border-gray-700 flex items-center justify-between transition-all"
                  :draggable="true"
                  @dragstart="onDragStart($event, index)"
                  @dragover.prevent="onDragOver($event)"
                  @dragleave="onDragLeave($event)"
                  @drop="onDrop($event, index)"
                  @dragend="onDragEnd($event)"
                >
                  <div class="flex items-center min-w-0">
                    <div class="drag-handle cursor-grab text-gray-500 hover:text-white mr-3 shrink-0">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
                    </div>
                    <span 
                      class="w-4 h-4 rounded-full mr-4 shrink-0"
                      :class="rule.enabled ? 'bg-green-500' : 'bg-gray-600'"
                      :title="rule.enabled ? '已启用' : '已禁用'"
                    ></span>
                    <span class="font-semibold text-white truncate">{{ rule.name }}</span>
                  </div>
                  <div class="flex items-center space-x-3">
                    <button @click="openModal(rule)" class="btn btn-secondary !px-3 !py-1 text-xs">编辑</button>
                    <button @click="removeRule(index)" class="btn btn-danger !px-3 !py-1 text-xs">删除</button>
                  </div>
                </div>
              </div>
            </ManagementLayout>
          </div>

          <div class="w-1/2 h-full">
              <GlobalPreview :rules="localRules" />
          </div>
        </div>
      </template>

      <template #story_weaver>
        <ToolsStoryWeaver />
      </template>

      <template #drawing>
        <ToolsDrawingTool />
      </template>

      <template #tts>
        <ToolsTtsTool />
      </template>

      <template #data>
        <ToolsDataCenter />
      </template>

      <template #community>
        <ToolsCommunityHub />
      </template>

    </CommonTabbedContent>
    
    <ClientOnly>
        <ToolsRegexRuleModal
            v-if="isModalOpen"
            :rule="editingRule"
            @close="closeModal"
            @save="handleSaveRule"
        />
        <CommonImportModal
            v-if="isImportModalOpen"
            data-type-name="渲染规则"
            theme-color="indigo"
            :importable-items="importableRegexRules"
            item-key="id"
            item-label="name"
            @close="isImportModalOpen = false"
            @import="handleImport"
        />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore, defaultRules } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import { useDraggable } from '~/composables/useDraggable';
import type { RegexRule } from '~/types/api';
import { v4 as uuidv4 } from 'uuid';
import { deepClone } from '~/utils/helpers';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import ToolsRegexRuleModal from '~/components/tools/RegexRuleModal.vue';
import GlobalPreview from '~/components/tools/GlobalPreview.vue';
import CommonTabbedContent from '~/components/common/TabbedContent.vue';
import ToolsStoryWeaver from '~/components/tools/StoryWeaver.vue';
import ToolsCommunityHub from '~/components/tools/CommunityHub.vue';


const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const { isReady, regexRules, importableRegexRules } = storeToRefs(settingsStore);

const localRules = ref<RegexRule[]>([]);
const isModalOpen = ref(false);
const editingRule = ref<RegexRule | null>(null);
const isImportModalOpen = ref(false);

const tabs = [
    { id: 'rules', label: '渲染规则' },
    { id: 'story_weaver', label: '故事编织者' },
    { id: 'drawing', label: 'AI 绘画' },
    { id: 'tts', label: '语音合成 (TTS)' },
    { id: 'data', label: '数据中心' },
    { id: 'community', label: '社区分享' },
];

watch(regexRules, (newRules) => {
    if (newRules && newRules.length > 0) {
        localRules.value = deepClone(newRules);
    } else if (isReady.value) {
        localRules.value = deepClone(defaultRules);
    }
}, { immediate: true, deep: true });

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localRules,
  async (newList) => {
    localRules.value = newList;
    await saveRules();
  }
);

function openModal(rule: RegexRule | null = null) {
    if (rule) {
        editingRule.value = rule;
    } else {
        editingRule.value = { id: uuidv4(), name: '', pattern: '', template: '', enabled: true };
    }
    isModalOpen.value = true;
}

function closeModal() {
    isModalOpen.value = false;
    editingRule.value = null;
}

async function handleSaveRule(savedRule: RegexRule) {
    const index = localRules.value.findIndex(r => r.id === savedRule.id);
    if (index > -1) {
        localRules.value[index] = savedRule;
    } else {
        localRules.value.unshift(savedRule);
    }
    closeModal();
    await saveRules();
}

async function removeRule(index: number) {
  const ruleToRemove = localRules.value[index];
  if (ruleToRemove && confirm(`确定要删除规则 "${ruleToRemove.name}" 吗？`)) {
    localRules.value.splice(index, 1);
    await saveRules();
  }
}

async function saveRules() {
    try {
        await settingsStore.updateRegexRules(localRules.value);
        uiStore.setGlobalError('渲染规则已自动保存！');
    } catch (e) {
        uiStore.setGlobalError(`保存失败: ${e}`);
    }
}

async function handleImport(ids: (string | number)[]) {
  await settingsStore.importDefaultRulesByIds(ids as string[]);
  isImportModalOpen.value = false;
}
</script>