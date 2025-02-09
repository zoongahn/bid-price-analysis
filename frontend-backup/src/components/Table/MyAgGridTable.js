// src/components/MyAgGridTable.js
import React, {useEffect, useRef, useState, useCallback, useMemo} from "react"
import {AgGridReact} from "ag-grid-react"
import {AllCommunityModule, inputStyleUnderlined, ModuleRegistry, themeBalham, themeQuartz} from "ag-grid-community"
import "./MyAgGridTable.css"

// (옵션) 필요한 css
// import "./MyAgGridTable.css"

// Register all Community features
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * props:
 *  - columns: AG Grid 형식의 columnDefs (배열)
 *    예) [ { headerName:"공고번호", field:"공고번호" }, { headerName:"입찰년도", field:"입찰년도" }, ... ]
 *  - tableData: 실제 행 데이터 배열
 *    예) [ { 공고번호:"2023-1234", 입찰년도:2023, ...}, ... ]
 */
function MyAgGridTable({columns, tableData}) {
	// columnDefs / rowData를 state로
	const [columnDefs, setColumnDefs] = useState(columns || [])
	const [rowData, setRowData] = useState(tableData || [])

	const gridRef = useRef(null)
	const gridApiRef = useRef(null)
	const gridColumnApiRef = useRef(null)

	// Grid 옵션 설정
	const gridOptions = {
		columnDefs: columns || [],
		rowData: tableData || [],
		headerHeight: 40,
		floatingFiltersHeight: 40,
		defaultColDef: {
			resizable: true,
			sortable: true,
			filter: true,
			floatingFilter: true,
			filterParams: {
				buttons: ["apply", "reset"],
				closeOnApply: true,
			},
			minWidth: 100,
			flex: false,
		},
		pagination: true,
		paginationPageSize: 500, // 페이지당 데이터 개수
		paginationPageSizeSelector: [100, 500, 1000],
		rowHeight: 30,
		onGridReady: (params) => {
			gridRef.current = params.api
			gridApiRef.current = params.api
			gridColumnApiRef.current = params.columnApi
		},
	}

	// (A) columns 또는 tableData가 갱신되면 업데이트
	useEffect(() => {
		if (columns) {
			setColumnDefs(columns)
		}
	}, [columns])

	useEffect(() => {
		if (tableData) {
			setRowData(tableData)
		}
	}, [tableData])

	// CSV 내보내기 함수
	const onBtnExport = useCallback(() => {
		gridRef.current.exportDataAsCsv()
	}, [])

	return (
		<div className="ag-grid-table">
			<button className="export-button" onClick={onBtnExport}>
				CSV파일 다운로드
			</button>

			<div className="ag-theme-alpine" style={{width: "100%", height: "600px"}}>
				<AgGridReact {...gridOptions} />
			</div>
		</div>
	)
}

export default MyAgGridTable
