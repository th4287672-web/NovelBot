<template>
  <div class="h-full w-full p-6 flex flex-col items-center">
    <div class="w-full max-w-3xl space-y-6">
      <div class="text-center">
        <h2 class="text-2xl font-bold text-indigo-300">故事编织者</h2>
        <p class="text-gray-400 mt-2">输入一个核心创意，AI将为您构建一个完整的可玩故事包。</p>
      </div>

      <div class="space-y-2">
        <label for="story-prompt" class="archive-label">核心创意</label>
        <textarea
          id="story-prompt"
          v-model="prompt"
          rows="4"
          class="archive-textarea focus:border-indigo-500"
          placeholder="例如：一个失忆的仿生人侦探，在霓虹灯下的反乌托邦都市中，追查一系列与他自身过去相关的神秘谋杀案。"
        ></textarea>
      </div>

      <button
        @click="weaveStory"
        :disabled="!prompt.trim() || isLoading"
        class="btn btn-primary bg-indigo-600 hover:bg-indigo-500 w-full text-lg"
      >
        <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ isLoading ? '正在编织故事...' : '开始编织' }}
      </button>

      <transition name="fade">
        <div v-if="generatedPackage" class="p-4 bg-gray-800/50 border border-gray-700 rounded-lg space-y-4">
          <h3 class="text-lg font-semibold text-green-400">🎉 故事包生成成功！</h3>
          <p class="text-sm text-gray-300">AI为您创建了以下内容，确认后将自动添加到您的资料库中：</p>
          <ul class="text-sm list-disc list-inside space-y-1 text-gray-400">
            <li>主角: <span class="font-semibold text-white">{{ generatedPackage.main_character.name }}</span></li>
            <li>NPCs ({{ generatedPackage.npcs.length }}个): <span class="font-semibold text-white">{{ generatedPackage.npcs.map((n: Character) => n.name).join(', ') }}</span></li>
            <li>世界书: <span class="font-semibold text-white">{{ generatedPackage.world_info.name }}</span> ({{ generatedPackage.world_info.entries.length }}个条目)</li>
            <li>开场场景: <span class="font-semibold text-white">{{ generatedPackage.group.name }}</span></li>
          </ul>
          <div class="flex justify-end gap-3 pt-3 border-t border-gray-700">
            <button @click="generatedPackage = null" class="btn btn-secondary">丢弃</button>
            <button @click="savePackage" class="btn btn-primary bg-green-600 hover:bg-green-500">确认并保存</button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useUIStore } from '~/stores/ui';
import { useSettingsStore } from '~/stores/settings';
import { apiService } from '~/services/api';
import { useInvalidateAllData } from '~/composables/useAllData';
import type { StoryPackage, Character } from '~/types/api';

const uiStore = useUIStore();
const settingsStore = useSettingsStore();
const invalidateAllData = useInvalidateAllData();

const prompt = ref('');
const isLoading = ref(false);
const generatedPackage = ref<StoryPackage | null>(null);

async function weaveStory() {
  if (!settingsStore.userId) {
    uiStore.setGlobalError("用户未登录，无法生成故事。");
    return;
  }
  isLoading.value = true;
  generatedPackage.value = null;
  uiStore.setGlobalError(null);
  try {
    const response = await apiService.weaveStory(settingsStore.userId, prompt.value);
    generatedPackage.value = response.data;
  } catch (error) {
    uiStore.setGlobalError(`故事生成失败: ${error}`);
  } finally {
    isLoading.value = false;
  }
}

async function savePackage() {
    if (!generatedPackage.value || !settingsStore.userId) return;
    
    const { main_character, npcs, world_info, group } = generatedPackage.value;
    
    // 从角色数据中移除 is_private 和 filename，因为它们是前端状态
    const prepareCharData = (char: any) => {
        const { is_private, filename, ...data } = char;
        return data;
    };

    const allCharacters = [main_character, ...npcs];
    
    try {
        const savedCharFilenames = await Promise.all(
            allCharacters.map(char => 
                apiService.createOrUpdateData(settingsStore.userId!, 'character', char.name, prepareCharData(char), false)
                .then(res => res.filename)
            )
        );

        const { filename: wf, is_private: wip, ...worldData } = world_info as any;
        await apiService.createOrUpdateData(settingsStore.userId!, 'world_info', worldData.name, worldData, false);
        
        const { filename: gf, is_private: gip, ...groupData } = group as any;
        groupData.character_filenames = savedCharFilenames;
        await apiService.createOrUpdateData(settingsStore.userId!, 'group', groupData.name, groupData, false);
        
        await invalidateAllData();
        uiStore.setGlobalError('故事包已成功保存！');
        generatedPackage.value = null;
        prompt.value = '';

    } catch (error) {
        uiStore.setGlobalError(`保存故事包时出错: ${error}`);
    }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>