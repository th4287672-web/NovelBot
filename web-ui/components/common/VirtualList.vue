<template>
  <div ref="scrollContainer" class="h-full w-full overflow-y-auto" @scroll="handleScroll">
    <div 
      class="relative w-full"
      :style="{ height: `${totalHeight}px` }"
    >
      <div 
        v-for="item in visibleItems" 
        :key="item.data.id"
        class="absolute top-0 left-0 w-full"
        :style="{ transform: `translateY(${item.top}px)` }"
      >
        <!-- [核心修复] 将自闭合的 <slot /> 改为完整的 <slot>...</slot> 标签对 -->
        <slot :item="item.data"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends { id: number | string }">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useElementSize } from '@vueuse/core';

const props = defineProps<{
  items: T[];
  estimateHeight?: number;
}>();

const scrollContainer = ref<HTMLElement | null>(null);
const scrollTop = ref(0);
const { height: containerHeight } = useElementSize(scrollContainer);

const itemHeights = ref<Record<string | number, number>>({});
const estimatedHeight = props.estimateHeight ?? 100;

const measurements = computed(() => {
  let totalHeight = 0;
  const itemsWithPositions = props.items.map(item => {
    const height = itemHeights.value[item.id] || estimatedHeight;
    const top = totalHeight;
    totalHeight += height;
    return { data: item, height, top };
  });
  return { itemsWithPositions, totalHeight };
});

const totalHeight = computed(() => measurements.value.totalHeight);
const itemsWithPositions = computed(() => measurements.value.itemsWithPositions);

function findStartIndex(items: { top: number, height: number }[], scrollPos: number): number {
    let low = 0;
    let high = items.length - 1;
    let index = high;

    while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        const item = items[mid];
        if (!item) { high = mid - 1; continue; }

        if (item.top + item.height >= scrollPos) {
            index = mid;
            high = mid - 1;
        } else {
            low = mid + 1;
        }
    }
    return index;
}

const visibleItems = computed(() => {
  const allItems = itemsWithPositions.value;
  if (allItems.length === 0) return [];
  
  const startIndex = findStartIndex(allItems, scrollTop.value);

  let endIndex = startIndex;
  let currentTop = allItems[startIndex]?.top ?? 0;
  while (endIndex < allItems.length - 1 && currentTop < scrollTop.value + containerHeight.value) {
    endIndex++;
    currentTop += allItems[endIndex]?.height ?? 0;
  }
  
  return allItems.slice(
    Math.max(0, startIndex - 5), 
    endIndex + 5 
  );
});

function handleScroll() {
  if (scrollContainer.value) {
    scrollTop.value = scrollContainer.value.scrollTop;
  }
}

onMounted(() => {
  let observer: ResizeObserver;
  
  const initObserver = () => {
    observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        // [FIX] 添加安全检查
        const borderBoxSize = entry.borderBoxSize[0];
        if (borderBoxSize) {
          const id = (entry.target as HTMLElement).parentElement?.dataset.id;
          if (id) {
            // 使用 requestAnimationFrame 避免布局抖动
            requestAnimationFrame(() => {
              itemHeights.value[id] = borderBoxSize.blockSize;
            });
          }
        }
      }
    });

    watch(visibleItems, (newVisible) => {
      nextTick(() => {
          if (!scrollContainer.value) return;
          observer.disconnect();
          newVisible.forEach(item => {
              const el = scrollContainer.value?.querySelector(`[data-id='${item.data.id}']`);
              if (el && el.children[0]) {
                  observer.observe(el.children[0]);
              }
          });
      });
    }, { deep: true, immediate: true });
  };
  
  watch(containerHeight, (h) => {
    if (h > 0 && !observer) {
      initObserver();
    }
  }, { immediate: true });

  watch(() => props.items.length, (newLength, oldLength) => {
    if (newLength > oldLength && scrollContainer.value) {
      nextTick(() => {
        // 使用平滑滚动
        scrollContainer.value!.scrollTo({ top: scrollContainer.value!.scrollHeight, behavior: 'smooth' });
      });
    }
  });

  onUnmounted(() => {
    if (observer) observer.disconnect()
  });
});

</script>