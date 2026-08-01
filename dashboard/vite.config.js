import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base ('./') so the built site works under a GitHub Pages
// project path like https://<user>.github.io/<repo>/ without hardcoding
// the repository name.
// https://vite.dev/config/
// Same-origin /api, so the browser never needs CORS and the built app can be
// served from the backend unchanged.
const proxy = {
  '/api': { target: 'http://localhost:8080', changeOrigin: true },
}

// A Cloudflare quick tunnel arrives with a *.trycloudflare.com Host header,
// which Vite rejects as an unknown host unless it is allowed here.
const allowedHosts = ['.trycloudflare.com']

export default defineConfig({
  base: './',
  plugins: [react()],
  server: { proxy, allowedHosts },
  // `vite preview` serves the production build. Prefer it over the dev server
  // for anything reachable from outside this machine: no HMR socket, no source
  // maps, no dev-only middleware.
  preview: { port: 4173, proxy, allowedHosts },
})
