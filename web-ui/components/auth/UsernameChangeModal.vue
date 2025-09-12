<template>
  <CommonBaseModal title="修改用户名" theme-color="cyan" max-width="60rem" @close="emit('close')">
    <div class="space-y-4">
      <div>
        <label for="new-username" class="archive-label">新用户名</label>
        <input 
          id="new-username"
          v-model="newUsername"
          type="text"
          class="archive-input focus:border-cyan-500"
        />
      </div>
       <div>
        <label for="password-confirm-rename" class="archive-label">请输入当前密码以确认</label>
        <input 
          id="password-confirm-rename"
          v-model="password"
          type="password"
          class="archive-input focus:border-cyan-500"
          @keydown.enter.prevent="handleConfirm"
        />
      </div>
    </div>
    <template #footer-actions>
      <button @click="emit('close')" class="btn btn-secondary">取消</button>
      <button 
        @click="handleConfirm" 
        :disabled="!newUsername.trim() || !password.trim()"
        class="btn btn-primary bg-cyan-600 hover:bg-cyan-500"
      >
        确认修改
      </button>
    </template>
  </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useUIStore } from '~/stores/ui';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', payload: { newUsername: string, password: string }): void;
}>();

const uiStore = useUIStore();
const newUsername = ref('');
const password = ref('');

function handleConfirm() {
  if (newUsername.value.trim() && password.value.trim()) {
    emit('confirm', { newUsername: newUsername.value, password: password.value });
  } else {
    uiStore.setGlobalError("新用户名和密码不能为空。");
  }
}
</script>