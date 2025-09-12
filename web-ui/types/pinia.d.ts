// types/pinia.d.ts
import type { QueryClient } from '@tanstack/vue-query'
import type { Store } from 'pinia'

/**
 * Pinia 存储扩展 - Vue Query 集成
 */
declare module 'pinia' {
  export interface PiniaCustomProperties {
    /**
     * Vue Query 客户端实例
     * @example
     * const { data } = useQuery({
     *   queryKey: ['todos'],
     *   queryFn: () => store.$queryClient.fetchQuery(...)
     * })
     */
    $queryClient: QueryClient

    /**
     * 安全获取查询客户端
     * @throws 如果未初始化则抛出错误
     */
    getQueryClient(): QueryClient
  }

  export interface DefineStoreOptionsBase<S, Store> {
    /**
     * 自定义查询客户端配置
     */
    queryClient?: QueryClient
  }

  export interface PiniaCustomStateProperties<S> {
    /**
     * 内部使用的查询客户端状态
     * @internal
     */
    _queryClient?: QueryClient
  }
}

/**
 * Nuxt 应用上下文扩展
 */
declare module '#app' {
  interface NuxtApp {
    /**
     * 全局 QueryClient 实例
     */
    $queryClient?: QueryClient
  }
}

/**
 * 全局类型扩展
 */
declare global {
  /**
   * Pinia Store 类型增强
   */
  interface PiniaStore {
    $queryClient: QueryClient
  }

  /**
   * 组合式 API 上下文扩展
   */
  interface ComponentCustomProperties {
    /**
     * 通过 store 访问 QueryClient 的快捷方式
     */
    $queryClient: QueryClient
  }
}

// 确保文件被当作模块处理
export {}