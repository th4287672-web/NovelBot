<template>
  <div class="flex flex-col h-full w-full">
    <div v-if="isLoading" class="flex flex-col items-center justify-center h-full w-full text-gray-500">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
      <p class="mt-4 text-lg">正在加载会话...</p>
    </div>
    <template v-else>
      <MessageArea 
        class="flex-1 min-h-0"
        @delete-message="chatStore.deleteMessage"
        @edit-message="handleEditMessage"
        @rewrite-message="chatStore.rewriteMessage"
        @continue-message="chatStore.continueMessage"
        @complete-message="chatStore.completeMessage"
        @send-option="chatStore.send"
        @regenerate-options="chatStore.regenerateOptions"
        @retry-message="chatStore.retryGeneration"
        @stop-generation="chatStore.stopGeneration"
        @set-active-alternative="handleSetActiveAlternative"
        @regenerate-message="chatStore.regenerateMessage"
      />
      <div class="shrink-0 resize-y overflow-auto min-h-[140px] max-h-[60vh] border-t border-gray-700 bg-gray-800">
        <ChatInput
          @send="chatStore.send"
          @fetch-suggestions="chatStore.fetchSuggestions"
          @clear-suggestions="chatStore.clearSuggestions"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '~/stores/chat';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import { watch, computed, ref, onMounted } from 'vue';
import MessageArea from '~/components/chat/MessageArea.vue';
import ChatInput from '~/components/chat/ChatInput.vue';

const chatStore = useChatStore();
const sessionStore = useSessionStore();
const settingsStore = useSettingsStore();
const route = useRoute();
const router = useRouter();

const isLoading = ref(true);

const sessionId = computed(() => {
    const param = route.params.session_id;
    return Array.isArray(param) ? param[0] : param;
});

async function initializePage() {
  await settingsStore.hydrationPromise;

  const id = sessionId.value;
  if (!id) {
    await router.replace('/chat/new');
    return;
  }

  isLoading.value = true;
  if (id === 'new') {
    if (settingsStore.activeCharacterKey && !settingsStore.isAnonymous) {
      const newSession = await sessionStore.createNewSession(settingsStore.activeCharacterKey);
      if (newSession) {
        await router.replace(`/chat/${newSession.id}`);
      } else {
        await router.replace('/characters');
      }
    } else {
       await router.replace('/characters');
    }
  } else {
    await sessionStore.setActiveSession(id);
    isLoading.value = false;
  }
}

watch(() => route.params.session_id, () => {
    initializePage();
}, { immediate: true });


function handleEditMessage(payload: { messageId: number; newContent: string; }) {
  chatStore.editMessage(payload);
}
function handleSetActiveAlternative(payload: { messageId: number; index: number; }) {
    chatStore.setActiveAlternative(payload);
}
</script>