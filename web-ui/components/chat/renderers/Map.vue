<template>
  <div v-if="parseError" class="text-xs text-red-400 my-2 p-2 bg-red-900/30 rounded">
     [地图渲染错误: {{ parseError }}]
  </div>
  <div v-else class="my-2 border border-gray-700 rounded-lg overflow-hidden bg-gray-800 aspect-video relative">
    <svg class="w-full h-full" :viewBox="`0 0 ${viewBoxSize} ${viewBoxSize}`">
      <path :d="gridPath" stroke-width="0.5" class="stroke-gray-700" />
      <g 
        v-for="(marker, index) in markersData" 
        :key="index" 
        :transform="`translate(${normalizeX(marker.lng)}, ${normalizeY(marker.lat)})`"
        class="cursor-pointer group"
        @click="activeMarker = activeMarker === index ? null : index"
      >
        <!-- [核心修复] 为SVG的 <circle> 标签添加正确的自闭合 -->
        <circle cx="0" cy="0" r="4" class="fill-red-500 group-hover:fill-red-400 transition-colors" />
        <circle cx="0" cy="0" r="8" class="fill-red-500/30 group-hover:fill-red-400/40 transition-colors" />
      </g>
    </svg>
    <div 
      v-if="activeMarker !== null && markersData[activeMarker]"
      class="absolute p-2 text-xs bg-gray-900 text-white rounded-md shadow-lg pointer-events-none transition-all"
      :style="{ 
        left: `${normalizeX(markersData[activeMarker]!.lng)}px`, 
        top: `${normalizeY(markersData[activeMarker]!.lat)}px`,
        transform: 'translate(-50%, -120%)' 
      }"
    >
      {{ markersData[activeMarker]!.popup }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue';

interface Marker {
  lat: number;
  lng: number;
  popup: string;
}

const props = defineProps<{
  lat: string; 
  lng: string;
  markers?: string;
}>();

const viewBoxSize = 200;
const activeMarker = ref<number | null>(null);
const parseError = ref<string | null>(null);
const markersData = ref<Marker[]>([]);

// UTF-8 safe Base64 decoding function
function base64UrlDecode(str: string): string {
  try {
    const binaryString = atob(str.replace(/-/g, '+').replace(/_/g, '/'));
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return new TextDecoder('utf-8').decode(bytes);
  } catch (e) {
    throw new Error('无效的 Base64 字符串');
  }
}

watchEffect(() => {
  markersData.value = [];
  parseError.value = null;

  const markersString = props.markers || '';
  if (!markersString.trim()) return;

  try {
    const decodedMarkers = base64UrlDecode(markersString);
    const parsed = JSON.parse(decodedMarkers);

    if (Array.isArray(parsed)) {
      markersData.value = parsed;
    } else {
       parseError.value = "标记数据不是一个有效的数组。";
    }
  } catch (e) {
    console.error("Failed to decode/parse map markers:", markersString, e);
    if (e instanceof Error) {
        parseError.value = e.message;
    } else {
        parseError.value = "未知解析错误";
    }
  }
});

const normalizeX = (lng: number) => ((Number(lng) + 180) / 360) * viewBoxSize;
const normalizeY = (lat: number) => viewBoxSize - ((Number(lat) + 90) / 180) * viewBoxSize;

const gridPath = computed(() => {
    let path = '';
    const step = viewBoxSize / 10;
    for (let i = 1; i < 10; i++) {
        path += `M ${i * step} 0 V ${viewBoxSize} `;
        path += `M 0 ${i * step} H ${viewBoxSize} `;
    }
    return path;
});
</script>