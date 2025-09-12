<template>
    <div class="p-8 space-y-6 overflow-y-auto h-full">
        <h2 class="text-2xl font-bold text-center text-cyan-400">登录</h2>
        <form @submit.prevent="handleLogin" class="space-y-4">
            <div>
                <label for="login-username" class="archive-label">用户名或账号</label>
                <input id="login-username" v-model="loginForm.username_or_account" type="text" class="archive-input" required />
            </div>
            <div>
                <label for="login-password" class="archive-label">密码</label>
                <input id="login-password" v-model="loginForm.password" type="password" class="archive-input" required />
            </div>
            <p class="text-xs text-right">
                <button type="button" @click="emit('switch-to-forgot')" class="text-cyan-400 hover:underline">忘记密码?</button>
            </p>
            <button type="submit" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 w-full" :disabled="isLoading">
              <span v-if="isLoading" class="animate-pulse">登录中...</span>
              <span v-else>登录</span>
            </button>
        </form>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { apiService } from '~/services/api';
import { useUIStore } from '~/stores/ui';
import type { UserInfo } from '~/types/api';

const emit = defineEmits<{
  (e: 'success', userInfo: UserInfo): void;
  (e: 'switch-to-forgot'): void;
}>();

const uiStore = useUIStore();
const loginForm = ref({ username_or_account: '', password: '' });
const isLoading = ref(false);

async function handleLogin() {
    isLoading.value = true;
    uiStore.setGlobalError(null); // 清除旧的错误
    try {
        const response = await apiService.login(loginForm.value);
        emit('success', response.user_info);
    } catch (error) {
        // [核心修复] 显示从后端传来的具体错误信息
        const message = error instanceof Error ? error.message : "发生未知错误";
        uiStore.setGlobalError(`登录失败: ${message}`);
    } finally {
        isLoading.value = false;
    }
}
</script>