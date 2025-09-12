<template>
  <div class="h-full w-full">
    <ManagementLayout
      :is-loading="!isReady"
      :is-empty="filteredPersonas.length === 0 && !searchQuery"
      @create="openModal('create')"
    >
      <template #title>// 用户人设管理</template>
      <template #create-button-content>
        <div class="flex gap-4 items-center">
            <div class="flex items-center bg-gray-700/60 rounded-md p-1">
              <button @click="viewType = 'grid'" class="p-1.5 rounded-md transition-colors" :class="{'bg-purple-600 text-white': viewType === 'grid'}"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg></button>
              <button @click="viewType = 'list'" class="p-1.5 rounded-md transition-colors" :class="{'bg-purple-600 text-white': viewType === 'list'}"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" /></svg></button>
            </div>
            <div class="relative">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="搜索人设..." 
                class="bg-gray-700/60 rounded-sm border-2 border-gray-500/80 px-3 py-2 text-white transition-colors duration-200 focus:outline-none focus:bg-gray-700 w-48 text-sm"
              />
            </div>
            <button @click.stop="isImportModalOpen = true" class="btn btn-secondary">导入默认</button>
            <button class="btn btn-primary bg-purple-600 hover:bg-purple-500">创建新人设</button>
        </div>
      </template>
      
      <div v-if="filteredPersonas.length > 0" :class="viewType === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-3'">
        <div
          v-for="(persona, index) in filteredPersonas"
          :key="persona.filename"
          class="relative transition-all"
          :draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event)"
          @dragleave="onDragLeave($event)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd($event)"
        >
          <PersonaCard v-if="viewType === 'grid'"
            :persona="persona"
            :is-active="activePersonaKey === persona.filename"
            @select="settingsStore.setActivePersona(persona.filename)"
            @edit="openModal('edit', persona)"
            @delete="handleDeletePersona"
          />
          <PersonaListItem v-else 
            :persona="persona"
            :is-active="activePersonaKey === persona.filename"
            @select="settingsStore.setActivePersona(persona.filename)"
            @edit="openModal('edit', persona)"
            @delete="handleDeletePersona"
          />
           <div v-if="viewType === 'grid'" class="drag-handle absolute -top-1 -right-1 p-1 cursor-grab text-gray-600 hover:text-white bg-gray-800 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 12a2 2 0 100-4 2 2 0 000 4zM12 10a2 2 0 11-4 0 2 2 0 014 0zM17 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
          </div>
        </div>
      </div>
      <div v-else-if="searchQuery" class="text-center py-20 text-gray-500">
        <p>未找到与 "{{ searchQuery }}" 匹配的人设。</p>
      </div>
    </ManagementLayout>

    <PersonaEditModal
      v-if="isModalOpen"
      :mode="modalMode"
      :persona="editingPersona"
      @close="closeModal"
      @save="handleSavePersona"
    />

    <CommonImportModal
        v-if="isImportModalOpen"
        data-type-name="人设"
        theme-color="purple"
        :importable-items="importablePersonas"
        @close="isImportModalOpen = false"
        @import="handleImport"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useCharacterStore } from '~/stores/characterStore';
import { useSettingsStore } from '~/stores/settings';
import { useDisplayOrderMutation } from '~/composables/useDataMutations';
import { useDraggable } from '~/composables/useDraggable';
import type { Character, BackendCharacter } from '~/types/api';
import ManagementLayout from '~/components/common/ManagementLayout.vue';
import PersonaCard from '~/components/persona/PersonaCard.vue';
import PersonaListItem from '~/components/persona/PersonaListItem.vue';
import PersonaEditModal from '~/components/persona/PersonaEditModal.vue';
import { useStorage } from '@vueuse/core';

const characterStore = useCharacterStore();
const settingsStore = useSettingsStore();
const { mutate: updateOrder } = useDisplayOrderMutation();

const { characters, importablePersonas } = storeToRefs(characterStore);
const { activePersonaKey, isReady, userFullConfig } = storeToRefs(settingsStore);

const isModalOpen = ref(false);
const isImportModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const editingPersona = ref<Character | null>(null);
const searchQuery = ref('');
const viewType = useStorage<'grid' | 'list'>('mynovelbot-persona-view', 'grid');

const userPersonas = computed(() => {
  return Object.values(characters.value).filter(char => char.is_user_persona);
});

const localOrderedPersonas = ref<Character[]>([]);

const orderedPersonasComputed = computed(() => {
  const order = userFullConfig.value?.display_order?.personas || [];
  const allItems = userPersonas.value;

  return allItems.sort((a, b) => {
    const indexA = order.indexOf(a.filename);
    const indexB = order.indexOf(b.filename);
    if (indexA === -1 && indexB === -1) return a.displayName.localeCompare(b.displayName);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
});

const filteredPersonas = computed(() => {
    if (!searchQuery.value) {
        return localOrderedPersonas.value;
    }
    return localOrderedPersonas.value.filter(p =>
        p.displayName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        p.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
});

watch(orderedPersonasComputed, (newList) => {
  localOrderedPersonas.value = newList;
}, { immediate: true });

const { onDragStart, onDragOver, onDragLeave, onDrop, onDragEnd } = useDraggable(
  localOrderedPersonas,
  (newList) => { 
    localOrderedPersonas.value = newList;
    const newOrder = newList.map(p => p.filename);
    updateOrder({ dataType: 'personas', order: newOrder });
  }
);

function openModal(mode: 'create' | 'edit', persona: Character | null = null) {
  modalMode.value = mode;
  editingPersona.value = persona;
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
  editingPersona.value = null;
}

function handleSavePersona(payload: { mode: 'create' | 'edit', data: Character }) {
  const isEditing = payload.mode === 'edit';
  const { filename, ...apiData } = payload.data;
  const personaData: BackendCharacter = { ...apiData, is_user_persona: true };
  const nameForApi = isEditing ? filename : apiData.displayName;
  characterStore.createOrUpdateCharacter(nameForApi, personaData, isEditing);
  closeModal();
}

function handleDeletePersona(persona: Character) {
  if (confirm(`确定要永久删除人设 "${persona.displayName}" 吗？`)) {
    characterStore.deleteCharacter(persona.filename);
  }
}

function handleImport(keys: (string | number)[]) {
    const filenames = keys.filter((key): key is string => typeof key === 'string');
    characterStore.importPublicCharacters(filenames);
    isImportModalOpen.value = false;
}
</script>