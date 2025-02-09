import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer
} from "recharts"

// 제공된 데이터를 기반으로 히스토그램 데이터를 생성하는 함수
const processHistogramData = (data, numSubBins = 15) => {
	// "기초대비사정률" 값만 추출 (null이나 NaN은 제외)
	const values = data
		.map(item => item["기초대비사정률"])
		.filter(val => val !== null && !isNaN(val))

	if (values.length === 0) return []

// 구간 생성: 17구간 (첫번째: < -3, 중간 15구간: -3~+3, 마지막: > +3)
	const bins = []

	// 첫 번째 구간: -3 미만
	bins.push({
		bin: "< -3",
		count: 0,
		lowerBound: -Infinity,
		upperBound: -3
	})

	// 중간 15 구간: -3 ~ +3
	const binWidth = (3 - (-3)) / numSubBins // 6/15 = 0.4

	for (let i = 0; i < numSubBins; i++) {
		const lowerBound = -3 + i * binWidth
		const upperBound = lowerBound + binWidth
		bins.push({
			bin: `${lowerBound.toFixed(2)} ~ ${upperBound.toFixed(2)}`,
			count: 0,
			lowerBound,
			upperBound
		})
	}

	// 마지막 구간: +3 초과
	bins.push({
		bin: "> +3",
		count: 0,
		lowerBound: 3,
		upperBound: Infinity
	})


	// 각 값이 어느 구간에 속하는지 계산
	values.forEach(val => {
		if (val < -3) {
			bins[0].count += 1
		} else if (val > 3) {
			bins[bins.length - 1].count += 1
		} else {
			// 중간 구간은 bins[1]부터 bins[15]까지 존재함
			const index = Math.floor((val + 3) / binWidth)
			// index는 0~14이므로 bins[index+1]
			bins[index + 1].count += 1
		}
	})


	return bins
}

// 히스토그램 차트를 그리는 컴포넌트
const HistogramChart = ({data, width, height}) => {
	const histogramData = processHistogramData(data, 15)

	return (
		<ResponsiveContainer width={width} height={height}>

			<BarChart
				data={histogramData}
				margin={{top: 20, right: 30, left: 20, bottom: 30}}
			>
				<CartesianGrid strokeDasharray="3 3"/>
				{/* X축: 구간 범위 */}
				<XAxis
					dataKey="bin"
					angle={-45}
					textAnchor="end"
					interval={0}
					height={60}
					label={{value: "사정률 범위", position: "insideBottom", offset: -5}}
				/>
				{/* Y축: 해당 구간의 투찰횟수 */}
				<YAxis
					label={{value: "투찰횟수", angle: -90, position: "insideLeft"}}
				/>
				<Tooltip/>
				<Legend
					iconSize="13"
					iconType="square"
					verticalAlign="top"
					wrapperStyle={{marginLeft: 250, paddingBottom: 5}}
				/>
				<Bar dataKey="count" fill="#8884d8" name="투찰횟수"/>
			</BarChart>
		</ResponsiveContainer>
	)
}

export default HistogramChart