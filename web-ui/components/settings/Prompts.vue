<template>
    <div class="space-y-6 max-w-4xl mx-auto">
        <section class="space-y-4">
            <h2 class="text-lg font-semibold text-cyan-400">AI 生成提示词</h2>
            <p class="text-sm text-gray-400">
                自定义用于AI辅助生成功能的系统提示词。如果留空，系统将使用内置的默认提示词。
            </p>
          
            <div v-for="profile in editableProfiles" :key="profile.key">
                <label :for="String(profile.key)" class="archive-label">{{ profile.label }}</label>
                <textarea
                v-if="localProfiles[profile.key]"
                :id="String(profile.key)"
                v-model="(localProfiles[profile.key] as GenerationProfile).prompt"
                rows="6"
                class="archive-textarea font-mono text-sm focus:border-cyan-500"
                :placeholder="profile.placeholder"
                ></textarea>
            </div>
        </section>
        <footer class="pt-6 text-right w-full">
            <button @click="saveSettings" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">
                保存所有设置
            </button>
        </footer>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore } from '~/stores/settings';
import { useUIStore } from '~/stores/ui';
import type { UserConfig, GenerationProfile, OptionsProfile } from '~/types/api';
import { deepClone } from '~/utils/helpers';

type GenerationProfiles = UserConfig['generation_profiles'];
type EditableProfileKey = keyof GenerationProfiles;

const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const { userConfig } = storeToRefs(settingsStore);

const localProfiles = ref<Partial<GenerationProfiles>>({});

const editableProfiles: { key: EditableProfileKey; label: string; placeholder: string }[] = [
  { key: 'thought', label: '思维链 (事后) 提示词', placeholder: '留空则使用系统默认提示词' },
  { key: 'story_option', label: '剧情选项提示词', placeholder: '留空则使用系统默认提示词' },
  { key: 'character_card', label: 'AI 辅助生成角色卡提示词', placeholder: '留空则使用系统默认提示词' },
  { key: 'user_persona', label: 'AI 辅助生成用户人设提示词', placeholder: '留空则使用系统默认提示词' },
  { key: 'world_info', label: 'AI 辅助生成世界书提示词', placeholder: '留空则使用系统默认提示词' },
];

watch(userConfig, (newConfig) => {
  if (newConfig) {
    const profiles = newConfig.generation_profiles || {};
    const fullLocalProfiles: GenerationProfiles = {} as GenerationProfiles;
    for (const profile of editableProfiles) {
      const defaultProfile: GenerationProfile | OptionsProfile = {
          prompt: '',
          target_length: 'medium',
          ...(profile.key === 'story_option' && { count: 3 })
      };
      fullLocalProfiles[profile.key] = { ...defaultProfile, ...(profiles[profile.key] || {}) };
    }
    localProfiles.value = fullLocalProfiles;
  }
}, { immediate: true, deep: true });

async function saveSettings() {
  try {
    await settingsStore.updateUserConfigValue('generation_profiles', localProfiles.value as GenerationProfiles);
    uiStore.setGlobalError('提示词设置已成功保存！');
  } catch (error) {
    uiStore.setGlobalError(`保存提示词设置失败: ${error}`);
  }
}
</script>