// NoticesPage.js
import React, {useEffect, useState} from "react"
import axios from "axios"
import MyAgGridTable from "../../components/Table/MyAgGridTable"
import {BID_COLUMNS, COMPANY_COLUMNS} from "../../components/Table/Columns"
import NavBar from "../../components/Nav-bar/Nav-bar"
import "../../assets/BasePage.css"

function BidsPage() {
	const [tableData, setTableData] = useState([])

	useEffect(() => {
		fetchData()
	}, [])

	const fetchData = async () => {
		try {
			// DRF: 공고번호, 입찰년도, 공고제목, 발주처 칼럼
			const url = "http://127.0.0.1:8000/api/bids/?page=1&page_size=10000"
			const res = await axios.get(url)
			// DRF 페이지 => { count, next, previous, results: [...] }
			setTableData(res.data || [])
		} catch (err) {
			console.error("fetchData error:", err)
		}
	}

	return (
		<div className="app-container">
			<NavBar />
			<div className="main-content">
				<h1 className="page-title">투찰 데이터 조회</h1>
				<MyAgGridTable columns={BID_COLUMNS} tableData={tableData} />
			</div>
		</div>
	)
}

export default BidsPage
