import type { Filename } from '~/types/api';

type ModelCategory = 'All' | 'Featured' | 'Gemini' | 'Images' | 'Gemma';

export interface OfficialModelEntry {
  name: Filename;
  display_name: string;
  description: string;
  categories: readonly ModelCategory[];
  isNew?: boolean;
  knowledgeCutoff?: string;
  pricingDetails: readonly string[];
  icon: { type: 'svg', paths: readonly string[], fill?: string, strokeWidth?: number };
}

const gemmaIconPath = 'M11.9961 4.21777C12.2419 4.83171 12.5282 5.42603 12.8584 5.99902C13.4696 7.05965 14.2152 8.02968 15.0928 8.90723C15.9703 9.78478 16.9404 10.5304 18.001 11.1416C18.5766 11.4733 19.1739 11.7583 19.791 12C19.1739 12.2417 18.5766 12.5267 18.001 12.8584C16.9404 13.4696 15.9703 14.2152 15.0928 15.0928C14.2152 15.9703 13.4696 16.9404 12.8584 18.001C12.5267 18.5766 12.2417 19.1739 12 19.791C11.7583 19.1739 11.4733 18.5766 11.1416 18.001C10.5304 16.9404 9.78478 15.9703 8.90723 15.0928C8.02968 14.2152 7.05965 13.4696 5.99902 12.8584C5.42309 12.5265 4.82541 12.2417 4.20801 12C4.82541 11.7583 5.42309 11.4735 5.99902 11.1416C7.05965 10.5304 8.02968 9.78478 8.90723 8.90723C9.78478 8.02968 10.5304 7.05965 11.1416 5.99902C11.4717 5.42614 11.7552 4.83169 11.9961 4.21777Z';
const imageIconPaths = [
  'M4 12.9993C7.5 10.9993 12 10.9993 14 14.9993C14.8461 14.5673 15.7897 14.3618 16.7389 14.4029C17.688 14.444 18.6103 14.7303 19.4159 15.2338C20.2216 15.7373 20.883 16.4409 21.3359 17.276C21.7887 18.1112 22.0175 19.0494 22 19.9993',
  'M5.15 17.89C10.67 16.37 13.8 11 12.15 5.89C11.55 4 11.5 2 13 2C16.22 2 18 7.5 18 10C18 16.5 13.8 22 7.51 22C5.11 22 2 22 2 20C2 18.5 3.14 18.45 5.15 17.89Z'
];

export const officialModelData: readonly OfficialModelEntry[] = [
  {
    name: 'models/gemini-2.5-flash-image-preview',
    display_name: 'Nano Banana',
    description: '(又名 Gemini 2.5 Flash Image) 最先进的图像生成和编辑模型。',
    categories: ['Featured', 'Images', 'Gemini'], isNew: true, knowledgeCutoff: '2025年6月',
    pricingDetails: ['文本 • 输入: $0.30 / 输出: $2.50', '图像 (*每张图片输出) • 输入: $0.30 / 输出: $0.039'],
    icon: { type: 'svg', paths: imageIconPaths }
  },
  {
    name: 'models/gemini-2.5-pro',
    display_name: 'Gemini 2.5 Pro',
    description: '谷歌DeepMind开发的最强大的推理模型，擅长编码和复杂推理任务。',
    categories: ['Featured', 'Gemini'], isNew: false, knowledgeCutoff: '2025年1月',
    pricingDetails: ['<=20万词元 • 输入: $1.25 / 输出: $10.00', '> 20万词元 • 输入: $2.50 / 输出: $15.00'],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/gemini-2.5-flash',
    display_name: 'Gemini 2.5 Flash',
    description: '谷歌DeepMind开发的混合推理模型，拥有100万词元的上下文窗口和思考预算功能。',
    categories: ['Featured', 'Gemini'], isNew: false, knowledgeCutoff: '2025年1月',
    pricingDetails: ['所有上下文长度 • 输入: $0.30 / 输出: $2.50'],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/gemini-2.5-flash-lite',
    display_name: 'Gemini 2.5 Flash-Lite',
    description: '谷歌DeepMind开发的最小且最具成本效益的模型，专为大规模使用而构建。',
    categories: ['Featured', 'Gemini'], isNew: false, knowledgeCutoff: '2025年1月',
    pricingDetails: ['所有上下文长度 • 输入: $0.10 / 输出: $0.40'],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/gemini-2.0-flash',
    display_name: 'Gemini 2.0 Flash',
    description: '谷歌DeepMind开发的最均衡的多模态模型，在所有任务中都表现出色。',
    categories: ['Gemini'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: ['所有上下文长度 • 输入: $0.10 / 输出: $0.40'],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/gemini-2.0-flash-lite',
    display_name: 'Gemini 2.0 Flash-Lite',
    description: '谷歌DeepMind开发的最小且最具成本效益的模型，专为大规模使用而构建。',
    categories: ['Gemini'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: ['所有上下文长度 • 输入: $0.075 / 输出: $0.30'],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/learnlm-2.0-flash-experimental',
    display_name: 'LearnLM 2.0 Flash Experimental',
    description: 'LearnLM 2.0 Flash 实验性模型',
    categories: ['Gemini'], isNew: false, knowledgeCutoff: '未知',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath], fill: 'currentColor' }
  },
  {
    name: 'models/gemma-3n-e2b-it',
    display_name: 'Gemma 3n E2B',
    description: '专为在低资源设备上高效运行而构建的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
  {
    name: 'models/gemma-3n-e4b-it',
    display_name: 'Gemma 3n E4B',
    description: '专为在低资源设备上高效运行而构建的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
  {
    name: 'models/gemma-3-1b-it',
    display_name: 'Gemma 3 1B',
    description: '专为以低延迟处理纯文本任务而构建的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
  {
    name: 'models/gemma-3-4b-it',
    display_name: 'Gemma 3 4B',
    description: '能够以低延迟处理视觉和文本输入的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
  {
    name: 'models/gemma-3-12b-it',
    display_name: 'Gemma 3 12B',
    description: '能够处理视觉和文本输入的复杂任务的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
  {
    name: 'models/gemma-3-27b-it',
    display_name: 'Gemma 3 27B',
    description: '能够处理视觉和文本输入的复杂任务的开放模型。',
    categories: ['Gemma'], isNew: false, knowledgeCutoff: '2024年8月',
    pricingDetails: [],
    icon: { type: 'svg', paths: [gemmaIconPath] }
  },
];