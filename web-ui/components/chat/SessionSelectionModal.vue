<template>
  <CommonBaseModal :title="modalTitle" theme-color="cyan" @close="emit('close')" max-width="80rem">
    <div class="relative min-h-[50vh]">
      <!-- 角色列表视图 -->
      <div v-if="currentView === 'characters'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="char in aiCharacters"
            :key="char.filename"
            @click="selectCharacter(char)"
            class="p-4 bg-gray-800 rounded-md cursor-pointer hover:bg-gray-700 border border-transparent hover:border-cyan-500 transition-all"
          >
            <h3 class="font-semibold text-white truncate">{{ char.displayName }}</h3>
            <p class="text-xs text-gray-400 mt-1 truncate">{{ char.description || '暂无描述' }}</p>
          </div>
        </div>
      </div>

      <!-- 会话列表视图 -->
      <div v-if="currentView === 'sessions' && selectedCharacter">
        <div class="flex items-center mb-4">
          <button @click="backToCharacterList" class="btn btn-secondary !px-3 !py-1 text-xs mr-4">
            &lt; 返回
          </button>
          <h3 class="text-lg font-semibold text-gray-300">
            {{ selectedCharacter.displayName }} 的会话
          </h3>
        </div>

        <div class="space-y-3">
          <button 
            @click="emit('create-new-session', selectedCharacter.filename)"
            class="w-full btn btn-primary bg-cyan-600 hover:bg-cyan-500"
          >
            + 新建会话
          </button>

          <div class="max-h-80 overflow-y-auto space-y-2 border-t border-gray-600/80 pt-3">
            <div 
              v-for="session in sessionsForSelectedChar" 
              :key="session.id"
              @click="!isEditing(session.id) && emit('select-session', { characterFilename: selectedCharacter.filename, sessionId: session.id })"
              class="p-3 rounded-md transition-colors group relative"
              :class="[
                session.id === activeSessionId ? 'bg-cyan-700/80 text-white' : 'bg-gray-800/60 hover:bg-gray-700',
                !isEditing(session.id) && 'cursor-pointer'
              ]"
            >
              <input 
                v-if="isEditing(session.id)"
                :value="session.title"
                @blur="saveRename(session, $event)"
                @keydown.enter.prevent="saveRename(session, $event)"
                @keydown.esc.prevent="cancelEdit"
                class="bg-gray-900 text-white w-full p-1 rounded-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
                v-focus
              />
              <p v-else class="font-semibold truncate">{{ session.title }}</p>
              
              <p class="text-xs mt-1" :class="session.id === activeSessionId ? 'text-gray-300' : 'text-gray-500'">
                最后更新于: {{ formatTimestamp(session.last_updated) }}
              </p>

               <div class="absolute top-1/2 -translate-y-1/2 right-2 flex items-center space-x-1 bg-gray-900/50 p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click.stop="startEditing(session)" title="重命名" class="p-1.5 hover:bg-gray-700 rounded text-sm">✏️</button>
                  <button @click.stop="aiRename(session)" title="AI命名" :disabled="sessionStore.isTitleGenerating(session.id).value" class="p-1.5 hover:bg-gray-700 rounded text-sm disabled:opacity-50">
                    <span v-if="sessionStore.isTitleGenerating(session.id).value" class="animate-pulse">✨</span>
                    <span v-else>✨</span>
                  </button>
                  <button @click.stop="handleDelete(session)" title="删除" class="p-1.5 hover:bg-gray-700 rounded text-sm">🗑️</button>
              </div>
            </div>
            <p v-if="sessionsForSelectedChar.length === 0" class="text-center text-gray-500 py-4">
              暂无历史会话。
            </p>
          </div>
        </div>
      </div>
    </div>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, computed, type PropType, nextTick } from 'vue';
import type { Session, SessionID, Character, Filename } from '~/types/api';
import { useCharacterStore } from '~/stores/characterStore';
import { useSessionStore } from '~/stores/sessionStore';
import { storeToRefs } from 'pinia';

const props = defineProps({
  activeSessionId: { type: String as PropType<SessionID | null>, required: true },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'select-session', payload: { characterFilename: Filename; sessionId: SessionID }): void;
  (e: 'create-new-session', characterFilename: Filename): void;
}>();

const characterStore = useCharacterStore();
const sessionStore = useSessionStore();
const router = useRouter();

const { characters } = storeToRefs(characterStore);
const { sessionsByChar } = storeToRefs(sessionStore);

const currentView = ref<'characters' | 'sessions'>('characters');
const selectedCharacter = ref<Character | null>(null);
const editingSessionId = ref<SessionID | null>(null);

const vFocus = {
  mounted: (el: HTMLInputElement) => {
    el.focus();
    el.select();
  }
}

const aiCharacters = computed(() => {
  return Object.values(characters.value).filter(char => !char.is_user_persona);
});

const modalTitle = computed(() => {
  return currentView.value === 'characters' ? '选择角色' : '选择会话';
});

const sessionsForSelectedChar = computed(() => {
  if (selectedCharacter.value) {
    return sessionsByChar.value[selectedCharacter.value.filename] || [];
  }
  return [];
});

function selectCharacter(character: Character) {
  selectedCharacter.value = character;
  sessionStore.loadSessionsForCharacter(character.filename);
  currentView.value = 'sessions';
}

function backToCharacterList() {
  currentView.value = 'characters';
  selectedCharacter.value = null;
}

function formatTimestamp(timestamp: number): string {
  if (!timestamp) return '未知时间';
  return new Date(timestamp * 1000).toLocaleString();
}

function isEditing(sessionId: SessionID) {
  return editingSessionId.value === sessionId;
}

function startEditing(session: Session) {
  editingSessionId.value = session.id;
}

function cancelEdit() {
  editingSessionId.value = null;
}

function saveRename(session: Session, event: Event) {
  const newTitle = (event.target as HTMLInputElement).value.trim();
  if (newTitle && newTitle !== session.title) {
    sessionStore.renameSession(session.id, newTitle);
  }
  cancelEdit();
}

async function aiRename(session: Session) {
    if (!selectedCharacter.value) return;
    await sessionStore.generateSessionTitle(selectedCharacter.value.filename, session.id);
}

async function handleDelete(session: Session) {
  if (confirm(`确定要永久删除会话 "${session.title}" 吗？此操作无法撤销。`)) {
    if (!selectedCharacter.value) return;
    const oldActiveId = props.activeSessionId;
    await sessionStore.deleteSession(selectedCharacter.value.filename, session.id);
    
    if (oldActiveId === session.id) {
        const newActiveId = sessionStore.activeSessionId;
        if (newActiveId) {
            router.replace(`/chat/${newActiveId}`);
        } else {
            router.replace('/chat/new');
        }
    }
  }
}
</script>