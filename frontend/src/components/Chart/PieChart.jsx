import {
	PieChart,
	Pie,
	Tooltip,
	Legend,
	ResponsiveContainer,
	Cell
} from "recharts"

// 예가범위를 그룹핑하여 카운트하는 함수
const processPieData = (data) => {
	// "예가범위" 필드에 해당하는 값만 추출
	const counts = {}
	data.forEach(item => {
		const category = item["예가범위"]
		if (category) {
			counts[category] = (counts[category] || 0) + 1
		}
	})

	const allData = Object.keys(counts).map(key => ({
		name: key,
		value: counts[key]
	}))

	const total = allData.reduce((sum, item) => sum + item.value, 0)
	const filtered = []
	let otherTotal = 0

	allData.forEach(item => {
		if (item.value / total < 0.05) {
			otherTotal += item.value
		} else {
			filtered.push(item)
		}
	})
	if (otherTotal > 0) {
		filtered.push({name: "기타", value: otherTotal})
	}

	return filtered
}

const COLORS = [
	"#0088FE", "#00C49F", "#FFBB28", "#FF8042",
	"#AA336A", "#9933FF", "#FF3333", "#33CCFF",
	"#66FF66", "#FF6699", "#CC9933", "#66CCFF"
]

// 파이 내부에 퍼센트를 표시하기 위한 커스텀 라벨 함수
const renderCustomizedLabel = ({cx, cy, midAngle, innerRadius, outerRadius, percent, index}) => {
	const RADIAN = Math.PI / 180
	// 퍼센트 텍스트 위치 계산
	const radius = innerRadius + (outerRadius - innerRadius) * 0.5
	const x = cx + radius * Math.cos(-midAngle * RADIAN)
	const y = cy + radius * Math.sin(-midAngle * RADIAN)

	return (
		<text x={x} y={y} fill={"white"} textAnchor="middle" dominantBaseline="central">
			{`${(percent * 100).toFixed(0)}%`}
		</text>
	)
}


const PieChartExample = ({data, width, height}) => {
	const pieData = processPieData(data)

	return (
		<ResponsiveContainer width={width} height={height}>
			<PieChart>
				<Pie
					data={pieData}
					dataKey="value"
					nameKey="name"
					cx="50%"
					cy="50%"
					outerRadius={120}
					label={renderCustomizedLabel}
					labelLine={false}

				>
					{pieData.map((entry, index) => (
						<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]}/>
					))}
				</Pie>
				<Tooltip/>
				<Legend verticalAlign="bottom" height={36}/>
			</PieChart>
		</ResponsiveContainer>
	)
}

export default PieChartExample