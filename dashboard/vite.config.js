import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base ('./') so the built site works under a GitHub Pages
// project path like https://<user>.github.io/<repo>/ without hardcoding
// the repository name.
// https://vite.dev/config/
const API_TARGET = 'http://localhost:8080'

// Same-origin /api, so the browser never needs CORS.
//
// The browser still stamps its own Origin on the request, and the proxy forwards
// it verbatim. Behind a tunnel that origin is a public hostname the backend has
// never heard of, so Spring's CORS filter rejects it with "Invalid CORS request"
// -- even though the browser considers the call same-origin. Rewriting Origin to
// the target keeps the backend's allow-list about real deployments rather than
// whatever hostname a tunnel happens to hand out.
const proxy = {
  '/api': {
    target: API_TARGET,
    changeOrigin: true,
    configure: (proxyServer) => {
      proxyServer.on('proxyReq', (proxyReq) => {
        proxyReq.setHeader('origin', API_TARGET)
      })
    },
  },
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
