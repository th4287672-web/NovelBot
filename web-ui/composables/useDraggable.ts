import { ref, type Ref } from 'vue';

// T 是我们想要拖拽的数组元素的类型
export function useDraggable<T>(
  list: Ref<T[]>,
  onUpdate: (newList: T[]) => void
) {
  const draggedItemIndex = ref<number | null>(null); // 正在被拖拽的元素的索引

  // [FIX] 显式接收 event 参数
  const onDragStart = (event: DragEvent, index: number) => {
    // [FIX] 类型断言并进行安全检查
    const target = event.currentTarget as HTMLElement;
    if (!target) return;

    draggedItemIndex.value = index;
    // 添加一个视觉效果，让被拖拽的元素半透明
    target.classList.add('dragging');
  };

  const onDragOver = (event: DragEvent) => {
    // 必须阻止默认行为，浏览器才能允许放置 (drop)
    event.preventDefault();
    const target = event.currentTarget as HTMLElement;
    if (target) {
      // 为放置目标添加一个高亮边框
      target.classList.add('drag-over');
    }
  };
  
  const onDragLeave = (event: DragEvent) => {
    const target = event.currentTarget as HTMLElement;
    if (target) {
      target.classList.remove('drag-over');
    }
  };

  // [FIX] 显式接收 event 参数
  const onDrop = (event: DragEvent, targetIndex: number) => {
    const target = event.currentTarget as HTMLElement;
    if (target) {
      target.classList.remove('drag-over');
    }
    
    if (draggedItemIndex.value === null || draggedItemIndex.value === targetIndex) {
      return;
    }

    const newList = [...list.value];
    // 从数组中“拿起”被拖拽的元素
    const [draggedItem] = newList.splice(draggedItemIndex.value, 1);

    // [FIX] 安全检查，确保 draggedItem 存在
    if (draggedItem === undefined) return;

    // 将它“放下”到新的位置
    newList.splice(targetIndex, 0, draggedItem);
    
    // 调用回调函数，通知父组件更新顺序
    onUpdate(newList);
    draggedItemIndex.value = null;
  };

  const onDragEnd = (event: DragEvent) => {
    // 清理所有视觉效果
    document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
    draggedItemIndex.value = null;
  };

  return {
    // [FIX] 移除不再需要的 targetRef
    onDragStart,
    onDragOver,
    onDragLeave,
    onDrop,
    onDragEnd,
  };
}