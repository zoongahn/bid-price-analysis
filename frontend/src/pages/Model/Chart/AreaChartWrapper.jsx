import {useState} from "react"
import ModelStackedAreaChart from "./ModelStackedAreaChart.jsx"
import SelectSectionNum from "./components/SelectSectionNum.jsx"
import SelectModel from "./components/SelectModel.jsx"

export default function AreaChartWrapper() {
	let sampleData = {}
	const rangeList = [10, 20, 50, 100]

	const modelNameList = ["모델A", "모델B", "모델C", "모델D", "모델E", "모델F", "모델G", "모델H", "모델I"]

	const [sectionNum, setSectionNum] = useState(20)
	const [selectedModel, setSelectedModel] = useState(modelNameList[0])


	rangeList.forEach((range) => {
		sampleData[range] = Array.from({length: range}, (_, i) => {
			let entry = {key: i + 1}

			modelNameList.forEach((model) => {
				const actual = Math.floor(Math.random() * 100) // 실제값 (0~100)
				const variation = actual * 0.3 // 10% 범위
				const predicted = Math.floor(actual + (Math.random() * 2 - 1) * variation) // 실제값 ±10% 내 랜덤값

				entry[`${model}_actual`] = actual
				entry[`${model}_predicted`] = predicted
			})
			return entry
		})
	})

	return (
		<div className="px-2">
			<div className="flex justify-end">
				<SelectSectionNum sectionNum={sectionNum} setSectionNum={setSectionNum}/>
				<SelectModel selectedModel={selectedModel} setSelectedModel={setSelectedModel}
							 modelNameList={modelNameList}/>
			</div>
			<ModelStackedAreaChart data={sampleData[sectionNum]} modelName={selectedModel}/>
		</div>
	)
}