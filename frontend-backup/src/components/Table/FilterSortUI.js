// src/components/FilterSortUI.js
import React, {useState} from "react"

function FilterSortUI({filterObj, onSubmitFilters, sortObj, onSortChange}) {
	// 로컬에 입력값을 잠시 보관 → "검색" 버튼 클릭 시 onSubmitFilters()
	const [localFilter, setLocalFilter] = useState(filterObj)

	const handleInputChange = (field, val) => {
		setLocalFilter(prev => ({...prev, [field]: val}))
	}

	const handleFilterSubmit = () => {
		onSubmitFilters(localFilter)
	}


	return (
		<div style={{border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem"}}>
			<h4>필터</h4>
			<div>
				<label>공고번호: </label>
				<input
					type="text"
					value={localFilter.공고번호 || ""}
					onChange={(e) => handleInputChange("공고번호", e.target.value)}
					style={{marginRight: "1rem"}}
				/>

				<label>발주처: </label>
				<input
					type="text"
					value={localFilter.발주처 || ""}
					onChange={(e) => handleInputChange("발주처", e.target.value)}
				/>
			</div>
			<button onClick={handleFilterSubmit} style={{marginTop: "0.5rem"}}>검색</button>

			<h4>정렬</h4>
			<div>
				<label style={{marginRight: "0.5rem"}}>정렬 컬럼:</label>
				<select
					value={sortObj.field}
					onChange={(e) => onSortChange(e.target.value, sortObj.dir || "asc")}
					style={{marginRight: "1rem"}}
				>
					<option value="">--선택--</option>
					<option value="공고번호">공고번호</option>
					<option value="기초금액">기초금액</option>
					<option value="입찰년도">입찰년도</option>
					<option value="발주처">발주처</option>
				</select>

				<label style={{marginRight: "0.5rem"}}>정렬 방향:</label>
				<select
					value={sortObj.dir}
					onChange={(e) => onSortChange(sortObj.field, e.target.value)}
				>
					<option value="asc">오름차순</option>
					<option value="desc">내림차순</option>
				</select>
			</div>
		</div>
	)
}

export default FilterSortUI