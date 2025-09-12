<template>
    <div class="p-8 flex flex-col h-full">
        <h2 class="text-2xl font-bold text-center text-cyan-400 shrink-0 mb-6">注册新账号</h2>
        <form @submit.prevent="handleRegister" class="flex-grow min-h-0 overflow-y-auto pr-2 -mr-4 space-y-4">
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                
                <div class="space-y-4">
                    <div>
                        <label for="reg-username" class="archive-label">用户名</label>
                        <input id="reg-username" v-model="registerForm.username" type="text" class="archive-input" required />
                    </div>
                    <div>
                        <label for="reg-password" class="archive-label">密码</label>
                        <input id="reg-password" v-model="registerForm.password" type="password" class="archive-input" required />
                    </div>
                     <div>
                        <label for="reg-digits" class="archive-label">随机账号位数</label>
                        <select id="reg-digits" v-model.number="registerForm.account_digits" class="archive-input">
                            <option>6</option><option>8</option><option>10</option>
                        </select>
                    </div>
                </div>

                <div class="space-y-4">
                    <div v-for="(q, index) in registerForm.security_questions" :key="index" class="space-y-2">
                         <label :for="`sq-question-${index}`" class="archive-label">安全问题 {{ index + 1 }}</label>
                         <input :id="`sq-question-${index}`" v-model="q.question" type="text" class="archive-input text-sm" placeholder="例如：我最喜欢的小学老师姓什么？" required />
                         <input :id="`sq-answer-${index}`" v-model="q.answer" type="text" class="archive-input text-sm" placeholder="输入答案" required />
                    </div>
                </div>
            </div>
            
            <div class="pt-4">
                <button type="submit" class="btn btn-primary bg-indigo-600 hover:bg-indigo-500 w-full">注册</button>
            </div>
        </form>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { apiService } from '~/services/api';
import { useUIStore } from '~/stores/ui';
import { useSettingsStore } from '~/stores/settings';
import type { UserInfo } from '~/types/api';

const emit = defineEmits<{
  (e: 'success', userInfo: UserInfo): void;
}>();

const uiStore = useUIStore();
const settingsStore = useSettingsStore();

const registerForm = ref({
    username: '',
    password: '',
    account_digits: 8,
    security_questions: [ { question: '', answer: '' }, { question: '', answer: '' }, { question: '', answer: '' } ]
});

async function handleRegister() {
    try {
        const payload = { ...registerForm.value, anonymous_user_id: settingsStore.userId };
        const response = await apiService.register(payload);
        uiStore.setGlobalError(`注册成功！您的新账号是: ${response.user_info.account_number}`);
        emit('success', response.user_info);
    } catch (error) {
        uiStore.setGlobalError(`注册失败: ${error}`);
    }
}
</script>