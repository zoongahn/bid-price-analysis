// tailwind.config.js
module.exports = {
	theme: {
		extend: {
			maxWidth: {
				"3xl": "1920px", // 기존 2xl(1536px)보다 큰 값을 추가
				"4xl": "2560px", // 예시로 더 큰 값 추가 가능
			},
		},
		// container 옵션을 커스터마이징할 경우:
		container: {
			center: true,
			padding: "1rem",
			screens: {
				// 여기에 원하는 커스텀 최대 너비를 지정할 수 있습니다.
				sm: "640px",
				md: "768px",
				lg: "1024px",
				xl: "1280px",
				"2xl": "1536px",
				"3xl": "1920px", // 추가한 값
			},
		},
	},
	plugins: [],
}
