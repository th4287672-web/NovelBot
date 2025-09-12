<template>
  <div class="h-full w-full p-6 flex items-center justify-center">
    <!-- 已登录用户视图 -->
    <div v-if="settingsStore.userInfo" class="w-full max-w-2xl bg-gray-800 rounded-lg shadow-2xl border border-gray-700 flex flex-col p-8 space-y-6">
        <h2 class="text-2xl font-bold text-center text-cyan-400">个人中心</h2>
        <div class="flex-grow space-y-4 bg-gray-900/50 p-4 rounded-md">
            <!-- [!! 已修改 !!] v-model绑定, 并且upload-function指向新函数 -->
            <CommonImageUploaderWithCropper
              v-model:image-url="localAvatarUrl"
              :key="settingsStore.userInfo.avatar || settingsStore.userInfo.user_id"
              cropper-title="裁剪头像"
              :aspect-ratio="1"
              :upload-function="uploadAvatarAndUpdate"
            />
            <div class="flex items-center gap-2">
              <p class="text-gray-400">用户名: <span class="font-semibold text-white">{{ settingsStore.userInfo.username }}</span></p>
              <button @click="isRenameModalOpen = true" class="text-xs text-cyan-400 hover:underline">(修改)</button>
            </div>
            <p class="text-gray-400">账号: <span class="font-semibold text-white">{{ settingsStore.userInfo.account_number }}</span></p>
            <div>
              <label class="text-gray-400">用户ID:</label>
              <div class="flex items-center gap-2 mt-1">
                <input :value="userId" type="text" class="archive-input !mt-0 flex-grow bg-gray-700 font-mono text-xs" readonly />
                <button @click="copyUserId" class="btn btn-secondary !px-3 !py-1.5 text-xs">复制</button>
              </div>
            </div>
        </div>
        <div class="flex gap-4">
           <button @click="logout" class="btn btn-secondary flex-1">退出登录</button>
           <button @click="isDeleteModalOpen = true" class="btn btn-danger flex-1">注销账号</button>
        </div>
    </div>

    <!-- 匿名/未登录用户视图 (保持不变) -->
    <div v-else class="w-full max-w-5xl h-full max-h-[90vh] bg-gray-800 rounded-lg shadow-2xl border border-gray-700 grid grid-cols-1 md:grid-cols-5 overflow-hidden">
      <div class="hidden md:flex flex-col items-center justify-center p-8 bg-gray-900/50 md:col-span-2">
          <svg class="w-24 h-24 text-cyan-500" fill="none" viewBox="0 0 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
          <h1 class="text-3xl font-bold text-cyan-400 mt-4">MyNovelBot</h1>
          <p class="mt-2 text-gray-400 text-center">您的私人AI角色扮演伙伴</p>
      </div>

      <div class="flex flex-col h-full md:col-span-3">
         <CommonTabbedContent :tabs="authTabs" :initial-tab="activeAuthTab" @update:active-tab="activeAuthTab = $event" theme-color="cyan" class="flex-grow min-h-0">
            <template #login> <AuthFormLogin @success="onLoginSuccess" @switch-to-forgot="activeAuthTab = 'forgot'" /> </template>
            <template #register> <AuthFormRegister @success="onLoginSuccess" /> </template>
            <template #forgot> <AuthFormForgotPassword @back-to-login="activeAuthTab = 'login'" /> </template>
         </CommonTabbedContent>
      </div>
    </div>
    
    <ClientOnly>
      <AuthAccountDeletionModal 
        v-if="isDeleteModalOpen"
        @close="isDeleteModalOpen = false"
        @confirm="handleDeleteAccount"
      />
      <AuthUsernameChangeModal
        v-if="isRenameModalOpen"
        @close="isRenameModalOpen = false"
        @confirm="handleRenameUsername"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
// [!! 新增 !!] 导入 useTaskStore
import { useTaskStore } from '~/stores/taskStore';
import type { UserInfo } from '~/types/api';
// [!! 新增 !!] 导入 getResourceUrl
import { getResourceUrl } from '~/utils/urlBuilder';

const settingsStore = useSettingsStore();
const uiStore = useUIStore();
// [!! 新增 !!] 获取 taskStore 实例
const taskStore = useTaskStore();
const router = useRouter();

const { userId } = storeToRefs(settingsStore);
const isDeleteModalOpen = ref(false);
const isRenameModalOpen = ref(false);
// [!! 已修改 !!] 使用 localAvatarUrl 和 watch 来更可靠地处理头像更新
const localAvatarUrl = ref(getResourceUrl(settingsStore.userInfo));

watch(() => settingsStore.userInfo?.avatar, (newAvatar) => {
    localAvatarUrl.value = getResourceUrl({ avatar: newAvatar, is_private: true, owner_id: settingsStore.userId });
});

const activeAuthTab = ref<'login' | 'register' | 'forgot'>('login');
const authTabs = [ { id: 'login', label: '登录' }, { id: 'register', label: '注册' }, { id: 'forgot', label: '找回密码' }];

const fullAvatarUrl = computed(() => getResourceUrl(settingsStore.userInfo));

function onLoginSuccess(userInfoPayload: UserInfo) {
    settingsStore.setUserInfo(userInfoPayload);
    settingsStore.setUserId(userInfoPayload.user_id);
    uiStore.setGlobalError("登录成功！正在加载您的数据...");
    router.push('/chat');
}

function logout() {
    settingsStore.logout();
}

// [!! 新增 !!] 创建适配器函数以封装任务提交和轮询逻辑
async function uploadAvatarAndUpdate(avatarBlob: Blob): Promise<string> {
  // 1. 提交上传任务并获取 task_id
  const taskSubmission = await settingsStore.uploadAvatar(avatarBlob);
  // 2. 使用 taskStore 的轮询工具等待任务完成
  const finalTask = await taskStore.pollTaskResult(taskSubmission.task_id);

  // 3. 检查任务结果
  if (finalTask.status === 'success' && finalTask.result.image_url) {
      const newUrl = finalTask.result.image_url;
      // 4. 更新用户信息
      if (settingsStore.userInfo) {
          const updatedUserInfo = { ...settingsStore.userInfo, avatar: newUrl };
          await settingsStore.updateUserInfo(updatedUserInfo);
      }
      // 5. 返回组件期望的 string 类型的 URL
      return newUrl;
  } else {
      // 如果任务失败，抛出错误
      throw new Error(finalTask.error?.error || "头像上传任务失败");
  }
}

async function handleRenameUsername(payload: { newUsername: string, password: string }) {
    isRenameModalOpen.value = false;
    try {
        await settingsStore.updateUsername(payload.newUsername, payload.password);
        uiStore.setGlobalError("用户名已成功更新！");
    } catch (error) {
         uiStore.setGlobalError(`用户名更新失败: ${error}`);
    }
}

async function handleDeleteAccount(password: string) {
    isDeleteModalOpen.value = false;
    try {
        await settingsStore.deleteAccount(password);
        uiStore.setGlobalError("账号已注销。");
    } catch (error) {
        uiStore.setGlobalError(`账号注销失败: ${error}`);
    }
}

async function copyUserId() {
    if (userId.value) {
        try {
            await navigator.clipboard.writeText(userId.value);
            uiStore.setGlobalError("用户ID已复制到剪贴板！");
        } catch (err) {
            uiStore.setGlobalError("复制失败，请手动复制。");
        }
    }
}
</script>