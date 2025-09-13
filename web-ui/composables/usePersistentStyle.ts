import { useStorage } from '@vueuse/core';
import { ref, watch, type Ref } from 'vue';

export interface TextStyle {
  fontSize: number; // in px
  color: string; // hex color
  fontFamily: string;
}

export interface StyleConfig {
  displayName: TextStyle;
  modelId: TextStyle;
}

const defaultStyles: StyleConfig = {
  displayName: {
    fontSize: 14,
    color: '#E5E7EB', // gray-200
    fontFamily: "'Roboto', sans-serif",
  },
  modelId: {
    fontSize: 11,
    color: '#6B7280', // gray-500
    fontFamily: "'Fira Code', monospace",
  },
};

export function usePersistentStyle(storageKey: string) {
  const styles = useStorage<StyleConfig>(storageKey, defaultStyles, localStorage, { mergeDefaults: true });

  function updateStyle(part: keyof StyleConfig, newStyle: TextStyle) {
    styles.value = {
      ...styles.value,
      [part]: newStyle,
    };
  }

  function resetStyles() {
    styles.value = defaultStyles;
  }

  return {
    styles,
    updateStyle,
    resetStyles,
  };
}