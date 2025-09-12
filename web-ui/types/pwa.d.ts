// types/pwa.d.ts
import type { PwaOptions } from '@vite-pwa/nuxt'
import type { ManifestOptions, VitePWAOptions } from 'vite-plugin-pwa'

/**
 * 扩展 Nuxt 配置类型以支持 PWA
 */
declare module 'nuxt/schema' {
  interface NuxtConfig {
    /**
     * PWA 配置选项
     * @example
     * export default defineNuxtConfig({
     *   pwa: {
     *     registerType: 'autoUpdate',
     *     manifest: {
     *       name: 'MyNovelBot',
     *       short_name: 'NovelBot'
     *     }
     *   }
     * })
     */
    pwa?: PwaOptions | VitePWAOptions
  }
}

/**
 * 扩展 manifest 配置类型
 */
declare module 'vite-plugin-pwa' {
  interface ManifestOptions {
    /**
     * 自定义协议处理
     * @example
     * protocol_handlers: [
     *   {
     *     protocol: 'web+novelbot',
     *     url: '/handle-protocol?url=%s'
     *   }
     * ]
     */
    protocol_handlers?: Array<{
      protocol: string
      url: string
    }>
    
    /**
     * 文件处理配置
     */
    file_handlers?: Array<{
      action: string
      accept: Record<string, string[]>
    }>
  }
}

/**
 * 扩展 NuxtApp 类型以支持 PWA 运行时
 */
declare module '#app' {
  interface NuxtApp {
    /**
     * PWA 更新检查
     * @returns 如果有更新返回 true
     */
    $checkPWAUpdate?(): Promise<boolean>
    
    /**
     * 触发 PWA 更新安装
     */
    $triggerPWAUpdate?(): Promise<void>
  }
}

/**
 * 全局类型扩展
 */
declare global {
  /**
   * Service Worker 注册类型
   */
  interface ServiceWorkerRegistration {
    /**
     * 检查更新 (非标准 API)
     */
    updateViaCache?: 'none' | 'imports' | 'all'
  }
  
  /**
   * BeforeInstallPromptEvent 类型
   */
  interface BeforeInstallPromptEvent extends Event {
    readonly platforms: string[]
    readonly userChoice: Promise<{
      outcome: 'accepted' | 'dismissed'
      platform: string
    }>
    prompt(): Promise<void>
  }
  
  interface Window {
    /**
     * PWA 安装事件
     */
    deferredPWAInstallPrompt?: BeforeInstallPromptEvent
    
    /**
     * 手动触发 PWA 安装
     */
    triggerPWAInstall?(): void
  }
}

// 确保文件被当作模块处理
export {}