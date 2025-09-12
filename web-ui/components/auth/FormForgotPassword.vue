<template>
    <div class="p-8 space-y-6 overflow-y-auto h-full">
        <h2 class="text-2xl font-bold text-center text-cyan-400">找回密码</h2>

        <!-- 步骤 1: 输入账号 -->
        <form v-if="step === 1" @submit.prevent="fetchQuestions" class="space-y-4">
            <p class="text-sm text-gray-400">请输入您的数字账号以获取安全问题。</p>
            <div>
                <label for="forgot-account" class="archive-label">账号</label>
                <input id="forgot-account" v-model="accountNumber" type="text" class="archive-input" required />
            </div>
            <button type="submit" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500 w-full">获取安全问题</button>
        </form>

        <!-- 步骤 2: 回答问题并重置密码 -->
        <form v-if="step === 2" @submit.prevent="resetPassword" class="space-y-4">
            <div v-for="(question, index) in securityQuestions" :key="index">
                <label :for="`ans-${index}`" class="archive-label">{{ question }}</label>
                <input :id="`ans-${index}`" v-model="answers[index]" type="text" class="archive-input" required />
            </div>
            <div>
                <label for="new-password" class="archive-label">新密码</label>
                <input id="new-password" v-model="newPassword" type="password" class="archive-input" required />
            </div>
            <button type="submit" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500 w-full">确认并重置密码</button>
        </form>

        <p class="text-xs text-center">
            <button type="button" @click="emit('back-to-login')" class="text-cyan-400 hover:underline">返回登录</button>
        </p>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { apiService } from '~/services/api';
import { useUIStore } from '~/stores/ui';

const emit = defineEmits(['back-to-login']);

const uiStore = useUIStore();
const step = ref(1);
const accountNumber = ref('');
const securityQuestions = ref<string[]>([]);
const answers = ref(['', '', '']);
const newPassword = ref('');

async function fetchQuestions() {
    try {
        const response = await apiService.getSecurityQuestions({ account_number: accountNumber.value });
        securityQuestions.value = response.questions;
        step.value = 2;
    } catch (error) {
        uiStore.setGlobalError(`获取安全问题失败: ${error}`);
    }
}

async function resetPassword() {
    try {
        await apiService.resetPassword({
            account_number: accountNumber.value,
            answers: answers.value,
            new_password: newPassword.value
        });
        uiStore.setGlobalError("密码重置成功！请使用新密码登录。");
        emit('back-to-login');
    } catch (error) {
        uiStore.setGlobalError(`重置密码失败: ${error}`);
    }
}
</script>