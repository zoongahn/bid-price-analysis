export default function SelectModel({selectedModel, setSelectedModel, modelNameList}) {

	// ✅ 모델 선택 핸들러
	const handleModelChange = (event) => {
		setSelectedModel(event.target.value)
	}

	return (
		<div className="mb-4 text-lg mx-4">
			<label className="mr-2 font-semibold">모델 선택:</label>
			<select value={selectedModel} onChange={handleModelChange}
					className="py-2 px-3 border border-gray-300 rounded-md"
			>
				{modelNameList.map((model) => (
					<option key={model} value={model}>{model}</option>
				))}
			</select>
		</div>
	)
}