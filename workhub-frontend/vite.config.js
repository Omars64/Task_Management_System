import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,   // important: bind to 0.0.0.0 inside Docker
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://workhub-backend:5000', // 👈 backend container name from docker-compose
        changeOrigin: true
      }
    }
  }
})
