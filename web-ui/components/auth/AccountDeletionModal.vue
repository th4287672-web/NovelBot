<template>
  <CommonBaseModal title="确认注销账号" theme-color="red" max-width="64rem" @close="emit('close')">
    <div class="space-y-4">
      <p class="text-lg font-semibold text-red-400">这是一个不可逆的操作！</p>
      <p class="text-sm text-gray-300">
        注销账号将永久删除您的用户名、密码、头像以及所有关联的私有数据（角色卡、人设、世界书、预设、聊天记录等）。
        此操作无法撤销，请谨慎操作。
      </p>
      <div>
        <label for="password-confirm" class="archive-label">请输入您的登录密码以确认</label>
        <input 
          id="password-confirm"
          v-model="password"
          type="password"
          class="archive-input focus:border-red-500"
          @keydown.enter.prevent="handleConfirm"
        />
      </div>
    </div>
    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button 
        @click="handleConfirm" 
        :disabled="!password.trim() || isLoading"
        class="btn btn-danger"
      >
        <span v-if="isLoading" class="animate-pulse">正在删除...</span>
        <span v-else>我已了解风险，确认注销</span>
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useUIStore } from '~/stores/ui';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', password: string): void;
}>();

const uiStore = useUIStore();
const password = ref('');
const isLoading = ref(false); // Can be used in the future if deletion is slow

function handleConfirm() {
  if (password.value.trim()) {
    emit('confirm', password.value);
  } else {
    uiStore.setGlobalError("请输入密码以确认。");
  }
}
</script>