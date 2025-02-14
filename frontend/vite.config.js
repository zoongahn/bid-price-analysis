import {defineConfig} from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// https://vite.dev/config/
export default defineConfig({
    plugins: [react(), tailwindcss()],
    server: {
        host: "0.0.0.0",
        allowedHosts: ['gfcon.ddnsfree.com'] // gfcon.ddnsfree.com 도메인을 허용

    },
})

