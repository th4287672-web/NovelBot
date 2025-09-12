<template>
  <ChatMessage
    :message="message"
    :character-name="characterName"
    @delete="onDelete"
    @edit="onEdit"
    @rewrite="onRewrite"
    @continue="onContinue"
    @complete-message="onCompleteMessage"
    @send-option="onSelectOption"
    @regenerate-options="onRegenerateOptions"
    @retry="onRetry"
    @regenerate="onRegenerate"
    @set-active-alternative="onSetActiveAlternative"
  />
</template>

<script setup lang="ts">
import { useCharacterStore } from '~/stores/characterStore';
import { computed } from 'vue';
import type { ChatMessage as Message } from '~/types/api';
// [FIX] 显式导入子组件
import ChatMessage from '~/components/chat/ChatMessage.vue';


const props = defineProps<{
  message: Message;
}>();

const emit = defineEmits<{
  (e: 'delete', messageId: number): void;
  (e: 'edit', payload: { messageId: number, newContent: string }): void;
  (e: 'rewrite', messageId: number): void;
  (e: 'continue', messageId: number): void;
  (e: 'complete-message', messageId: number): void;
  (e: 'select-option', content: string): void;
  (e: 'regenerate-options', messageId: number): void;
  (e: 'retry', messageId: number): void;
  (e: 'regenerate', messageId: number): void;
  (e: 'set-active-alternative', payload: { messageId: number, index: number }): void;
}>();

const characterStore = useCharacterStore();

const characterName = computed(() => {
  return characterStore.activeCharacter?.displayName || 'AI';
});

const onEdit = (payload: { messageId: number, newContent: string }) => emit('edit', payload);
const onDelete = (messageId: number) => emit('delete', messageId);
const onRewrite = (messageId: number) => emit('rewrite', messageId);
const onContinue = (messageId: number) => emit('continue', messageId);
const onCompleteMessage = (messageId: number) => emit('complete-message', messageId);
const onSelectOption = (content: string) => emit('select-option', content);
const onRegenerateOptions = (messageId: number) => emit('regenerate-options', messageId);
const onRetry = (messageId: number) => emit('retry', messageId);
const onRegenerate = (messageId: number) => emit('regenerate', messageId);
const onSetActiveAlternative = (payload: { messageId: number, index: number }) => emit('set-active-alternative', payload);
</script>