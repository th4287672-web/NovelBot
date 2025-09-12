<script lang="ts">
import { h, defineComponent, defineAsyncComponent, type VNode, type Component } from 'vue';
import { useSettingsStore } from '~/stores/settings';

// [FIX] 关键修复：导入自身的新文件名 .client.vue 以实现递归
import ContentRenderer from './ContentRenderer.client.vue';

interface ParsedNode {
  type: 'tag' | 'text';
  tag?: string;
  props?: Record<string, any>;
  children?: (ParsedNode | string)[];
  text?: string;
}

export default defineComponent({
  name: 'ContentRenderer',
  props: {
    content: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const settingsStore = useSettingsStore();

    const componentsMap: Record<string, Component> = {
      Foldable: defineAsyncComponent(() => import('./renderers/Foldable.vue')),
      StoryOption: defineAsyncComponent(() => import('./renderers/StoryOption.vue')),
      Highlight: defineAsyncComponent(() => import('./renderers/Highlight.vue')),
      Spoiler: defineAsyncComponent(() => import('./renderers/Spoiler.vue')),
      Table: defineAsyncComponent(() => import('./renderers/Table.vue')),
      ProgressBar: defineAsyncComponent(() => import('./renderers/ProgressBar.vue')),
      Map: defineAsyncComponent(() => import('./renderers/Map.vue')),
      Card: defineAsyncComponent(() => import('./renderers/Card.vue')),
      DiceRoll: defineAsyncComponent(() => import('./renderers/DiceRoll.vue')),
      ECharts: defineAsyncComponent(() => import('./renderers/ECharts.vue')),
      FloorPlan: defineAsyncComponent(() => import('./renderers/FloorPlan.vue')),
    };

    const allowedHtmlTags = new Set([
      'span', 'div', 'p', 'b', 'i', 'strong', 'em', 'code', 'pre', 'blockquote',
      'br', 'hr', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'table', 'thead', 'tbody', 'tr', 'th', 'td', 'u', 's', 'sub', 'sup',
    ]);

    function parseHTML(html: string): (ParsedNode | string)[] {
      const results: (ParsedNode | string)[] = [];
      const tagRegex = /<([A-Za-z][a-zA-Z0-9]*)\s*([^>]*?)>([\s\S]*?)<\/\1>/g;
      let lastIndex = 0;
      let match;

      while ((match = tagRegex.exec(html)) !== null) {
        const [fullMatch, tagName, attrsStr, innerContent] = match;
        if (match.index > lastIndex) {
          results.push(html.substring(lastIndex, match.index));
        }
        
        const props: Record<string, any> = {};
        if (attrsStr) {
            // [核心修复] 将 (\w+) 修改为 ([\w-]+) 以支持带连字符的属性名
            const attrRegex = /([\w-]+)=['"]([^'"]*)['"]/g;
            let attrMatch;
            while ((attrMatch = attrRegex.exec(attrsStr)) !== null) {
                if (attrMatch[1] && attrMatch[2] !== undefined) {
                    const tempEl = document.createElement('textarea');
                    tempEl.innerHTML = attrMatch[2];
                    props[attrMatch[1]] = tempEl.value;
                }
            }
        }

        results.push({
          type: 'tag',
          tag: tagName,
          props: props,
          children: parseHTML(innerContent || ''),
        });
        lastIndex = match.index + fullMatch.length;
      }
      if (lastIndex < html.length) {
        results.push(html.substring(lastIndex));
      }
      return results;
    }
    
    function renderNode(node: ParsedNode | string): VNode | string {
      if (typeof node === 'string') return node;
      if (node.type === 'text') return node.text || '';

      if (node.type === 'tag' && node.tag) {
        let component: string | Component | undefined = undefined;
        
        if (componentsMap[node.tag]) {
          component = componentsMap[node.tag];
        } else if (allowedHtmlTags.has(node.tag.toLowerCase())) {
          component = node.tag.toLowerCase();
        }

        if (component) {
            const finalProps = { ...node.props };
            for (const key in finalProps) {
                if (finalProps[key] === 'undefined') {
                    delete finalProps[key];
                }
            }
            const children = node.children ? node.children.map(renderNode) : [];
            return h(component, finalProps, children);
        } else {
            const innerText = (node.children || []).map(child => typeof child === 'string' ? child : (child.text || '')).join('');
            return `<${node.tag}>${innerText}</${node.tag}>`;
        }
      }
      return '';
    }

    return () => {
      let tempContent = props.content;
      const enabledRules = settingsStore.regexRules.filter(rule => rule.enabled && rule.pattern);
      
      if (enabledRules.length > 0) {
          for (const rule of enabledRules) {
              try {
                  const regex = new RegExp(rule.pattern, 'gs');
                  tempContent = tempContent.replace(regex, rule.template);
              } catch (e) {
                  console.warn(`Invalid regex for rule "${rule.name}":`, e);
              }
          }
      }
      
      const parsedTree = parseHTML(tempContent);
      return h('div', { class: 'whitespace-pre-wrap leading-relaxed' }, parsedTree.map(renderNode));
    };
  }
});
</script>