// NoticesPage.js
import {useEffect, useState} from "react"
import axios from "axios"
import {BID_COLUMNS, COMPANY_COLUMNS} from "../../components/Table/Columns.jsx"
import NavBar from "../../components/Nav-bar.jsx"
import TableContainer from "../../components/Table/TableContainer.jsx"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL


function BidsPage() {
	const [tableData, setTableData] = useState([])

	useEffect(() => {
		fetchData()
	}, [])

	const fetchData = async () => {
		try {
			// DRF: 공고번호, 입찰년도, 공고제목, 발주처 칼럼
			const url = `${API_BASE_URL}/api/bids/?page=1&page_size=1000`
			const res = await axios.get(url)
			// DRF 페이지 => { count, next, previous, results: [...] }
			setTableData(res.data || [])
		} catch (err) {
			console.error("fetchData error:", err)
		}
	}

	return (
		<div className="app-container flex flex-col">
			<NavBar/>
			<div className="main-content mt-20">
				<h1 className="page-title text-3xl font-semibold">투찰 데이터 조회</h1>
				<TableContainer columns={BID_COLUMNS} tableData={tableData} server={true}/>
			</div>
		</div>
	)
}

export default BidsPage
