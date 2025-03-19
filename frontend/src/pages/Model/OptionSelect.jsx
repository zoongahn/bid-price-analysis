import {useEffect, useState} from "react"

export default function OptionSelect({options, maxSelect, onChange}) {
	const [selected, setSelected] = useState(options)
	const allSelected = selected.length === options.length

	const toggleSelection = (option) => {
		let newSelected
		if (selected.includes(option)) {
			newSelected = selected.filter((item) => item !== option)
		} else if (selected.length < maxSelect) {
			newSelected = [...selected, option]
		} else {
			return
		}
		setSelected(newSelected)
	}

	const toggleAll = () => {
		if (allSelected) {
			setSelected([])
		} else {
			setSelected(options.slice(0, maxSelect))
		}
	}

	useEffect(() => {
		onChange(selected)
	}, [selected, onChange])

	return (
		<div className="p-4 max-w-md">
			<h2 className="text-lg font-semibold mb-3">옵션을 선택하세요 ({selected.length}/{maxSelect})</h2>
			<div className="border rounded-lg p-2">
				<label className="flex items-center space-x-2 mb-2">
					<input
						type="checkbox"
						checked={allSelected}
						onChange={toggleAll}
						className="w-6 h-6"
					/>
					<span className="font-semibold text-lg">전체 선택</span>
				</label>
				{options.map((option) => (
					<label key={option} className="flex items-center space-x-2 mb-1">
						<input
							type="checkbox"
							checked={selected.includes(option)}
							onChange={() => toggleSelection(option)}
							className="w-6 h-6"
						/>
						<span className="text-lg">{option}</span>
					</label>
				))}
			</div>
			<div className="mt-4">
				<h3 className="font-semibold">선택된 옵션:</h3>
				<p>{selected.length > 0 ? selected.join(", ") : "없음"}</p>
			</div>
		</div>
	)
}

// 사용 예시
// <OptionSelect options={["옵션1", "옵션2", "옵션3", "옵션4", "옵션5"]} maxSelect={3} />