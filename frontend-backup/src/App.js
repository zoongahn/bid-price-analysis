import React from "react"
import {BrowserRouter as Router, Routes, Route} from "react-router-dom"
import MainPage from "./pages/MainPage/MainPage"
import NoticesPage from "./pages/ReferData/NoticesShow"
import CompaniesPage from "./pages/ReferData/CompaniesShow"
import BidsPage from "./pages/ReferData/BidsShow"

function App() {
	return (
		<Router>
			<div className="container mx-auto p-4">
				<Routes>
					<Route path="/" element={<MainPage />} />
					<Route path="/origin-data/notices" element={<NoticesPage />} />
					<Route path="/origin-data/companies" element={<CompaniesPage />} />
					<Route path="/origin-data/bids" element={<BidsPage />} />
				</Routes>
			</div>
		</Router>
	)
}

export default App
