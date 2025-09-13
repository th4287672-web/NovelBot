import { useVirtualizer, type Virtualizer } from '@tanstack/vue-virtual';
import { ref, computed, type Ref, watch } from 'vue';

interface UseVirtualListOptions<T> {
  items: Ref<T[]>;
  containerRef: Ref<HTMLElement | null>;
  estimateHeight: number;
}

export function useVirtualList<T>({
  items,
  containerRef,
  estimateHeight,
}: UseVirtualListOptions<T>) {

  const rowVirtualizer = useVirtualizer({
    count: items.value.length,
    getScrollElement: () => containerRef.value,
    estimateSize: () => estimateHeight,
    onChange: (instance) => {
      if (!instance.range) return;
      if (instance.range.endIndex >= instance.options.count - 2) {
        containerRef.value?.scrollTo({
            top: instance.getTotalSize(),
            behavior: 'smooth'
        });
      }
    },
    overscan: 5,
  });
  
  watch(items, () => {
      (rowVirtualizer.value.options as any).count = items.value.length;
  });

  const virtualItems = computed(() => rowVirtualizer.value.getVirtualItems());
  const totalSize = computed(() => rowVirtualizer.value.getTotalSize());

  return {
    virtualItems,
    totalSize,
  };
}