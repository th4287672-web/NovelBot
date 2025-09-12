<template>
  <div class="flex flex-col h-full w-full">
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
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '~/stores/chat';
import { useSessionStore } from '~/stores/sessionStore';
import { useSettingsStore } from '~/stores/settings';
import { watch, computed, type Ref } from 'vue';
import MessageArea from '~/components/chat/MessageArea.vue';
import ChatInput from '~/components/chat/ChatInput.vue';

const chatStore = useChatStore();
const sessionStore = useSessionStore();
const settingsStore = useSettingsStore();
const route = useRoute();

const sessionId = computed(() => {
    const param = route.params.session_id;
    return Array.isArray(param) ? param[0] || '' : param || '';
});

watch(
  () => [settingsStore.isReady, sessionId.value],
  ([isReady, newId]) => {
    if (isReady && typeof newId === 'string' && newId && sessionStore.activeSessionId !== newId) {
      sessionStore.setActiveSession(newId);
    }
  },
  { immediate: true }
);

function handleEditMessage(payload: { messageId: number; newContent: string; }) {
  chatStore.editMessage(payload);
}
function handleSetActiveAlternative(payload: { messageId: number; index: number; }) {
    chatStore.setActiveAlternative(payload);
}
</script>