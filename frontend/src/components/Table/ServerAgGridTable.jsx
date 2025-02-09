/* eslint-disable no-unused-vars */
// src/components/MyAgGridTable.js
import {useEffect, useRef, useState, useCallback} from "react"
import {AgGridReact} from "ag-grid-react"
import {AllCommunityModule, ModuleRegistry, InfiniteRowModelModule} from "ag-grid-community"

// Register all Community features
ModuleRegistry.registerModules([AllCommunityModule, InfiniteRowModelModule])

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL


export default function ServerAgGridTable({columns, tableData}) {
	// columnDefs / rowData를 state로
	const [columnDefs, setColumnDefs] = useState(columns || [])
	const [rowData, setRowData] = useState(tableData || [])

	const gridRef = useRef(null)
	const gridApiRef = useRef(null)
	const gridColumnApiRef = useRef(null)

	const onGridReady = useCallback((params) => {
		// datasource 정의 (Infinite Row Model)
		const pageSize = 500
		const dataSource = {
			// rowCount: undefined이면 전체 로우 수를 동적으로 판단합니다.
			rowCount: undefined,
			getRows: (params) => {
				// 페이지 번호 계산 (1-based)
				const page = Math.floor(params.startRow / pageSize) + 1

				// 가져온 sort 및 filter 모델
				const sortModel = params.sortModel
				const filterModel = params.filterModel

				// URLSearchParams를 사용해 쿼리 스트링 생성
				const queryParams = new URLSearchParams({
					page: page,
					page_size: pageSize,
					sort: JSON.stringify(sortModel),
					filter: JSON.stringify(filterModel),
				})

				console.log("요청 페이지:", page, "정렬 모델:", sortModel, "필터 모델:", filterModel)

				// 실제 API 엔드포인트 URL (백엔드에서 이 쿼리 파라미터들을 처리하도록 구현해야 함)
				fetch(`${API_BASE_URL}/api/bids/?${queryParams.toString()}`)
					.then((response) => response.json())
					.then((data) => {
						// API 응답은 { results: [...], count: <전체 건수> } 형태여야 합니다.
						const rowsThisPage = data.results
						const totalCount = data.count
						params.successCallback(rowsThisPage, totalCount)
						console.log(data)
					})
					.catch((error) => {
						console.error("데이터 불러오기 에러:", error)
						params.failCallback()
					})
			},
		}
		params.api.setGridOption("datasource", dataSource)
		gridRef.current = params.api
	}, [])

	// Grid 옵션 설정
	const gridOptions = {
		columnDefs: columns || [],
		// rowData: tableData || [],
		rowModelType: "infinite",
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

			flex: false,
		},
		pagination: true,
		paginationPageSize: 500, // 페이지당 데이터 개수
		paginationPageSizeSelector: [100, 500, 1000],
		rowHeight: 30,
		onGridReady: onGridReady,
		cacheBlockSize: 500, // block size를 500으로 설정 (페이지 크기와 동일)
		infiniteInitialRowCount: 500, // 초기 로우 수도 500으로 설정하여 block size와 일치
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
		<div className="ag-theme-alpine" style={{width: "100%", height: "1000px"}}>
			<AgGridReact {...gridOptions} />
		</div>
	)
}
