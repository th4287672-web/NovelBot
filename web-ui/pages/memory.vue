<template>
  <div class="h-full w-full p-6 flex gap-6 overflow-hidden">
    <!-- 左侧: 角色列表 -->
    <div class="w-1/3 h-full flex flex-col bg-gray-800/50 rounded-lg border border-gray-700">
      <header class="p-3 border-b border-gray-700 shrink-0">
        <h3 class="font-semibold text-gray-200">选择角色</h3>
      </header>
      <div class="flex-grow p-2 overflow-y-auto space-y-1">
        <button
          v-for="char in aiCharacters"
          :key="char.filename"
          @click="selectCharacter(char)"
          class="w-full text-left p-2 rounded-md transition-colors"
          :class="selectedCharacter?.filename === char.filename ? 'bg-cyan-700 text-white' : 'hover:bg-gray-700'"
        >
          {{ char.displayName }}
        </button>
      </div>
    </div>

    <!-- 右侧: 记忆编辑器 -->
    <div class="w-2/3 h-full flex flex-col bg-gray-800/50 rounded-lg border border-gray-700">
      <header class="p-3 border-b border-gray-700 shrink-0 flex justify-between items-center">
        <h3 v-if="selectedCharacter" class="font-semibold text-gray-200">
          <span class="text-cyan-400">{{ selectedCharacter.displayName }}</span> 的记忆
        </h3>
        <h3 v-else class="font-semibold text-gray-500">请先选择一个角色</h3>
        <div class="flex items-center gap-2">
            <button
                @click="extractMemory"
                :disabled="!canExtractMemory"
                class="btn btn-secondary text-xs !px-3 !py-1"
                title="从该角色最新的对话中提取记忆并追加"
            >
                AI提取并追加
            </button>
        </div>
      </header>

      <div class="flex-grow p-4 overflow-y-auto">
        <div v-if="selectedCharacter" class="space-y-2">
            <div 
                v-for="(entry, index) in localMemoryEntries" 
                :key="index"
                class="flex items-center gap-2"
            >
                <input 
                    type="text" 
                    v-model="localMemoryEntries[index]"
                    class="archive-input flex-grow !mt-0"
                    placeholder="输入一条记忆..."
                />
                <button @click="deleteEntry(index)" class="btn btn-danger !px-2 !py-1 text-xs shrink-0">
                    -
                </button>
            </div>
            <button @click="addEntry" class="btn btn-secondary w-full mt-2">
                + 添加新条目
            </button>
        </div>
        <div v-else class="flex items-center justify-center h-full text-gray-500">
            <p>← 请先从左侧选择一个角色来管理其记忆。</p>
        </div>
      </div>
      <footer class="p-3 border-t border-gray-700 shrink-0 text-right">
        <button 
          @click="saveMemory"
          :disabled="!selectedCharacter || memoryStore.isLoading"
          class="btn btn-primary bg-cyan-600 hover:bg-cyan-500"
        >
          {{ memoryStore.isLoading ? '保存中...' : '保存记忆' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { storeToRefs } from 'pinia';
import { useCharacterStore } from '~/stores/characterStore';
import { useMemoryStore } from '~/stores/memoryStore';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import type { Character } from '~/types/api';

const characterStore = useCharacterStore();
const memoryStore = useMemoryStore();
const sessionStore = useSessionStore();
const settingsStore = useSettingsStore();

const { characters } = storeToRefs(characterStore);
const { activeCharacterKey } = storeToRefs(settingsStore);
const { sessionsByChar, messageHistoryCache } = storeToRefs(sessionStore);
const { memories } = storeToRefs(memoryStore);

const selectedCharacter = ref<Character | null>(null);
const localMemoryEntries = ref<string[]>([]);

const aiCharacters = computed(() => {
  return Object.values(characters.value).filter(char => !char.is_user_persona);
});

const historyForSelectedChar = computed(() => {
    if (!selectedCharacter.value) return [];
    
    const sessions = sessionsByChar.value[selectedCharacter.value.filename] || [];
    const latestSession = sessions[0];

    if (latestSession) {
        const latestSessionId = latestSession.id;
        return messageHistoryCache.value[latestSessionId] || [];
    }
    
    return [];
});

const canExtractMemory = computed(() => {
    return selectedCharacter.value &&
           historyForSelectedChar.value.length > 1 &&
           !memoryStore.isLoading;
});

watch(selectedCharacter, (newChar) => {
  if (newChar) {
    memoryStore.fetchMemories(newChar.filename);
  } else {
    localMemoryEntries.value = [];
  }
});

watch(memories, (newMemories) => {
  if (selectedCharacter.value) {
    const charMemory = newMemories[selectedCharacter.value.filename];
    localMemoryEntries.value = charMemory ? [...charMemory.entries] : [];
  }
}, { deep: true });

async function selectCharacter(character: Character) {
  selectedCharacter.value = character;
  await sessionStore.loadSessionsForCharacter(character.filename);
}

function addEntry() {
    localMemoryEntries.value.push('');
    nextTick(() => {
        const inputs = document.querySelectorAll('.archive-input');
        const lastInput = inputs[inputs.length - 1] as HTMLInputElement;
        lastInput?.focus();
    });
}

function deleteEntry(index: number) {
    localMemoryEntries.value.splice(index, 1);
}

async function extractMemory() {
    if (!canExtractMemory.value || !selectedCharacter.value) return;
    const newMemories = await memoryStore.extractMemoryFromHistory(selectedCharacter.value.filename, historyForSelectedChar.value);
    if(newMemories && newMemories.length > 0) {
        localMemoryEntries.value.push(...newMemories);
        await saveMemory();
    }
}

async function saveMemory() {
  if (!selectedCharacter.value) return;
  const entries = localMemoryEntries.value.map(line => line.trim()).filter(Boolean);
  await memoryStore.updateMemories(selectedCharacter.value.filename, { entries });
}

watch(activeCharacterKey, (key) => {
    if (key && characters.value[key] && !selectedCharacter.value) {
        selectCharacter(characters.value[key]!);
    }
}, { immediate: true });
</script>

