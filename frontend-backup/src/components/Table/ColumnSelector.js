// ColumnSelector.js (간략화 예시)
import React, {useState, useEffect, useRef} from "react"
import Choices from "choices.js"
import "choices.js/public/assets/styles/choices.css"
import "./ColumnSelector.css" // 스타일 파일 추가

import {ALL_COLUMNS} from "./Columns/NoticesColumns"  // 위에서 정의한 전체 컬럼

const ColumnSelector = ({onApplyColumns}) => {
	// 기본적으로 전체 컬럼 다 선택
	const [selectedFields, setSelectedFields] = useState(
		ALL_COLUMNS.map((col) => col.field)
	)

	const selectRef = useRef(null)
	let choiceInstance = useRef(null)

	useEffect(() => {
		if (selectRef.current) {
			// Choice.js 인스턴스 생성
			choiceInstance.current = new Choices(selectRef.current, {
				removeItemButton: true,
				shouldSort: false,
				duplicateItemsAllowed: false,

				position: "auto"
			})

			// 초기 값 설정
			choiceInstance.current.setChoiceByValue(selectedFields)

			// 값 변경 시 핸들링
			selectRef.current.addEventListener("change", (event) => {
				const values = Array.from(event.target.selectedOptions, (option) => option.value)
				setSelectedFields(values)
			})
		}

		return () => {
			if (choiceInstance.current) {
				choiceInstance.current.destroy()
			}
		}
	}, [])


	const handleApply = () => {
		onApplyColumns(selectedFields)
	}

	return (
		<div className="column-selector-container">
			<h3>표시할 컬럼 선택</h3>
			<div className="choice-submit">
				<div className="choice-wrapper">
					<select ref={selectRef} multiple>
						{ALL_COLUMNS.map((col) => (
							<option key={col.field} value={col.field}>
								{col.title}
							</option>
						))}
					</select>
				</div>
				<button className="apply-btn" onClick={handleApply}>적용</button>
			</div>
		</div>
	)
}

export default ColumnSelector