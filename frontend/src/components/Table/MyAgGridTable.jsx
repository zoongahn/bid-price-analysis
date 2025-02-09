/* eslint-disable no-unused-vars */
// src/components/MyAgGridTable.js
import {useEffect, useRef, useState} from "react"
import {AgGridReact} from "ag-grid-react"
import {AllCommunityModule, inputStyleUnderlined, ModuleRegistry, themeBalham, themeQuartz} from "ag-grid-community"

// Register all Community features
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * props:
 *  - columns: AG Grid 형식의 columnDefs (배열)
 *    예) [ { headerName:"공고번호", field:"공고번호" }, { headerName:"입찰년도", field:"입찰년도" }, ... ]
 *  - tableData: 실제 행 데이터 배열
 *    예) [ { 공고번호:"2023-1234", 입찰년도:2023, ...}, ... ]
 */

export default function MyAgGridTable({
										  gridOptions: parentGridOptions,
										  columns, tableData, tableStyle = {width: "100%", height: "1000px"}
									  }) {
	// columnDefs / rowData를 state로
	const [columnDefs, setColumnDefs] = useState(columns || [])
	const [rowData, setRowData] = useState(tableData || [])

	const gridRef = useRef(null)
	const gridApiRef = useRef(null)
	const gridColumnApiRef = useRef(null)

	// Grid 옵션 설정
	const defaultGridOptions = {
		columnDefs: columnDefs,
		rowData: rowData,
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

	// 부모 gridOptions와 기본 gridOptions 병합 (부모 옵션 우선)
	const mergedGridOptions = {
		...defaultGridOptions,
		...parentGridOptions,
		// 만약 컬럼 옵션을 별도로 관리한다면 gridOptions로 넘겨받은 columnDefs가 우선됨
		rowData: tableData || [],
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

	return (
		<div className="ag-theme-alpine" style={tableStyle}>
			<AgGridReact {...mergedGridOptions} />
		</div>
	)
}
