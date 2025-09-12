<template>
  <div class="h-full w-full bg-gray-800 flex flex-col">
    <!-- 
      [核心修改] VirtualList 组件的用法已更新。
      它现在内部处理滚动容器，我们只需要传递数据和预估高度即可。
      组件的高度由其父容器决定。
    -->
    <VirtualList
      :items="filteredMessages"
      :estimate-height="120"
      class="flex-grow min-h-0 p-4"
    >
      <template #default="{ item: message }">
        <!-- 
          不再需要额外包裹 div 并设置 data-id。
          VirtualList 组件内部通过 virtualRow.index 来追踪每个项目。
          我们直接渲染 ChatBubble 组件。
        -->
        <ChatBubble
          :key="message.id"
          :message="message"
          @delete-message="emit('delete-message', $event)"
          @edit-message="handleEdit"
          @rewrite-message="emit('rewrite-message', $event)"
          @continue-message="emit('continue-message', $event)"
          @complete-message="emit('complete-message', $event)"
          @send-option="emit('send-option', $event)"
          @regenerate-options="emit('regenerate-options', $event)"
          @retry-message="emit('retry-message', $event)"
          @stop-generation="emit('stop-generation')"
          @set-active-alternative="emit('set-active-alternative', $event)"
          @regenerate-message="emit('regenerate-message', $event)"
        />
      </template>
    </VirtualList>
    
    <div v-if="requestState.status === 'streaming' || requestState.status === 'thinking'" class="flex justify-center mt-4 shrink-0 pb-4">
      <button @click="emit('stop-generation')" class="btn btn-danger">
        停止生成
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useChatStore } from '~/stores/chat';
import { useSessionStore } from '~/stores/sessionStore';
import VirtualList from '~/components/common/VirtualList.vue';
import ChatBubble from '~/components/chat/ChatBubble.vue';
import type { ChatMessage } from '~/types/api';

const chatStore = useChatStore();
const sessionStore = useSessionStore();

const { activeSessionMessages } = storeToRefs(sessionStore);
const { requestState } = storeToRefs(chatStore);

const filteredMessages = computed(() => {
  return activeSessionMessages.value.filter(msg => {
    if (msg.role === 'user') return true;
    if (msg.role === 'model' && (msg.content?.trim() || msg.isStreaming || msg.isError)) return true;
    return false;
  });
});

const emit = defineEmits<{
  (e: 'delete-message', messageId: number): void;
  (e: 'edit-message', payload: { messageId: number, newContent: string }): void;
  (e: 'rewrite-message', messageId: number): void;
  (e: 'continue-message', messageId: number): void;
  (e: 'complete-message', messageId: number): void;
  (e: 'send-option', content: string): void;
  (e: 'regenerate-options', messageId: number): void;
  (e: 'retry-message', messageId: number): void;
  (e: 'stop-generation'): void;
  (e: 'regenerate-message', messageId: number): void;
  (e: 'set-active-alternative', payload: { messageId: number, index: number }): void;
}>();


function handleEdit(payload: { messageId: number, newContent: string }) {
  emit('edit-message', payload);
}
</script>