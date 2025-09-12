// types/vueuse.d.ts
import type { UseFetchOptions } from '@vueuse/core'

declare module '@vueuse/nuxt' {
  interface NuxtApp {
    $useFetch: <T>(url: string, options?: UseFetchOptions) => Promise<T>
  }
}