import { defineNuxtConfig } from 'nuxt/config'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const webUiDir = fileURLToPath(new URL('.', import.meta.url))

export default defineNuxtConfig({
  ssr: false,
  devtools: { enabled: true },
  srcDir: webUiDir,
  rootDir: webUiDir,
  buildDir: resolve(webUiDir, '.nuxt'),

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt',
    '@nuxtjs/i18n',
    '@vite-pwa/nuxt'
  ],

  i18n: {
    locales: ['zh'],
    defaultLocale: 'zh',
  },

  plugins: [
    '~/plugins/vue-query.ts',
    '~/plugins/axios.client.ts',
    '~/plugins/auth.client.ts',
    '~/plugins/logger.client.ts'
  ],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8080',
      wsBase: process.env.NUXT_PUBLIC_WS_BASE || 'ws://localhost:8080',
      appVersion: process.env.npm_package_version || '0.1.0'
    }
  },

  vite: {
    server: {
      fs: {
        strict: true,
        allow: [webUiDir]
      },
    },
    build: {
      sourcemap: process.env.NODE_ENV === 'development',
      minify: 'terser',
      chunkSizeWarningLimit: 2000
    }
  },

  nitro: {
    output: {
      dir: resolve(webUiDir, '.output'),
      publicDir: resolve(webUiDir, '.output/public')
    },
    compatibilityDate: '2025-09-04',
    serveStatic: true,
    devProxy: {
      '/proxy-api': {
        target: 'http://localhost:8080/api',
        changeOrigin: true,
        prependPath: true
      }
    }
  },

  tailwindcss: {
    cssPath: resolve(webUiDir, 'assets/css/main.css'),
    configPath: resolve(webUiDir, 'tailwind.config.js'),
    exposeConfig: false,
  },

  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'MyNovelBot',
      short_name: 'NovelBot',
      theme_color: '#111827',
      background_color: '#111827',
      display: 'standalone',
      scope: '/',
      start_url: '/',
      icons: [
        {
          src: 'icons/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: 'icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico}']
    }
  },

  app: {
    baseURL: '/',
    buildAssetsDir: '/_nuxt/',
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
      title: 'MyNovelBot',
      meta: [
        { name: 'description', content: 'AI角色扮演聊天机器人' },
        { name: 'theme-color', content: '#111827' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'manifest', href: '/manifest.webmanifest' }
      ],
      script: [
        {
          key: 'gtm',
          innerHTML: `if (location.hostname !== 'localhost') { /* GTM脚本 */ }`
        }
      ]
    }
  },

  typescript: {
    strict: true,
    typeCheck: true,
    tsConfig: {
      compilerOptions: {
        types: ['@tanstack/vue-query', '@pinia/nuxt']
      }
    }
  },

  experimental: {
    payloadExtraction: false,
    renderJsonPayloads: true
  }
})