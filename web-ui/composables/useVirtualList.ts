// 简体中文注释：
// 这是一个封装了 @tanstack/vue-virtual 库核心功能的可复用 Composable。
// 它简化了在项目中创建高性能虚拟列表的逻辑。

import { useVirtualizer } from '@tanstack/vue-virtual';
import { ref, computed, type Ref } from 'vue';

interface UseVirtualListOptions<T> {
  // 要进行虚拟化渲染的数据列表
  items: Ref<T[]>;
  // 滚动容器的引用
  containerRef: Ref<HTMLElement | null>;
  // 每个项目的预估高度（像素）
  estimateHeight: number;
}

export function useVirtualList<T>({
  items,
  containerRef,
  estimateHeight,
}: UseVirtualListOptions<T>) {

  // 创建一个虚拟化实例
  const rowVirtualizer = useVirtualizer({
    // 数据项的总数
    count: computed(() => items.value.length),
    // 获取滚动元素的函数
    getScrollElement: () => containerRef.value,
    // 预估每个项目的高度
    estimateSize: () => estimateHeight,
    // 在项目数量变化时，自动滚动到底部
    onChange: (instance) => {
      // [代码注释] 检查列表是否滚动到了最底部
      if (instance.range.endIndex >= instance.options.count - 2) {
        containerRef.value?.scrollTo({
            top: instance.getTotalSize(),
            behavior: 'smooth'
        });
      }
    },
    // 为平滑滚动提供一些额外的渲染项
    overscan: 5,
  });

  // 获取虚拟化后的可见项目列表
  const virtualItems = computed(() => rowVirtualizer.value.getVirtualItems());
  // 获取整个列表的总高度
  const totalSize = computed(() => rowVirtualizer.value.getTotalSize());

  return {
    virtualItems,
    totalSize,
  };
}