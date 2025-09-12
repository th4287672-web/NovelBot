import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue';
import * as echarts from 'echarts';
import { useResizeObserver } from '@vueuse/core';

export function useEcharts(container: Ref<HTMLElement | null>) {
  const chartInstance = ref<echarts.ECharts | null>(null);

  const initChart = () => {
    if (container.value && !chartInstance.value) {
      chartInstance.value = echarts.init(container.value, 'dark', { renderer: 'svg' });
    }
  };

  const setOption = (option: echarts.EChartsOption | null, notMerge = false) => {
    if (!chartInstance.value) {
      initChart();
    }
    if (chartInstance.value && option) {
      const defaultGrid = { top: '15%', right: '5%', bottom: '15%', left: '10%', containLabel: true };
      
      const finalOption = { 
        ...option, 
        grid: Array.isArray(option.grid) 
          ? option.grid 
          : { ...defaultGrid, ...(option.grid || {}) }
      };
      
      chartInstance.value.setOption(finalOption, notMerge);
    }
  };

  const resizeChart = () => {
    chartInstance.value?.resize();
  };

  useResizeObserver(container, resizeChart);

  onMounted(() => {
    initChart();
  });

  onUnmounted(() => {
    chartInstance.value?.dispose();
  });

  watch(container, (newEl) => {
    if (newEl && !chartInstance.value) {
      initChart();
    }
  });

  return {
    setOption,
    chartInstance
  };
}
