import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import type { Pinia } from 'pinia'

export default defineNuxtPlugin((nuxtApp) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        refetchOnWindowFocus: false,
        retry: 1,
        gcTime: 1000 * 60 * 10
      },
      mutations: {
        retry: 0
      }
    }
  })

  nuxtApp.vueApp.use(VueQueryPlugin, { queryClient })

  const pinia = nuxtApp.$pinia as Pinia | undefined
  if (pinia) {
    pinia.use(() => {
      return { $queryClient: queryClient }
    })
  } else {
    console.warn('[VueQuery] Pinia实例未找到，部分功能可能受限')
  }

  if (process.dev) {
    console.log('[VueQuery] 插件已初始化', {
      hasPinia: !!pinia,
      queryClientConfig: queryClient.getDefaultOptions()
    })
  }

  return {
    provide: {
      queryClient
    }
  }
})