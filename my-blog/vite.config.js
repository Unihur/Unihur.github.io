import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 读取 .env / .env.[mode] 中的环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    resolve: {
      alias: {
        // 使用 @ 别名指向 src，与后续的路径引用保持简洁
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    plugins: [
      vue(),
      // Element Plus 按需自动导入（API + 组件），避免全量打包
      AutoImport({
        resolvers: [ElementPlusResolver()]
      }),
      Components({
        resolvers: [ElementPlusResolver()]
      })
    ],
    server: {
      // 开发环境代理：把 /api 转发到真实后端，前端代码全部使用相对路径 /api
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'https://unihur.xyz',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
})
