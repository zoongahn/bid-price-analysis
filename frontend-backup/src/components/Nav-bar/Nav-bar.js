// src/components/Nav-bar/Nav-bar.js
import React from "react"
import {Link} from "react-router-dom"
import "./Nav-bar.css"

const NavBar = () => {
	return (
		<header className="nav-bar">
			<nav>
				<ul className="main-menu">
					<li className="menu-item">
						<Link to="/">홈</Link>
						{/* 홈 메뉴의 서브메뉴 예시 */}
						<ul className="sub-menu">
							<li>
								<Link to="/home/sub1">서브 홈 1</Link>
							</li>
							<li>
								<Link to="/home/sub2">서브 홈 2</Link>
							</li>
						</ul>
					</li>
					<li className="menu-item">
						<Link>원천 데이터 조회</Link>
						<ul className="sub-menu">
							<li>
								<Link to="/origin-data/notices">공고 데이터</Link>
							</li>
							<li>
								<Link to="/origin-data/bids">투찰 데이터</Link>
							</li>
							<li>
								<Link to="/origin-data/companies">기업 데이터</Link>
							</li>
						</ul>
					</li>
					<li className="menu-item">
						<Link to="/analysis">데이터 분석</Link>
						<ul className="sub-menu">
							<li>
								<Link to="/analysis/sub1">서브 분석 1</Link>
							</li>
							<li>
								<Link to="/analysis/sub2">서브 분석 2</Link>
							</li>
						</ul>
					</li>
					<li className="menu-item">
						<Link to="/prediction">데이터 예측</Link>
						<ul className="sub-menu">
							<li>
								<Link to="/prediction/sub1">서브 예측 1</Link>
							</li>
							<li>
								<Link to="/prediction/sub2">서브 예측 2</Link>
							</li>
						</ul>
					</li>
					<li className="menu-item">
						<Link to="/info">추가 정보</Link>
						<ul className="sub-menu">
							<li>
								<Link to="/info/sub1">서브 정보 1</Link>
							</li>
							<li>
								<Link to="/info/sub2">서브 정보 2</Link>
							</li>
						</ul>
					</li>
				</ul>
			</nav>
		</header>
	)
}

export default NavBar
