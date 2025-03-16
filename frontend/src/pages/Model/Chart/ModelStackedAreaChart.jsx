import {useState} from 'react'
import {
	ComposedChart,
	Line,
	Area,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
} from 'recharts'

const ModelComposedChart = ({data, modelName}) => {
	// ✅ 데이터 변환
	const transformedData = data.map(entry => ({
		key: entry.key,
		actual: entry[`${modelName}_actual`],
		predicted: entry[`${modelName}_predicted`],
	}))

	return (
		<ResponsiveContainer width="100%" height={500}>
			<ComposedChart
				data={transformedData}
				margin={{top: 20, right: 20, bottom: 20, left: 20}}
			>
				<CartesianGrid stroke="#f5f5f5"/>
				<XAxis dataKey="key" label={{value: "구간", position: "insideBottom", offset: -10}}/>
				<YAxis/>
				<Tooltip/>
				<Legend wrapperStyle={{paddingTop: 30}}/>

				{/* ✅ 실제값 (채워진 영역) */}
				<Area
					type="number"
					dataKey="actual"
					fill="#A1E3F9"
					stroke="#A1E3F9"
					fillOpacity={0.5}
					name={`실제값`}
					
				/>

				{/* ✅ 예측값 (선 그래프) */}
				<Line
					type="number"
					dataKey="predicted"
					stroke="#F96E2A"
					strokeWidth={2}
					dot={{r: 3}}
					name={`예측값`}
				/>

			</ComposedChart>
		</ResponsiveContainer>
	)
}

export default ModelComposedChart