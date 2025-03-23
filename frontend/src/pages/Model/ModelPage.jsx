import {useState} from "react"
import {IoIosArrowDown} from "react-icons/io"


import NavBar from "../../components/Nav-bar.jsx"
import OptionSelect from "./OptionSelect.jsx"
import ModelBarChart from "./Chart/ModelBarChart.jsx"
import ModelIndices from "./ModelIndices.jsx"
import ModelStackedAreaChart from "./Chart/ModelStackedAreaChart.jsx"
import AreaChartWrapper from "./Chart/AreaChartWrapper.jsx"

const modelPage = () => {
	let sampleData = {}
	const rangeList = [10, 20, 50, 100]
	rangeList.forEach(range => {
		sampleData[range] = Array.from({length: range}, (_, i) => ({
			key: i + 1,
			모델A: Math.floor(Math.random() * 100),
			모델B: Math.floor(Math.random() * 100),
			모델C: Math.floor(Math.random() * 100),
			모델D: Math.floor(Math.random() * 100),
			모델E: Math.floor(Math.random() * 100),
			모델F: Math.floor(Math.random() * 100),
			모델G: Math.floor(Math.random() * 100),
			모델H: Math.floor(Math.random() * 100),
			모델I: Math.floor(Math.random() * 100),
		}))
	})

	const options = ["기초금액", "예정가격", "정답사정률", "예가범위", "지역제한"]
	const numericOptions = ["기초금액", "예정가격", "정답사정률"]
	const categoricalOptions = {"예가범위": ["-3% ~ +3%", "-2% ~ +2%", "-5% ~ +5%"], "지역제한": ["서울", "부산", "대구", "광주"]}

	const chartTabs = [
		{name: "구간별 모델 성능 비교", component: <ModelBarChart data={sampleData}/>},
		{name: "예측값 vs 실제값", component: <AreaChartWrapper/>},
		{name: "Test-B", component: <div>{name}</div>},
	]

	const [selected, setSelected] = useState([])
	const [ranges, setRanges] = useState({})
	const [categories, setCategories] = useState(categoricalOptions)
	const [selectedTab, setSelectedTab] = useState(chartTabs[1].name) // ✅ 기본 탭 선택


	const handleSelectionChange = (selectedOptions) => {
		setSelected(selectedOptions)
	}

	const handleRangeChange = (option, value, type) => {
		setRanges((prevRanges) => ({
			...prevRanges,
			[option]: {
				...prevRanges[option],
				[type]: value,
			},
		}))
	}

	const handleCategoryChange = (option, selectedCategories) => {
		setCategories((prevCategories) => ({
			...prevCategories,
			[option]: selectedCategories,
		}))
	}

	const handleSubmitButton = () => {
		console.log("Submitted")
	}

	return (
		<div>
			<NavBar/>
			<div className="mt-30 flex w-full">
				<div className="w-[30%]">
					<OptionSelect options={options} maxSelect={5} onChange={handleSelectionChange}/>
				</div>
				<div className="w-[70%] flex">
					<div className="w-1/2 p-4 border rounded-lg mr-4">
						<h3 className="font-semibold mb-5 text-xl">수치형 범위</h3>
						{selected.filter((option) => numericOptions.includes(option)).map((option) => (
							<div key={option} className="mb-4">
								<h4 className="font-semibold">{option}</h4>
								<div className="flex space-x-2">
									<input
										type="number"
										placeholder="MIN"
										value={ranges[option]?.min || ""}
										onChange={(e) => handleRangeChange(option, e.target.value, "min")}
										className="border p-2 rounded"
									/>
									<span className="text-xl">~</span>
									<input
										type="number"
										placeholder="MAX"
										value={ranges[option]?.max || ""}
										onChange={(e) => handleRangeChange(option, e.target.value, "max")}
										className="border p-2 rounded"
									/>
								</div>
							</div>
						))}
					</div>
					<div className="w-1/2 p-4 border rounded-lg">
						<h3 className="font-semibold mb-5 text-xl">범주형 선택</h3>
						<div className="flex">
							{selected.filter((option) => categoricalOptions[option]).map((option) => (
								<div key={option} className="mx-4 p-4 border-1 border-black/30 rounded-lg">
									<h4 className="font-semibold text-lg">{option}</h4>
									{categoricalOptions[option].map((category) => (
										<label key={category}
											   className="flex items-center space-x-2 py-0.5 px-1 ">
											<input
												type="checkbox"
												checked={categories[option]?.includes(category) || false}
												onChange={(e) => {
													const selectedCats = categories[option] || []
													if (e.target.checked) {
														handleCategoryChange(option, [...selectedCats, category])
													} else {
														handleCategoryChange(option, selectedCats.filter((c) => c !== category))
													}
												}}
												className="w-4 h-4"
											/>
											<span>{category}</span>
										</label>
									))}
								</div>
							))}
						</div>
					</div>
				</div>
			</div>
			<div>
				<div className="relative flex items-center justify-center my-4">
					<div
						className="absolute w-full h-[3px] bg-gradient-to-r from-gray-500 via-transparent to-gray-500"></div>
					<button type="submit"
							className="bg-white px-4 py-2 rounded-full shadow-md hover:bg-gray-100 transition duration-200 z-10 cursor-pointer"
							onClick={handleSubmitButton}
					><IoIosArrowDown
						className="text-5xl"/>
					</button>
				</div>
			</div>
			<nav className="flex space-x-4 border-b border-gray-300 mb-5">
				{chartTabs.map((tab) => (
					<button
						key={tab.name}
						className={`px-4 py-2 rounded-t-lg text-lg font-medium transition-all cursor-pointer ${
							selectedTab === tab.name
								? "bg-sky-100 border-t border-l border-r border-gray-300"
								: "bg-gray-100 hover:bg-gray-200"
						}`}
						onClick={() => setSelectedTab(tab.name)}
					>
						{tab.name}
					</button>
				))}
			</nav>
			<div className="">

				{/* ✅ 선택한 탭에 따라 그래프 변경 */}
				<div className="py-4 border border-gray-300 rounded-lg my-4">
					{chartTabs.find((tab) => tab.name === selectedTab)?.component}
				</div>

				<div className="w-[30%]">
					<ModelIndices mse={0.023} mae={0.012} rmse={0.045} r2={0.89}/>
				</div>
			</div>
		</div>
	)
}

export default modelPage