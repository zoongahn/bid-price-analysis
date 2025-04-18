// NoticesPage.js
import {useEffect, useState} from "react"
import axios from "axios"
import MyAgGridTable from "../../components/Table/MyAgGridTable"
import {COMPANY_COLUMNS} from "../../components/Table/Columns"
import NavBar from "../../components/Nav-bar"
import TableContainer from "../../components/Table/TableContainer"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL


function CompaniesPage() {
	const [tableData, setTableData] = useState([])

	useEffect(() => {
		fetchData()
	}, [])

	const fetchData = async () => {
		try {
			// DRF: 공고번호, 입찰년도, 공고제목, 발주처 칼럼
			const url = `${API_BASE_URL}/api/companies/?page=1&page_size=100000`
			const res = await axios.get(url)
			// DRF 페이지 => { count, next, previous, results: [...] }
			setTableData(res.data.results || [])
		} catch (err) {
			console.error("fetchData error:", err)
		}
	}

	return (
		<div className="app-container">
			<NavBar/>
			<div className="main-content mt-20">
				<h1 className="page-title text-3xl font-semibold">기업 데이터 조회</h1>
				<TableContainer columns={COMPANY_COLUMNS} tableData={tableData}/>
			</div>
		</div>
	)
}

export default CompaniesPage
