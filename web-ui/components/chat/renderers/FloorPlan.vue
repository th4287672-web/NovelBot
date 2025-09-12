<template>
  <div class="my-2 p-2 bg-gray-800 border border-gray-700 rounded-lg">
    <div v-if="parseError" class="text-xs text-red-400 p-2 bg-red-900/30 rounded">
      [平面图渲染错误: {{ parseError }}]
    </div>
    <div v-else class="w-full flex items-center justify-center">
      <svg :viewBox="planData.viewBox" class="max-w-full max-h-[60vh] bg-gray-900/50 rounded">
        <!-- [核心升级] 渲染自定义区域 -->
        <rect
          v-for="area in planData.areas"
          :key="area.id"
          :x="area.rect[0]"
          :y="area.rect[1]"
          :width="area.rect[2]"
          :height="area.rect[3]"
          :fill="area.fill || '#555'"
          :stroke="area.stroke || 'none'"
          stroke-width="0.1"
        />
        <!-- [核心升级] 渲染路径 -->
        <path
          v-for="(path, index) in planData.paths"
          :key="`path-${index}`"
          :d="path.d"
          :stroke="path.stroke || '#888'"
          :stroke-width="path.strokeWidth || 0.3"
          fill="none"
        />
        <!-- 渲染房间 -->
        <g v-for="room in planData.rooms" :key="room.id">
          <rect
            :x="room.rect[0]"
            :y="room.rect[1]"
            :width="room.rect[2]"
            :height="room.rect[3]"
            :fill="room.fill || '#4A5568'"
            :stroke="room.stroke || '#718096'"
            stroke-width="0.2"
          />
        </g>
        <!-- [核心升级] 渲染对象 -->
         <g v-for="(obj, index) in planData.objects" :key="`obj-${index}`" :transform="`translate(${obj.pos[0]}, ${obj.pos[1]})`">
            <rect v-if="obj.shape === 'rect'" :width="obj.size[0]" :height="obj.size[1]" :x="-obj.size[0]/2" :y="-obj.size[1]/2" :fill="obj.fill || '#9F7AEA'" />
            <circle v-else cx="0" cy="0" :r="obj.size[0] / 2" :fill="obj.fill || '#48BB78'" />
        </g>
        <!-- 渲染门窗 (保持不变) -->
        <rect v-for="(door, index) in planData.doors" :key="`door-${index}`" :x="door.pos[0]-(door.width>door.height?door.width/2:0.1)" :y="door.pos[1]-(door.height>door.width?door.height/2:0.1)" :width="door.width" :height="door.height" class="fill-amber-800"/>
        <rect v-for="(window, index) in planData.windows" :key="`window-${index}`" :x="window.pos[0]-(window.width>window.height?window.width/2:0.1)" :y="window.pos[1]-(window.height>window.width?window.height/2:0.1)" :width="window.width" :height="window.height" class="fill-cyan-500"/>
        
        <!-- 渲染文字标签 (房间+独立标签) -->
        <text v-for="room in planData.rooms" :key="room.id" :x="room.rect[0]+room.rect[2]/2" :y="room.rect[1]+room.rect[3]/2" :font-size="room.fontSize" class="fill-gray-300 font-sans" text-anchor="middle" dominant-baseline="middle">{{ room.name }}</text>
        <text v-for="(label, index) in planData.labels" :key="`label-${index}`" :x="label.pos[0]" :y="label.pos[1]" :font-size="label.fontSize || 2" :fill="label.fill || '#E2E8F0'" class="font-sans" text-anchor="middle">{{ label.text }}</text>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, useSlots } from 'vue';

// [核心升级] 扩展数据接口
interface Room { id: string; name: string; rect: [number, number, number, number]; fontSize: number; fill?: string; stroke?: string; }
interface Area { id: string; rect: [number, number, number, number]; fill?: string; stroke?: string; }
interface Path { d: string; stroke?: string; strokeWidth?: number; }
interface SvgObject { shape: 'rect' | 'circle'; pos: [number, number]; size: [number, number]; fill?: string; }
interface Label { text: string; pos: [number, number]; fontSize?: number; fill?: string; }
interface Door { pos: [number, number]; width: number; height: number; }
interface Window { pos: [number, number]; width: number; height: number; }
interface PlanData { rooms: Room[]; areas: Area[]; paths: Path[]; objects: SvgObject[]; labels: Label[]; doors: Door[]; windows: Window[]; }

const slots = useSlots();
const parseError = ref<string | null>(null);

const planData = computed(() => {
  parseError.value = null;
  const defaultSlot = slots.default?.();
  const rawContent = defaultSlot?.[0]?.children?.toString() || '';
  const commentMatch = rawContent.match(/<!--([\s\S]*)-->/);
  const jsonString = commentMatch?.[1]?.trim();

  const emptyPlan = { rooms:[], areas:[], paths:[], objects:[], labels:[], doors:[], windows:[], viewBox:'0 0 100 100' };

  if (!jsonString) {
    parseError.value = "在 <FloorPlan> 标签内未找到有效的JSON注释块。";
    return emptyPlan;
  }

  try {
    const data: Partial<PlanData> = JSON.parse(jsonString);
    const rooms = (data.rooms || []).map(room => {
      const smallerSide = Math.min(room.rect[2], room.rect[3]);
      const fontSize = Math.min(smallerSide * 0.3, 2);
      return { ...room, fontSize };
    });
    
    // [核心升级] 解析新增的元素类型
    const areas = data.areas || [];
    const paths = data.paths || [];
    const objects = data.objects || [];
    const labels = data.labels || [];
    const doors = data.doors || [];
    const windows = data.windows || [];

    const allRects = [...rooms.map(r => r.rect), ...areas.map(a => a.rect)];
    if (allRects.length === 0) {
        parseError.value = "JSON数据中至少需要一个 'rooms' 或 'areas'。";
        return emptyPlan;
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const rect of allRects) {
        minX = Math.min(minX, rect[0]);
        minY = Math.min(minY, rect[1]);
        maxX = Math.max(maxX, rect[0] + rect[2]);
        maxY = Math.max(maxY, rect[1] + rect[3]);
    }
    const padding = 2;
    const x = minX - padding;
    const y = minY - padding;
    const width = (maxX - minX) + (padding * 2);
    const height = (maxY - minY) + (padding * 2);

    return { rooms, areas, paths, objects, labels, doors, windows, viewBox: `${x} ${y} ${width} ${height}` };
  } catch (e) {
    console.error('解析平面图JSON失败:', e);
    parseError.value = e instanceof Error ? e.message : "未知的JSON解析错误";
    return emptyPlan;
  }
});
</script>