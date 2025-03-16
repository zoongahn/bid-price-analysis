export default function SelectSectionNum({sectionNum, setSectionNum}) {

	const handleChange = (event) => {
		setSectionNum(Number(event.target.value))
	}

	return (
		<div className="mb-4 text-lg mx-4">
			<label className="mr-2 font-semibold">구간 개수:</label>
			<select
				className="py-2 px-3 border border-gray-300 rounded-md"
				value={sectionNum}
				onChange={handleChange}
			>
				{[10, 20, 50, 100].map((num) => (
					<option key={num} value={num}>{num}개</option>
				))}
			</select>
		</div>
	)
}