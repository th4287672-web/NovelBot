<template>
    <CommonBaseModal 
        :title="modalTitle"
        theme-color="green"
        max-width="80rem"
        @close="emit('close')"
    >
        <form @submit.prevent="save" class="space-y-6">
            <div>
                <label for="module-name" class="archive-label">模块名称</label>
                <input id="module-name" type="text" v-model="localModule.name" required class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2">
            </div>
            
            <div>
                <label for="module-content" class="archive-label">内容 (Prompt)</label>
                <textarea id="module-content" v-model="localModule.content" required rows="12" class="archive-textarea focus:border-green-500 focus:ring-green-500/30 focus:ring-2 font-mono text-sm"></textarea>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-gray-600/80 pt-4">
              <div>
                <label for="module-role" class="archive-label">角色 (Role)</label>
                <select id="module-role" v-model="localModule.role" class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2">
                  <option>system</option>
                  <option>user</option>
                  <option>assistant</option>
                </select>
              </div>
              <div>
                <label for="module-depth" class="archive-label">注入深度</label>
                <input id="module-depth" type="number" v-model.number="localModule.injection_depth" required class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2">
              </div>
               <div>
                <label for="module-order" class="archive-label">注入顺序</label>
                <input id="module-order" type="number" v-model.number="localModule.injection_order" class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2">
              </div>
            </div>
            <div class="flex items-center space-x-6">
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" v-model="localModule.system_prompt" class="form-checkbox h-4 w-4 bg-gray-700 border-gray-500 rounded text-green-500 focus:ring-green-500/50">
                  <span class="text-sm text-gray-300">系统提示 (System Prompt)</span>
                </label>
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" v-model="localModule.forbid_overrides" class="form-checkbox h-4 w-4 bg-gray-700 border-gray-500 rounded text-green-500 focus:ring-green-500/50">
                  <span class="text-sm text-gray-300">禁止覆盖 (Forbid Overrides)</span>
                </label>
            </div>

            <!-- [核心新增] 思维链模块配置 -->
            <div class="space-y-4 border-t border-gray-600/80 pt-4">
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" v-model="localModule.is_thought_module" class="form-checkbox h-4 w-4 bg-gray-700 border-gray-500 rounded text-green-500 focus:ring-green-500/50">
                  <span class="text-sm text-gray-300 font-semibold">这是一个思维链模块 (CoT)</span>
                </label>
                <div v-if="localModule.is_thought_module">
                    <label for="thinking-budget" class="archive-label">Thinking Budget (推理温度)</label>
                    <input id="thinking-budget" type="number" step="0.1" min="0" max="2" v-model.number="localModule.thinking_budget" class="archive-input focus:border-green-500 focus:ring-green-500/30 focus:ring-2">
                    <p class="text-xs text-gray-500 mt-1">控制AI思维过程的创造性。推荐值在 0.7 到 1.0 之间。0 表示禁用。</p>
                </div>
            </div>
        </form>
      
        <template #footer-actions>
            <button type="button" @click="emit('close')" class="btn btn-secondary">
                取消
            </button>
            <button type="submit" @click="save" :disabled="!isFormValid" class="btn btn-primary bg-green-600 hover:bg-green-500">
                保存模块
            </button>
        </template>
    </CommonBaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed, type PropType } from 'vue';
import type { PresetModule } from '@/types/api';
import { v4 as uuidv4 } from 'uuid';
import { deepClone } from '~/utils/helpers';

const props = defineProps({
    mode: {
        type: String as PropType<'create' | 'edit'>,
        required: true
    },
    module: {
        type: Object as PropType<PresetModule | null>,
        default: null
    },
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', module: PresetModule): void;
}>();

const getDefaultModule = (): PresetModule => ({
    identifier: uuidv4(),
    name: '新模块',
    system_prompt: true,
    enabled: true,
    marker: false,
    role: 'system',
    content: '',
    injection_position: 0,
    injection_depth: 4,
    injection_order: 100,
    forbid_overrides: false,
    is_thought_module: false,
    thinking_budget: 0.9,
});

const localModule = ref<PresetModule>(getDefaultModule());

const isFormValid = computed(() => {
  return localModule.value.name && localModule.value.content;
});

const modalTitle = computed(() => props.mode === 'edit' ? `编辑模块: ${props.module?.name}` : '新建模块');

watch(() => [props.mode, props.module], () => {
    if (props.mode === 'edit' && props.module) {
      localModule.value = deepClone(props.module);
    } else {
      localModule.value = getDefaultModule();
    }
}, { immediate: true, deep: true });

function save() {
  if (isFormValid.value) {
    emit('save', localModule.value);
  }
}
</script>