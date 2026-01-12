import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3001,
    proxy: {
      '/api/options': {
        target: 'http://options-api:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/options/, '/api')
      },
      '/api/risk': {
        target: 'http://risk-management:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/risk/, '')
      },
      '/api/prediction': {
        target: 'http://prediction-engine:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/prediction/, '')
      },
      '/api/data-api': {
        target: 'http://data-api:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/data-api/, '')
      }
    }
  }
})
