import React from "react"
import {Link} from "react-router-dom"
import NavBar from "../../components/Nav-bar/Nav-bar"
import "../../assets/BasePage.css"


const MainPage = () => {
	return (
		<div className="app-container">
			<NavBar/>
			<main className="main-content">
				<h1>메인 페이지</h1>
				<p>
					데이터 분석 대시보드에 오신 것을 환영합니다. 이곳에서는 다양한 데이터 시각화와 분석 결과를 확인할 수 있습니다.
				</p>
			</main>
		</div>
	)
}

export default MainPage