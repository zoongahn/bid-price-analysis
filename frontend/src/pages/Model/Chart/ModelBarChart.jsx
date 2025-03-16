import {useState} from "react"
import {BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid} from "recharts"
import SelectSectionNum from "./components/SelectSectionNum.jsx"


const colors = {
	모델A: "#8884d8",
	모델B: "#82ca9d",
	모델C: "#ffc658",
	모델D: "#ff7f50",
	모델E: "#6a5acd",
	모델F: "#20b2aa",
	모델G: "#dc143c",
	모델H: "#32cd32",
	모델I: "#ff1493",
}

export default function ModelBarChart({data}) {
	const [numSections, setNumSections] = useState(20) // ✅ 기본 구간 20개
	const [hiddenModels, setHiddenModels] = useState([])


	// ✅ 구간 개수별 동적 설정값 (dx, fontSize, interval 조정)
	const tickSettings = {
		10: {dx: 70, fontSize: 20},
		20: {dx: 35, fontSize: 16},
		50: {dx: 15, fontSize: 12},
		100: {dx: 7, fontSize: 7},
	}

	const currentSettings = tickSettings[numSections] || tickSettings[20]


	// 범례 클릭 이벤트: 모델 숨김/표시
	const handleLegendClick = (e) => {
		const model = e.value
		setHiddenModels((prev) =>
			prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
		)
	}

	return (

		<div className="flex flex-col items-center w-full">
			<SelectSectionNum sectionNum={numSections} setSectionNum={setNumSections}/>
			<div className="flex flex-col items-center w-full">
				{/* ✅ 그래프 제목 */}
				<h2 className="text-2xl font-bold mb-4">&lt;{numSections}개 구간별 {9 - hiddenModels.length}개 모델의 예측 성능
					비교&gt;</h2>
				<ResponsiveContainer width="100%" height={400}>
					<BarChart data={data[numSections]} margin={{top: 20, right: 30, left: 20, bottom: 5}} barGap={0}
							  barCategoryGap={"10%"}>
						<CartesianGrid stroke="#828282" strokeDasharray="0" vertical={true} horizontal={false}/>
						<XAxis
							dataKey="key"
							type="number"
							domain={[0.5, numSections + 0.5]} // X축 범위 설정
							ticks={Array.from({length: numSections}, (_, i) => i + 0.5)} // 경계선 맞추기
							tick={{fontSize: currentSettings.fontSize, dx: currentSettings.dx}}
							tickFormatter={(tick) => `[${tick + 0.5}]`}
							allowDecimals={false}
							interval={0}
							label={{
								value: "구간",
								position: "insideBottom",
								offset: -10,
								"fontSize": 20,
								"fontWeight": "bold"
							}}
						/>
						<YAxis/>
						<Tooltip wrapperStyle={{marginLeft: `${currentSettings.dx}px`}}/>
						<Legend
							onClick={handleLegendClick}
							payload={Object.keys(colors).map((key) => ({
								value: key,
								type: "square",
								id: key,
								color: hiddenModels.includes(key) ? "#ddd" : colors[key], // 숨겨진 모델은 회색 처리
							}))}
							wrapperStyle={{cursor: "pointer", paddingTop: 20}}
						/>

						{/* 숨기지 않은 모델만 렌더링 */}
						{Object.keys(colors)
							.filter((model) => !hiddenModels.includes(model))
							.map((model) => (
								<Bar key={model} dataKey={model} fill={colors[model]}/>
							))}
					</BarChart>
				</ResponsiveContainer>
			</div>
		</div>
	)
}