<template>
  <div class="p-6 h-full w-full flex flex-col">
    <h1 class="text-2xl font-bold text-gray-300 mb-2 shrink-0">系统设置</h1>
    
    <div class="flex-grow min-h-0">
        <CommonTabbedContent :tabs="tabs" initial-tab="api_keys" theme-color="cyan" class="h-full">
            
            <template #api_keys>
                <div class="h-full w-full p-4 overflow-y-auto">
                    <SettingsApiKeys />
                </div>
            </template>
            
            <template #tts>
                 <div class="h-full w-full p-4 overflow-y-auto">
                    <SettingsTts />
                 </div>
            </template>

            <template #prompts>
                 <div class="h-full w-full p-4 overflow-y-auto">
                    <SettingsPrompts />
                 </div>
            </template>

        </CommonTabbedContent>
    </div>
  </div>
</template>

<script setup lang="ts">
import CommonTabbedContent from '~/components/common/TabbedContent.vue';
import SettingsApiKeys from '~/components/settings/ApiKeys.vue';
import SettingsTts from '~/components/settings/Tts.vue';
import SettingsPrompts from '~/components/settings/Prompts.vue';

const tabs = [
    { id: 'api_keys', label: 'API 服务' },
    { id: 'tts', label: '语音合成' },
    { id: 'prompts', label: 'AI 生成提示词' },
];
</script>