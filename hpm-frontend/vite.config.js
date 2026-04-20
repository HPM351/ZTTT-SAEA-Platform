import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  server: {
    host: '0.0.0.0', // ✨ 新增：暴露局域网 IP
    port: 5173,
    proxy: {
      // 保持你原有的配置不变
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '/ws': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      }
    }
  },

  build: {
    // 构建产物输出到后端目录下的 dist 文件夹，方便 main.py 直接读取
    outDir: '../dist', 
    emptyOutDir: true 
  }
})