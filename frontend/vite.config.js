import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    port: 5173,
    // Proxy /api calls to the FastAPI backend during local development.
    // In production (Vercel), VITE_API_BASE_URL is prepended to all API
    // calls inside App.jsx instead — this proxy is dev-only.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },

  build: {
    // Explicit output directory — matches Vercel's default expectation.
    // Vercel automatically serves files from this directory after build.
    outDir: 'dist',
    // Emit a warning (not an error) if a chunk exceeds 800kB.
    // jsPDF + autoTable are large but expected for this project.
    chunkSizeWarningLimit: 800,
  }
})