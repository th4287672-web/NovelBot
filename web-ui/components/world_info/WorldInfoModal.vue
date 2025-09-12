<template>
  <div>
    <CommonBaseModal :title="modalTitle" theme-color="yellow" max-width="80rem" @close="emit('close')">
      <CommonTabbedContent :tabs="tabs" initial-tab="info" theme-color="yellow" class="h-full">
        <template #info>
          <div class="p-4 space-y-4">
            <div v-if="mode === 'create'" class="text-right">
              <button @click="viewMode = 'ai'" class="text-sm text-yellow-400 hover:underline">切换到 AI 辅助生成</button>
            </div>
            <div v-if="viewMode === 'form'">
              <label for="bookName" class="archive-label">世界书名称</label>
              <input 
                id="bookName"
                type="text"
                v-model="localBook.name"
                class="archive-input focus:border-yellow-500 focus:ring-yellow-500/30 focus:ring-2"
              />
            </div>
             <div v-if="viewMode === 'ai'" class="space-y-4">
              <div>
                <label for="ai-prompt-world" class="archive-label">输入世界观核心主题</label>
                <textarea id="ai-prompt-world" v-model="aiPrompt" rows="5" class="archive-textarea focus:border-yellow-500 focus:ring-yellow-500/30 focus:ring-2" placeholder="例如：一个魔法与科技共存，但魔法正在衰退的蒸汽朋克世界。"></textarea>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="archive-label">选择预设作为规则 (可选)</label>
                  <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
                    <label v-for="preset in Object.values(presets) as Preset[]" :key="preset.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
                      <input type="checkbox" :value="preset.filename" v-model="selectedPresets" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-yellow-500 focus:ring-yellow-600">
                      <span class="ml-2 text-gray-300 truncate">{{ preset.displayName }}</span>
                    </label>
                  </div>
                </div>
                <div>
                  <label class="archive-label">选择其他世界书作为参考 (可选)</label>
                  <div class="max-h-32 overflow-y-auto space-y-1 p-2 border border-gray-600 rounded-md">
                    <label v-for="world in Object.values(worldInfo) as WorldInfo[]" :key="world.filename" class="flex items-center text-sm p-1 rounded hover:bg-gray-700">
                      <input type="checkbox" :value="world.filename" v-model="selectedWorlds" class="form-checkbox h-4 w-4 bg-gray-600 border-gray-500 rounded text-yellow-500 focus:ring-yellow-600">
                      <span class="ml-2 text-gray-300 truncate">{{ world.name }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template #entries>
          <div class="p-4 flex flex-col h-full">
            <div class="flex justify-between items-center mb-3 shrink-0">
                <h3 class="text-lg font-semibold text-gray-300">条目列表</h3>
                <button @click="openEntryModal('create')" class="btn btn-primary bg-green-600 hover:bg-green-500 text-sm">添加新条目</button>
            </div>
            <div class="flex-grow min-h-0 overflow-y-auto pr-2">
              <div class="space-y-2">
                <div 
                  v-for="(entry, index) in localBook.entries" 
                  :key="entry.uid" 
                  class="bg-gray-800/60 p-3 rounded-sm flex justify-between items-center border border-gray-600/50 transition-all"
                  :draggable="true"
                  @dragstart="onDragStart($event, index)"
                  @dragover.prevent="onDragOver($event)"
                  @dragleave="onDragLeave($event)"
                  @drop="onDrop($event, index)"
                  @dragend="onDragEnd($event)"
                >
                    <div class="flex items-center flex-grow min-w-0">
                      <div class="drag-handle cursor-grab text-gray-500 hover:text-white mr-3">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
                      </div>
                      <span class="font-semibold text-gray-200 truncate pr-4">
                        {{ entry.name || (Array.isArray(entry.keywords) && entry.keywords.length > 0 ? entry.keywords.join(', ') : `条目 ${index + 1}`) }}
                      </span>
                    </div>
                      <div class="flex space-x-3 shrink-0">
                          <button @click="openEntryModal('edit', entry, index)" class="text-sm text-gray-400 hover:text-cyan-400">编辑</button>
                          <button @click="deleteEntry(index)" class="text-sm text-gray-400 hover:text-red-500">删除</button>
                      </div>
                  </div>
                </div>
              <div v-if="!localBook.entries || localBook.entries.length === 0" class="text-center text-gray-500 py-10">
                  <p>暂无条目。</p>
              </div>
            </div>
          </div>
        </template>
      </CommonTabbedContent>

      <template #footer-actions>
        <button @click="emit('close')" class="btn btn-secondary">关闭</button>
        <button v-if="viewMode === 'form'" @click="handleSaveBook" class="btn btn-primary bg-yellow-600 hover:bg-yellow-500">保存世界书</button>
        <button v-if="viewMode === 'ai'" @click="handleAiGenerate" :disabled="isGenerating" class="btn btn-primary bg-yellow-600 hover:bg-yellow-500 disabled:bg-gray-500">
          {{ isGenerating ? '生成中...' : '开始生成' }}
        </button>
      </template>
    </CommonBaseModal>

    <ClientOnly>
      <WorldInfoEntryModal 
          v-if="isEntryModalOpen"
          :mode="entryModalMode"
          :entry="editingEntry"
          @close="closeEntryModal"
          @save="handleSaveEntry"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type PropType } from 'vue';
import { useWorldStore } from '~/stores/worldStore';
import { usePresetStore } from '~/stores/presetStore';
import { storeToRefs } from 'pinia';
import { useDraggable } from '~/composables/useDraggable';
import type { WorldInfo, WorldInfoEntry, Filename, Preset } from '~/types/api';
import { deepClone } from '~/utils/helpers';
import { v4 as uuidv4 } from 'uuid';
import WorldInfoEntryModal from './WorldInfoEntryModal.vue';

const props = defineProps({
    mode: {
        type: String as PropType<'create' | 'edit'>,
        required: true
    },
    filename: {
        type: String as PropType<Filename | null>,
        default: null
    }
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', payload: { mode: 'create' | 'edit', filename: Filename | null, data: Omit<WorldInfo, 'filename'> }): void;
}>();

const worldStore = useWorldStore();
const presetStore = usePresetStore();
const { worldInfo } = storeToRefs(worldStore);
const { presets } = storeToRefs(presetStore);

const localBook = ref<Omit<WorldInfo, 'filename'>>({ name: '', entries: [], is_private: true });
const viewMode = ref<'form' | 'ai'>('form');
const aiPrompt = ref('');
const isGenerating = ref(false);

const selectedPresets = ref<Filename[]>([]);
const selectedWorlds = ref<Filename[]>([]);

const isEntryModalOpen = ref(false);
const entryModalMode = ref<'create' | 'edit'>('create');
const editingEntry = ref<WorldInfoEntry | null>(null);
const editingEntryIndex = ref<number | null>(null);

const tabs = [
  { id: 'info', label: '基础信息' },
  { id: 'entries', label: '条目管理' },
];

const modalTitle = computed(() => props.mode === 'create' ? '创建新世界书' : `编辑世界书: ${localBook.value.name}`);

const localEntries = computed({
    get: () => localBook.value.entries,
    set: (newList: WorldInfoEntry[]) => { localBook.value.entries = newList; }
});

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localEntries,
  (newList) => { 
    localEntries.value = newList; 
  }
);

watch(() => [props.mode, props.filename], ([newMode, newFilename]) => {
  let bookData: Omit<WorldInfo, 'filename' | 'is_private'> & { is_private?: boolean };
  if (newMode === 'edit' && newFilename && worldInfo.value[newFilename]) {
    bookData = deepClone(worldInfo.value[newFilename]);
  } else {
    bookData = { name: '新的世界书', entries: [] };
  }
  
  if (bookData.entries && !Array.isArray(bookData.entries)) {
      bookData.entries = Object.values(bookData.entries);
  }

  bookData.entries = (bookData.entries || []).map(entry => ({ ...entry, uid: entry.uid || uuidv4() }));
  
  localBook.value = {
      name: bookData.name,
      entries: bookData.entries,
      is_private: bookData.is_private ?? true
  };

  viewMode.value = props.mode === 'create' ? 'ai' : 'form';
  selectedPresets.value = [];
  selectedWorlds.value = [];
}, { immediate: true });

function openEntryModal(mode: 'create' | 'edit', entry: WorldInfoEntry | null = null, index: number | null = null) {
    entryModalMode.value = mode;
    editingEntry.value = entry;
    editingEntryIndex.value = index;
    isEntryModalOpen.value = true;
}

function closeEntryModal() {
    isEntryModalOpen.value = false;
    editingEntry.value = null;
    editingEntryIndex.value = null;
}

function deleteEntry(index: number) {
  if (confirm('确定要删除这个条目吗？')) {
    localBook.value.entries.splice(index, 1);
  }
}

function handleSaveEntry(entry: WorldInfoEntry) {
    const entryWithUid = { ...entry, uid: entry.uid || uuidv4() };
    if (entryModalMode.value === 'create') {
        localBook.value.entries.push(entryWithUid);
    } else if (editingEntryIndex.value !== null) {
        localBook.value.entries[editingEntryIndex.value] = entryWithUid;
    }
    closeEntryModal();
}

function handleSaveBook() {
  if (!localBook.value.name.trim()) {
    alert('世界书名称不能为空！');
    return;
  }
  emit('save', { 
    mode: props.mode, 
    filename: props.filename, 
    data: localBook.value 
  });
}

function isGeneratedWorldBookValid(data: any): data is Omit<WorldInfo, 'filename' | 'is_private'> {
    if (!data || typeof data.name !== 'string' || data.name.trim() === '' || !Array.isArray(data.entries)) {
        return false;
    }
    if (data.entries.length === 0) return true;
    for (const entry of data.entries) {
        if (!entry || !Array.isArray(entry.keywords) || typeof entry.content !== 'string') {
            return false;
        }
    }
    return true;
}

async function handleAiGenerate() {
    if (!aiPrompt.value.trim()) {
        alert('请输入世界观核心主题！');
        return;
    }
    isGenerating.value = true;
    try {
        const generatedData = await worldStore.generateWorldBook(
          aiPrompt.value,
          selectedPresets.value,
          selectedWorlds.value
        );
        if (isGeneratedWorldBookValid(generatedData)) {
            generatedData.entries = generatedData.entries.map(e => ({ ...e, uid: uuidv4() }));
            localBook.value = { ...generatedData, is_private: true };
            viewMode.value = 'form';
        } else {
            alert('AI生成的内容不完整或格式不正确，请调整提示词后重试，或切换到手动填写。');
        }
    } finally {
        isGenerating.value = false;
    }
}
</script>