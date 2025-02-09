import {defineConfig} from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// https://vite.dev/config/
export default defineConfig({
	plugins: [react(), tailwindcss()],
	server: {
		host: "0.0.0.0",
		proxy: {
			"/api": {
				target: "http://192.168.1.100:포트번호", // 백엔드 서버의 실제 주소
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, ""),
			},
		},
	},
})
