<template>
  <div>
    <CommonBaseModal :title="`管理预设: ${localPreset.displayName}`" theme-color="green" max-width="80rem" @close="emit('close')">
      <!-- [核心优化] 新增“调试器”标签页 -->
      <CommonTabbedContent :tabs="tabs" initial-tab="modules" theme-color="green" class="h-full">
        <template #modules>
          <div class="p-4 flex flex-col h-full">
            <div class="flex justify-between items-center mb-4 shrink-0">
                <h3 class="text-lg font-semibold text-gray-300">模块列表</h3>
                <button v-if="localPreset?.is_private" @click="openModuleEditor('create')" class="btn btn-primary bg-green-600 hover:bg-green-500 text-sm">
                    添加新模块
                </button>
            </div>
            <div class="flex-1 overflow-y-auto min-h-0 pr-2 -mr-6">
                <div v-if="(localPreset?.prompts?.length ?? 0) > 0" class="space-y-2">
                    <div 
                        v-for="(module, index) in localPreset?.prompts" 
                        :key="module.identifier" 
                        class="bg-gray-800/60 p-3 rounded-sm flex justify-between items-center border border-gray-600/50 transition-all"
                        :draggable="localPreset?.is_private"
                        @dragstart="onDragStart($event, index)"
                        @dragover.prevent="onDragOver($event)"
                        @dragleave="onDragLeave($event)"
                        @drop="onDrop($event, index)"
                        @dragend="onDragEnd($event)"
                    >
                        <div class="flex-1 min-w-0 flex items-center">
                            <div v-if="localPreset?.is_private" class="drag-handle cursor-grab text-gray-500 hover:text-white mr-3 shrink-0">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
                            </div>
                            <input 
                                type="checkbox"
                                v-model="module.enabled"
                                :disabled="!localPreset?.is_private"
                                class="form-checkbox h-5 w-5 bg-gray-700 border-gray-500 rounded text-green-500 focus:ring-green-500/50 cursor-pointer shrink-0"
                                :title="module.enabled ? '默认启用' : '默认禁用'"
                            />
                            <h4 class="font-semibold text-white truncate ml-4">{{ module.name }}</h4>
                        </div>
                        <div v-if="localPreset?.is_private" class="flex items-center space-x-4 ml-4 shrink-0">
                            <button @click="openModuleEditor('edit', module)" class="text-xs text-gray-400 hover:text-white">编辑</button>
                            <button @click="handleDeleteModule(module.identifier)" class="text-xs text-red-500 hover:text-red-400">删除</button>
                        </div>
                    </div>
                </div>
                <div v-else class="text-center py-10 text-gray-500">
                  <p>这个预设还没有任何模块。</p>
                </div>
            </div>
          </div>
        </template>
        <template #settings>
            <div class="p-4 space-y-6">
                <div>
                    <label class="archive-label">预设显示名称</label>
                    <input v-model="localPreset.displayName" type="text" class="archive-input focus:border-green-500" :disabled="!localPreset.is_private" />
                </div>
                <div v-if="localPreset.is_private" class="border-t border-red-500/30 pt-4 space-y-2">
                    <h4 class="text-red-400 font-semibold">危险操作</h4>
                    <div class="flex gap-4">
                        <button @click="emit('clone')" class="btn btn-secondary">克隆此预设</button>
                        <button @click="emit('delete')" class="btn btn-danger">删除此预设</button>
                    </div>
                </div>
            </div>
        </template>
        <!-- [核心新增] 调试器标签页的内容 -->
        <template #debugger>
            <div class="p-4 space-y-4 h-full flex flex-col">
                <div>
                    <label for="debug-input" class="archive-label">模拟用户输入</label>
                    <textarea id="debug-input" v-model="debugUserInput" rows="3" class="archive-textarea font-mono text-sm" placeholder="输入一句你想测试的话..."></textarea>
                </div>
                <button @click="runDebugger" :disabled="presetStore.debugState.isLoading" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500 w-full">
                    {{ presetStore.debugState.isLoading ? '正在生成预览...' : '生成最终提示预览' }}
                </button>
                <div class="flex-grow min-h-0">
                    <label class="archive-label">最终生成的系统提示 (System Prompt)</label>
                    <div class="h-full bg-gray-900 rounded-md p-3 overflow-auto border border-gray-600">
                        <pre v-if="presetStore.debugState.promptText" class="text-xs text-gray-300 whitespace-pre-wrap">{{ presetStore.debugState.promptText }}</pre>
                        <p v-else class="text-gray-500 text-sm">点击上方按钮以生成预览。</p>
                    </div>
                </div>
            </div>
        </template>
      </CommonTabbedContent>
      
      <template #footer-actions>
          <button type="button" @click="emit('close')" class="btn btn-secondary">
              关闭
          </button>
          <button v-if="localPreset.is_private" type="button" @click="handleSave" class="btn btn-primary bg-green-600 hover:bg-green-500">
              保存更改
          </button>
      </template>
    </CommonBaseModal>

    <ClientOnly>
        <PresetsPresetModuleEditModal
            v-if="isModuleModalOpen"
            :mode="moduleModalMode"
            :module="editingModule"
            @close="closeModuleEditor"
            @save="handleSaveModule"
        />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType, computed } from 'vue';
import type { Preset, PresetModule } from '@/types/api'; 
import { deepClone } from '~/utils/helpers';
import { useDraggable } from '~/composables/useDraggable';
// [核心新增] 导入 presetStore
import { usePresetStore } from '~/stores/presetStore';

const props = defineProps({
  preset: {
    type: Object as PropType<Preset | null>,
    required: true,
  }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', preset: Preset): void;
  (e: 'delete'): void;
  (e: 'clone'): void;
}>();

const presetStore = usePresetStore(); // [核心新增]
const localPreset = ref<Preset>(deepClone(props.preset!));

const isModuleModalOpen = ref(false);
const moduleModalMode = ref<'create' | 'edit'>('create');
const editingModule = ref<PresetModule | null>(null);
const debugUserInput = ref('你好'); // [核心新增]

// [核心优化] 动态添加“调试器”标签
const tabs = computed(() => {
    const baseTabs = [
        { id: 'modules', label: '模块管理' },
        { id: 'settings', label: '预设设置' },
    ];
    if (localPreset.value.is_private) {
        baseTabs.push({ id: 'debugger', label: '调试器' });
    }
    return baseTabs;
});

const localModules = computed({
    get: () => localPreset.value.prompts || [],
    set: (newList: PresetModule[]) => {
        if (localPreset.value) {
            localPreset.value.prompts = newList;
        }
    }
});

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localModules,
  (newList) => { 
    localModules.value = newList; 
  }
);

watch(() => props.preset, (newVal) => {
    if (newVal) localPreset.value = deepClone(newVal);
}, { deep: true });

function openModuleEditor(mode: 'create' | 'edit', module?: PresetModule) {
  moduleModalMode.value = mode;
  editingModule.value = module || null;
  isModuleModalOpen.value = true;
}

function closeModuleEditor() {
  isModuleModalOpen.value = false;
  editingModule.value = null;
}

function handleSaveModule(module: PresetModule) {
  if (!localPreset.value.prompts) {
    localPreset.value.prompts = [];
  }
  if (moduleModalMode.value === 'create') {
    localPreset.value.prompts.push(module);
  } else {
    const index = localPreset.value.prompts.findIndex(p => p.identifier === module.identifier);
    if (index !== -1) {
      localPreset.value.prompts[index] = module;
    }
  }
  closeModuleEditor();
}

function handleDeleteModule(moduleId: string) {
    if (confirm('你确定要删除这个模块吗？') && localPreset.value.prompts) {
        localPreset.value.prompts = localPreset.value.prompts.filter(p => p.identifier !== moduleId);
    }
}

function handleSave() {
    emit('save', localPreset.value);
}

// [核心新增] 调试器运行逻辑
function runDebugger() {
    presetStore.debugPreset(localPreset.value, debugUserInput.value);
}
</script>