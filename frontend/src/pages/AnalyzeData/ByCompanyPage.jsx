import {useState} from "react"
import axios from "axios"
import SearchBar from "../../components/Search-bar"
import NavBar from "../../components/Nav-bar"
import {BID_COLUMNS, COMPANY_COLUMNS, NOTICE_COLUMNS} from "../../components/Table/Columns.jsx"
import MyAgGridTable from "../../components/Table/MyAgGridTable.jsx"
import HistogramChart from "../../components/Chart/Histogram"
import PieChartExample from "../../components/Chart/PieChart.jsx"

const selectedColumns = ["공고번호", "공고제목", "투찰금액", "순위", "기초대비사정률", "예가범위", "비고"]

// 모든 컬럼 배열을 합칩니다.
const allColumns = [...NOTICE_COLUMNS, ...COMPANY_COLUMNS, ...BID_COLUMNS]

// 선택한 필드에 해당하는 컬럼만 필터링
const filteredColumns = allColumns.filter((col) => selectedColumns.includes(col.field))

function ByCompanyPage() {
	const dropdownOptions = ["사업자등록번호", "업체명"]
	// 검색 조건 및 결과 데이터를 상태로 관리
	const [tableData, setTableData] = useState([])

	// 부모에서 gridOptions 객체를 생성 (필요한 옵션 추가)
	const gridOptions = {
		pagination: true,
		paginationPageSize: 500,
		defaultColDef: {
			resizable: true,
			sortable: true,
			filter: true,
			floatingFilter: false,
			filterParams: {
				buttons: ["apply", "reset"],
				closeOnApply: true,
			},
			minWidth: 100,
			flex: true,
		},
	}

	// SearchBar에서 onSearch 호출 시 동작하는 함수
	function handleOnSearch({selectedOption, queryValue}) {
		// URLSearchParams로 파라미터 인코딩
		const params = new URLSearchParams({
			option: selectedOption, // 예: "사업자등록번호"
			query: queryValue, // 예: "2048626080"
			selectedColumns: selectedColumns.join(",")
		})

		// 백엔드 엔드포인트 URL (필요한 경우 baseURL과 결합)
		const url = `http://127.0.0.1:8000/api/by-company/?${params.toString()}`

		axios
			.get(url)
			.then((response) => {
				// 테이블 렌더링 용
				setTableData(response.data)
			})
			.catch((error) => {
				console.error("검색 에러:", error)
			})
	}

	return (
		<div className="app-container mt-20 flex justify-center">
			<NavBar/>
			<div className="main-content flex flex-col w-full">
				<h1 className="self-start text-3xl font-semibold mb-10">업체별 분석</h1>

				<div className="self-center w-full">
					<SearchBar dropdownOptions={dropdownOptions} onSearch={handleOnSearch}/>
				</div>
				<div className="result flex flex-row justify-center mt-15">
					<div className="ag-grid-table w-[50%]">
						<MyAgGridTable
							gridOptions={gridOptions}
							columns={filteredColumns}
							tableData={tableData}
							tableStyle={{width: "100%", height: "500px"}}
						/>
					</div>
					<div className="chart w-[50%]">
						<HistogramChart data={tableData} width="100%" height={400}/>
						<PieChartExample data={tableData} width="100%" height={400}/>
					</div>
				</div>
			</div>
		</div>
	)
}

export default ByCompanyPage
