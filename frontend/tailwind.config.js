// tailwind.config.js

import scrollbarHide from 'tailwind-scrollbar-hide'

/** @type {import('tailwindcss').Config} */
export default {
	content: [
		'./index.html',
		'./src/**/*.{js,ts,jsx,tsx}'
	],
	theme: {
		extend: {
			// 원하는 설정들...
		}
	},
	plugins: [
		scrollbarHide
	]
}