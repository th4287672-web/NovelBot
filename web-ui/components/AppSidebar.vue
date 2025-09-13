<template>
  <aside 
    class="h-full shrink-0 transition-all duration-300 ease-in-out bg-gray-800 relative border-r border-gray-700 flex flex-col"
    :class="persistentState.isSidebarCollapsed ? 'w-20' : 'w-64'"
  >
    <button 
        @click="uiStore.toggleSidebar" 
        class="absolute top-1/2 -translate-y-1/2 bg-gray-700 hover:bg-gray-600 p-1 rounded-full shadow-lg transition-all duration-300 ease-in-out z-20 focus:outline-none -right-3 transform"
        :class="{'rotate-180': persistentState.isSidebarCollapsed}"
        title="切换侧边栏"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
    </button>

    <div class="flex-grow flex flex-col justify-between overflow-hidden p-3">
      <nav class="flex flex-col space-y-2">
        <NuxtLink
          v-for="item in navItems.main"
          :key="item.path"
          :to="item.path === '/chat' ? chatLink : item.path"
          class="flex items-center p-3 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          active-class="bg-cyan-700 text-white font-semibold"
          :title="item.name"
        >
          <div class="shrink-0" v-html="item.icon"></div>
          <div 
            class="ml-4 transition-opacity duration-200 whitespace-nowrap overflow-hidden min-w-0"
            :class="persistentState.isSidebarCollapsed ? 'opacity-0' : 'opacity-100'"
          >
            <span>{{ item.name }}</span>
          </div>
        </NuxtLink>
        <NuxtLink
          to="/tasks"
          class="flex items-center p-3 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-colors relative"
          active-class="bg-cyan-700 text-white font-semibold"
          title="任务中心"
        >
          <div class="shrink-0" v-html="navItems.tasks.icon"></div>
          <div 
            class="ml-4 transition-opacity duration-200 whitespace-nowrap overflow-hidden min-w-0"
            :class="persistentState.isSidebarCollapsed ? 'opacity-0' : 'opacity-100'"
          >
            <span>任务中心</span>
          </div>
          <span v-if="activeTaskCount > 0" class="absolute top-1 right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {{ activeTaskCount }}
          </span>
        </NuxtLink>
      </nav>
      
      <nav class="flex flex-col space-y-2">
        <NuxtLink
          v-for="item in navItems.footer"
          :key="item.path"
          :to="item.path"
          class="flex items-center p-3 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          active-class="bg-cyan-700 text-white font-semibold"
          :title="item.name"
        >
          <div v-if="item.path === '/me' && getResourceUrl(settingsStore.userInfo)" class="shrink-0">
            <img :key="settingsStore.userInfo?.avatar || settingsStore.userInfo?.user_id" :src="getResourceUrl(settingsStore.userInfo)!" class="h-6 w-6 rounded-full object-cover">
          </div>
          <div v-else class="shrink-0" v-html="item.icon"></div>
          <div 
            class="ml-4 transition-opacity duration-200 whitespace-nowrap overflow-hidden min-w-0"
            :class="persistentState.isSidebarCollapsed ? 'opacity-0' : 'opacity-100'"
          >
            <span>{{ item.name }}</span>
          </div>
        </NuxtLink>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUIStore } from '~/stores/ui';
import { useSettingsStore } from '~/stores/settings';
import { useTaskStore } from '~/stores/taskStore';
import { useSessionStore } from '~/stores/sessionStore';
import { storeToRefs } from 'pinia';
import { getResourceUrl } from '~/utils/urlBuilder';

const uiStore = useUIStore();
const settingsStore = useSettingsStore();
const taskStore = useTaskStore();
const sessionStore = useSessionStore();
const { persistentState } = storeToRefs(uiStore);
const { activeSessionId } = storeToRefs(sessionStore);

const activeTaskCount = computed(() => {
    return Object.values(taskStore.tasks).filter(t => t.status === 'processing').length;
});

const chatLink = computed(() => {
  return activeSessionId.value ? `/chat/${activeSessionId.value}` : '/chat/new';
});

const navItems = {
  main: [
    { name: '聊天', path: '/chat', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>` },
    { name: '角色卡', path: '/characters', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>` },
    { name: '群聊场景', path: '/groups', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>` },
    { name: '用户人设', path: '/personas', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" /></svg>` },
    { name: '世界书', path: '/worlds', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2h10a2 2 0 002-2v-1a2 2 0 012-2h1.945M7.737 16.525l.41-1.025a1 1 0 011.696 0l.41 1.025a1 1 0 001.218.665l1.026-.41a1 1 0 011.085 1.085l-.41 1.026a1 1 0 00.665 1.218l1.025.41a1 1 0 010 1.696l-1.025.41a1 1 0 00-.665 1.218l.41 1.026a1 1 0 01-1.085-1.085l-1.026-.41a1 1 0 00-1.218.665l-.41 1.025a1 1 0 01-1.696 0l-.41-1.025a1 1 0 00-1.218-.665l-1.026.41a1 1 0 01-1.085-1.085l.41-1.026a1 1 0 00-.665-1.218l-1.025-.41a1 1 0 010-1.696l1.025.41a1 1 0 00.665-1.218l-.41-1.026a1 1 0 011.085-1.085l1.026.41a1 1 0 001.218.665z" /></svg>` },
    { name: '预设', path: '/presets', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>` },
    { name: '工具箱', path: '/tools', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>` },
  ],
  tasks: { name: '任务中心', path: '/tasks', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>` },
  footer: [
    { name: '设置', path: '/settings', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6V4m0 16v-2m0-8v-2m0 12V10m6 6h2m-16 0h2m8 0h2M4 12H2m16 0h2M12 8a2 2 0 100-4 2 2 0 000 4zm0 12a2 2 0 100-4 2 2 0 000 4zm8-6a2 2 0 100-4 2 2 0 000 4zm-16 0a2 2 0 100-4 2 2 0 000 4z" /></svg>` },
    { name: '我的', path: '/me', icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>` },
  ]
};
</script>