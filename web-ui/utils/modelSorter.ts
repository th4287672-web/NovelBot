import type { ModelDetails } from '~/types/api';

interface ModelDefinition {
  name: string;
  displayName: string;
  docsUrl: string;
  series: 'special' | 'gemini' | 'learnlm' | 'gemma' | 'unknown';
  version: number[];
  tier: 'pro' | 'flash' | 'unknown';
  modifiers: Set<string>;
  numericSuffix: number;
}

const geminiBaseUrl = 'https://ai.google.dev/gemini-api/docs/models?hl=zh-cn#';
const gemmaBaseUrl = 'https://ai.google.dev/gemma/docs?hl=zh-cn';

// 权威的模型数据库
const officialModelData: readonly ModelDefinition[] = [
  // Special
  { name: 'models/gemini-2.5-flash-image-preview', displayName: 'Nano Banana', docsUrl: `${geminiBaseUrl}gemini-2.5-flash-image-preview`, series: 'special', version: [2,5], tier: 'flash', modifiers: new Set(['image']), numericSuffix: 0 },

  // Gemini 2.5
  { name: 'models/gemini-2.5-pro-preview-06-05', displayName: 'Gemini 2.5 Pro Preview', docsUrl: `${geminiBaseUrl}gemini-2.5-pro-preview-06-05`, series: 'gemini', version: [2,5], tier: 'pro', modifiers: new Set(['preview']), numericSuffix: 605 },
  { name: 'models/gemini-2.5-pro-preview-05-06', displayName: 'Gemini 2.5 Pro Preview 05-06', docsUrl: `${geminiBaseUrl}gemini-2.5-pro-preview-05-06`, series: 'gemini', version: [2,5], tier: 'pro', modifiers: new Set(['preview']), numericSuffix: 506 },
  { name: 'models/gemini-2.5-pro-preview-03-25', displayName: 'Gemini 2.5 Pro Preview 03-25', docsUrl: `${geminiBaseUrl}gemini-2.5-pro-preview-03-25`, series: 'gemini', version: [2,5], tier: 'pro', modifiers: new Set(['preview']), numericSuffix: 325 },
  { name: 'models/gemini-2.5-pro-preview-tts', displayName: 'Gemini 2.5 Pro Preview TTS', docsUrl: `${geminiBaseUrl}gemini-2.5-pro-preview-tts`, series: 'gemini', version: [2,5], tier: 'pro', modifiers: new Set(['preview', 'tts']), numericSuffix: 0 },
  { name: 'models/gemini-2.5-pro', displayName: 'Gemini 2.5 Pro', docsUrl: `${geminiBaseUrl}gemini-2.5-pro`, series: 'gemini', version: [2,5], tier: 'pro', modifiers: new Set(), numericSuffix: 0 },
  { name: 'models/gemini-2.5-flash-preview-05-20', displayName: 'Gemini 2.5 Flash Preview 05-20', docsUrl: `${geminiBaseUrl}gemini-2.5-flash-preview-05-20`, series: 'gemini', version: [2,5], tier: 'flash', modifiers: new Set(['preview']), numericSuffix: 520 },
  { name: 'models/gemini-2.5-flash-preview-tts', displayName: 'Gemini 2.5 Flash Preview TTS', docsUrl: `${geminiBaseUrl}gemini-2.5-flash-preview-tts`, series: 'gemini', version: [2,5], tier: 'flash', modifiers: new Set(['preview', 'tts']), numericSuffix: 0 },
  { name: 'models/gemini-2.5-flash-lite-preview-06-17', displayName: 'Gemini 2.5 Flash-Lite Preview 06-17', docsUrl: `${geminiBaseUrl}gemini-2.5-flash-lite-preview-06-17`, series: 'gemini', version: [2,5], tier: 'flash', modifiers: new Set(['preview', 'lite']), numericSuffix: 617 },
  { name: 'models/gemini-2.5-flash', displayName: 'Gemini 2.5 Flash', docsUrl: `${geminiBaseUrl}gemini-2.5-flash`, series: 'gemini', version: [2,5], tier: 'flash', modifiers: new Set(), numericSuffix: 0 },
  { name: 'models/gemini-2.5-flash-lite', displayName: 'Gemini 2.5 Flash-Lite', docsUrl: `${geminiBaseUrl}gemini-2.5-flash-lite`, series: 'gemini', version: [2,5], tier: 'flash', modifiers: new Set(['lite']), numericSuffix: 0 },

  // Gemini 2.0
  { name: 'models/gemini-2.0-pro-exp-02-05', displayName: 'Gemini 2.0 Pro Experimental 02-05', docsUrl: `${geminiBaseUrl}gemini-2.0-pro-exp-02-05`, series: 'gemini', version: [2,0], tier: 'pro', modifiers: new Set(['exp']), numericSuffix: 205 },
  { name: 'models/gemini-2.0-pro-exp', displayName: 'Gemini 2.0 Pro Experimental', docsUrl: `${geminiBaseUrl}gemini-2.0-pro-exp`, series: 'gemini', version: [2,0], tier: 'pro', modifiers: new Set(['exp']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-exp-image-generation', displayName: 'Gemini 2.0 Flash (Image Generation) Experimental', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-exp-image-generation`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['exp', 'image']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-preview-image-generation', displayName: 'Gemini 2.0 Flash Preview Image Generation', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-preview-image-generation`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['preview', 'image']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-thinking-exp-1219', displayName: 'Gemini 2.0 Flash Thinking Experimental 1219', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-thinking-exp-1219`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['exp', 'thinking']), numericSuffix: 1219 },
  { name: 'models/gemini-2.0-flash-thinking-exp-01-21', displayName: 'Gemini 2.0 Flash Thinking Experimental 01-21', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-thinking-exp-01-21`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['exp', 'thinking']), numericSuffix: 121 },
  { name: 'models/gemini-2.0-flash-thinking-exp', displayName: 'Gemini 2.0 Flash Thinking Experimental', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-thinking-exp`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['exp', 'thinking']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-exp', displayName: 'Gemini 2.0 Flash Experimental', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-exp`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['exp']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-001', displayName: 'Gemini 2.0 Flash 001', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-001`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(), numericSuffix: 1 },
  { name: 'models/gemini-2.0-flash', displayName: 'Gemini 2.0 Flash', docsUrl: `${geminiBaseUrl}gemini-2.0-flash`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-lite-preview-02-05', displayName: 'Gemini 2.0 Flash-Lite Preview 02-05', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-lite-preview-02-05`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['preview', 'lite']), numericSuffix: 205 },
  { name: 'models/gemini-2.0-flash-lite-preview', displayName: 'Gemini 2.0 Flash-Lite Preview', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-lite-preview`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['preview', 'lite']), numericSuffix: 0 },
  { name: 'models/gemini-2.0-flash-lite-001', displayName: 'Gemini 2.0 Flash-Lite 001', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-lite-001`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['lite']), numericSuffix: 1 },
  { name: 'models/gemini-2.0-flash-lite', displayName: 'Gemini 2.0 Flash-Lite', docsUrl: `${geminiBaseUrl}gemini-2.0-flash-lite`, series: 'gemini', version: [2,0], tier: 'flash', modifiers: new Set(['lite']), numericSuffix: 0 },

  // Gemini 1.5
  { name: 'models/gemini-1.5-pro-latest', displayName: 'Gemini 1.5 Pro Latest', docsUrl: `${geminiBaseUrl}gemini-1.5-pro-latest`, series: 'gemini', version: [1,5], tier: 'pro', modifiers: new Set(['latest']), numericSuffix: 0 },
  { name: 'models/gemini-1.5-pro-002', displayName: 'Gemini 1.5 Pro 002', docsUrl: `${geminiBaseUrl}gemini-1.5-pro-002`, series: 'gemini', version: [1,5], tier: 'pro', modifiers: new Set(), numericSuffix: 2 },
  { name: 'models/gemini-1.5-pro', displayName: 'Gemini 1.5 Pro', docsUrl: `${geminiBaseUrl}gemini-1.5-pro`, series: 'gemini', version: [1,5], tier: 'pro', modifiers: new Set(), numericSuffix: 0 },
  { name: 'models/gemini-1.5-flash-latest', displayName: 'Gemini 1.5 Flash Latest', docsUrl: `${geminiBaseUrl}gemini-1.5-flash-latest`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(['latest']), numericSuffix: 0 },
  { name: 'models/gemini-1.5-flash-8b-latest', displayName: 'Gemini 1.5 Flash-8B Latest', docsUrl: `${geminiBaseUrl}gemini-1.5-flash-8b-latest`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(['latest', '8b']), numericSuffix: 0 },
  { name: 'models/gemini-1.5-flash-002', displayName: 'Gemini 1.5 Flash 002', docsUrl: `${geminiBaseUrl}gemini-1.5-flash-002`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(), numericSuffix: 2 },
  { name: 'models/gemini-1.5-flash-8b-001', displayName: 'Gemini 1.5 Flash-8B 001', docsUrl: `${geminiBaseUrl}gemini-1.5-flash-8b-001`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(['8b']), numericSuffix: 1 },
  { name: 'models/gemini-1.5-flash', displayName: 'Gemini 1.5 Flash', docsUrl: `${geminiBaseUrl}gemini-1.5-flash`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(), numericSuffix: 0 },
  { name: 'models/gemini-1.5-flash-8b', displayName: 'Gemini 1.5 Flash-8B', docsUrl: `${geminiBaseUrl}gemini-1.5-flash-8b`, series: 'gemini', version: [1,5], tier: 'flash', modifiers: new Set(['8b']), numericSuffix: 0 },

  // Other Gemini
  { name: 'models/gemini-exp-1206', displayName: 'Gemini Experimental 1206', docsUrl: `${geminiBaseUrl}gemini-exp-1206`, series: 'gemini', version: [0,0], tier: 'unknown', modifiers: new Set(['exp']), numericSuffix: 1206 },
  
  // LearnLM
  { name: 'models/learnlm-2.0-flash-experimental', displayName: 'LearnLM 2.0 Flash Experimental', docsUrl: geminiBaseUrl, series: 'learnlm', version: [2,0], tier: 'flash', modifiers: new Set(['exp']), numericSuffix: 0 },

  // Gemma
  { name: 'models/gemma-3-27b-it', displayName: 'Gemma 3 27B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 27 },
  { name: 'models/gemma-3-12b-it', displayName: 'Gemma 3 12B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 12 },
  { name: 'models/gemma-3n-e4b-it', displayName: 'Gemma 3n E4B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 4 },
  { name: 'models/gemma-3-4b-it', displayName: 'Gemma 3 4B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 4 },
  { name: 'models/gemma-3n-e2b-it', displayName: 'Gemma 3n E2B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 2 },
  { name: 'models/gemma-3-1b-it', displayName: 'Gemma 3 1B', docsUrl: gemmaBaseUrl, series: 'gemma', version: [3,0], tier: 'unknown', modifiers: new Set(['it']), numericSuffix: 1 },
];

const seriesOrder = ['special', 'gemini', 'learnlm', 'gemma', 'unknown'];
const tierOrder = ['pro', 'flash', 'unknown'];

export type EnrichedModel = ModelDetails & Omit<ModelDefinition, 'name' | 'displayName' | 'description'>;

export function sortModels(models: ModelDetails[]): EnrichedModel[] {
  const enhancedModels = models.map(backendModel => {
    const officialData = officialModelData.find(m => m.name === backendModel.name);
    if (officialData) {
      return {
        ...backendModel,
        display_name: officialData.displayName, 
        docsUrl: officialData.docsUrl,
        series: officialData.series,
        version: officialData.version,
        tier: officialData.tier,
        modifiers: officialData.modifiers,
        numericSuffix: officialData.numericSuffix,
      };
    }
    return {
      ...backendModel,
      display_name: backendModel.display_name,
      docsUrl: `${geminiBaseUrl}${backendModel.name.replace('models/', '')}`,
      series: 'unknown' as const,
      version: [0,0],
      tier: 'unknown' as const,
      modifiers: new Set<string>(),
      numericSuffix: 0,
    };
  });

  enhancedModels.sort((a, b) => {
    const seriesIndexA = seriesOrder.indexOf(a.series);
    const seriesIndexB = seriesOrder.indexOf(b.series);
    if (seriesIndexA !== seriesIndexB) return seriesIndexA - seriesIndexB;

    const versionLength = Math.max(a.version.length, b.version.length);
    for (let i = 0; i < versionLength; i++) {
        const vA = a.version[i] ?? 0;
        const vB = b.version[i] ?? 0;
        if (vB !== vA) return vB - vA;
    }

    const tierIndexA = tierOrder.indexOf(a.tier);
    const tierIndexB = tierOrder.indexOf(b.tier);
    if (tierIndexA !== tierIndexB) return tierIndexA - tierIndexB;

    const aIsPreview = a.modifiers.has('preview') || a.modifiers.has('exp');
    const bIsPreview = b.modifiers.has('preview') || b.modifiers.has('exp');
    if (aIsPreview !== bIsPreview) return bIsPreview ? 1 : -1;

    const aIsLatest = a.modifiers.has('latest');
    const bIsLatest = b.modifiers.has('latest');
    if (aIsLatest !== bIsLatest) return bIsLatest ? 1 : -1;

    if (b.numericSuffix !== a.numericSuffix) return b.numericSuffix - a.numericSuffix;

    const aIsLite = a.modifiers.has('lite');
    const bIsLite = b.modifiers.has('lite');
    if (aIsLite !== bIsLite) return aIsLite ? 1 : -1;

    return a.display_name.localeCompare(b.display_name);
  });

  return enhancedModels;
}