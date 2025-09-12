/** @type {import('tailwindcss').Config} */
export default {
// 更新后的content配置
content: [
  "./components/**/*.{js,vue,ts}",
  "./layouts/**/*.vue",
  "./pages/**/*.vue",
  "./plugins/**/*.{js,ts}",
  "./app.vue",
  "./error.vue",
  // 移除有风险的全局匹配模式
  // "./**/*.{js,vue,ts}", 
  // "./*.{js,vue,ts}"
  // 改用安全的白名单模式
  "./{composables,utils}/**/*.{js,ts}"
],
  theme: {
    extend: {
      colors: {
        'theme-cyan': 'rgb(6, 182, 212)',
        'theme-purple': 'rgb(139, 92, 246)',
        'theme-yellow': 'rgb(234, 179, 8)',
        'theme-green': 'rgb(16, 185, 129)',
        'theme-gray': 'rgb(156, 163, 175)',
        'theme-indigo': 'rgb(99, 102, 241)'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    // 安全插件：防止生成过大CSS
    function({ addBase }) {
      addBase({
        'html': { 
          'background-color': 'red !important',
          'height': '100%' 
        },
        'body': { 
          'background-color': 'green !important',
          'height': '100%' 
        },
        '#__nuxt': { 
          'background-color': '#111827 !important',
          'height': '100%' 
        }
      })
    }
  ]
}