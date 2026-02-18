import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Écoute sur toutes les interfaces (nécessaire pour Docker)
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000', // Backend dans le réseau Docker
        changeOrigin: true,
      },
    },
  },
})
