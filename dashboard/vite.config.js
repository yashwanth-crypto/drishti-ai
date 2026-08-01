import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base ('./') so the built site works under a GitHub Pages
// project path like https://<user>.github.io/<repo>/ without hardcoding
// the repository name.
// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  // Same-origin /api during development, so the browser never needs CORS and
  // the built app can be served from the backend unchanged.
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
})
