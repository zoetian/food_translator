import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // GitHub Pages serves this project at https://<user>.github.io/food_translator/,
  // so the built assets need that base path. Leave dev server at the root.
  base: command === 'build' ? '/food_translator/' : '/',
  plugins: [react()],
}))
