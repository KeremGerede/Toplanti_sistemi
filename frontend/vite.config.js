import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// FastAPI yalnızca 127.0.0.1:8000'de çalışır; CORS yerine geliştirme proxy'si kullanılır.
const backend = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': backend,
      '/diarize': backend,
    },
  },
})
