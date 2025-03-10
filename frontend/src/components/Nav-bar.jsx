// src/components/Nav-bar/Nav-bar.jsx
import {Link} from "react-router-dom"

const NavBar = () => {
	return (
		<header className="fixed top-0 left-0 w-full bg-blue-700 shadow-lg z-[1000]">
			<nav className="container mx-auto flex justify-center items-center py-4">
				<ul className="flex space-x-8">
					{/* 홈 */}
					<li className="relative group mr-0 px-5 border-r border-white/70">
						<Link to="/" className="text-white hover:text-gray-300">
							홈
						</Link>
					</li>

					{/* API 명세 페이지 */}
					<li className="relative group mr-0 px-5 border-r border-white/70">
						<Link to="/api-info" className="text-white hover:text-gray-300">
							API 정보
						</Link>
					</li>

					{/* 원천 데이터 조회 */}
					<li className="relative group mr-0 px-5 border-r border-white/70">
						<span className="text-white cursor-pointer hover:text-gray-300">원천 데이터 조회</span>
						<ul className="absolute left-0 hidden mt-0 w-40 bg-white shadow-md rounded-md group-hover:block">
							<li>
								<Link
									to="/origin-data/notices"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									공고 데이터
								</Link>
							</li>
							<li>
								<Link
									to="/origin-data/bids"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									투찰 데이터
								</Link>
							</li>
							<li>
								<Link
									to="/origin-data/companies"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									기업 데이터
								</Link>
							</li>
						</ul>
					</li>

					{/* 데이터 분석 */}
					<li className="relative group mr-0 px-5 border-r border-white/70">
						<Link to="/analyze" className="text-white hover:text-gray-300">
							데이터 분석
						</Link>
						<ul className="absolute left-0 hidden mt-0 w-40 bg-white shadow-md rounded-md group-hover:block">
							<li>
								<Link
									to="/analyze/by-notice"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									공고별 분석
								</Link>
							</li>
							<li>
								<Link
									to="/analyze/by-company"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									업체별 분석
								</Link>
							</li>
						</ul>
					</li>

					{/* 데이터 예측 */}
					<li className="relative group mr-0 px-5 border-r border-white/70">
						<Link to="/prediction" className="text-white hover:text-gray-300">
							데이터 예측
						</Link>
						<ul className="absolute left-0 hidden mt-0 w-40 bg-white shadow-md rounded-md group-hover:block">
							<li>
								<Link
									to="/prediction/sub1"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									서브 예측 1
								</Link>
							</li>
							<li>
								<Link
									to="/prediction/sub2"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									서브 예측 2
								</Link>
							</li>
						</ul>
					</li>

					{/* 추가 정보 */}
					<li className="relative group mr-0 px-5 ">
						<Link to="/info" className="text-white hover:text-gray-300">
							추가 정보
						</Link>
						<ul className="absolute left-0 hidden mt-0 w-40 bg-white shadow-md rounded-md group-hover:block">
							<li>
								<Link
									to="/info/sub1"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									서브 정보 1
								</Link>
							</li>
							<li>
								<Link
									to="/info/sub2"
									className="block px-4 py-2 bg-blue-500 text-white hover:bg-blue-700"
								>
									서브 정보 2
								</Link>
							</li>
						</ul>
					</li>
				</ul>
			</nav>
		</header>
	)
}

export default NavBar
