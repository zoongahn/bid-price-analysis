import {useState, useEffect} from "react"
import Select from "react-select"
import NavBar from "../../components/Nav-bar.jsx"
import {ClimbingBoxLoader, ClipLoader} from "react-spinners"


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const API_URL = `${API_BASE_URL}/api/api-info/`
const SAVE_URL = `${API_BASE_URL}/api/api-info/save_selected_fields/`

const ApiInfoPage = () => {
	const [apiData, setApiData] = useState([])
	const [selectedService, setSelectedService] = useState(null)
	const [selectedOperation, setSelectedOperation] = useState(null)
	const [operations, setOperations] = useState([])
	const [fields, setFields] = useState([])
	const [checkedFields, setCheckedFields] = useState({})
	const [isLoading, setIsLoading] = useState(true)
	const [error, setError] = useState(null)


	// 백엔드에서 데이터 불러오기
	useEffect(() => {
		const fetchApiData = async () => {
			try {
				const response = await fetch(API_URL)
				if (!response.ok) throw new Error("데이터 로드 실패")
				const data = await response.json()
				setApiData(data)
			} catch (err) {
				setError(err.message)
			} finally {
				setIsLoading(false)
			}
		}
		fetchApiData()
	}, [])

	const handleServiceChange = (option) => {
		const selected = apiData.find((service) => service.service_name === option.value)
		setSelectedService(selected)
		setFields([])
	}


	// 오퍼레이션 선택 시 필드 설정 (selected_for_use 값을 반영)
	const handleOperationChange = (option) => {
		setSelectedOperation(option.value)
		const newFields = option.value.response_fields || []
		setFields(newFields)

		// 기존 데이터에서 `selected_for_use` 값 가져와 반영
		const defaultCheckedFields = {}
		newFields.slice(5).forEach((field) => {
			defaultCheckedFields[field["항목명(영문)"]] = field.selected_for_use || false
		})
		setCheckedFields(defaultCheckedFields)
	}

	// 체크박스 상태 업데이트
	const handleCheckboxChange = (fieldName) => {
		setCheckedFields((prevChecked) => ({
			...prevChecked,
			[fieldName]: !prevChecked[fieldName], // 현재 상태 반전
		}))
	}

	// 전체 선택 / 해제 기능
	const handleSelectAll = () => {
		const allChecked = Object.values(checkedFields).some((value) => !value) // 하나라도 false가 있으면 전체 선택
		const updatedCheckedFields = {}
		Object.keys(checkedFields).forEach((key) => {
			updatedCheckedFields[key] = allChecked // true/false 반전
		})
		setCheckedFields(updatedCheckedFields)
	}

	// 선택된 필드 데이터를 백엔드로 전송
	const handleSaveToDB = async () => {
		if (!selectedOperation) {
			alert("먼저 오퍼레이션을 선택하세요.")
			return
		}

		const payload = {
			service_name: selectedService.service_name,
			operation_name: selectedOperation["오퍼레이션명(영문)"],
			selected_fields: checkedFields, // { "항목명(영문)": true/false }
		}

		try {
			const response = await fetch(SAVE_URL, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(payload),
			})

			if (!response.ok) throw new Error("데이터 저장 실패")
			alert("✅ 선택한 필드가 성공적으로 저장되었습니다.")
		} catch (err) {
			alert(`❌ 오류 발생: ${err.message}`)
		}
	}

	useEffect(() => {
		if (selectedService) {
			setOperations(selectedService.operations)
			setSelectedOperation(null)
			setFields([])
		}
	}, [selectedService])

	useEffect(() => {
		if (selectedOperation) {
			setFields(selectedOperation.response_fields)
		}
	}, [selectedOperation])


	// if (isLoading) return <div className="p-6 text-lg">⏳ 데이터 로딩 중...</div>
	// if (error) return <div className="p-6 text-red-500">⚠️ 오류 발생: {error}</div>

	return (
		<div>
			<NavBar/>
			{isLoading ?
				<div className="h-screen flex justify-center items-center">
					<ClipLoader color={"#828282"} loading={true} size={100} speedMultiplier={.5}
								className="opacity-50"/>
				</div> :
				<div className="mt-20">
					<h1 className="text-3xl font-bold mb-8">조달청 나라장터 오픈API 필드 탐색기</h1>

					<div className="mb-4 flex items-center">
						<div className="text-lg mr-1 w-30">서비스명</div>
						{/* 서비스 선택 */}
						<Select
							options={apiData.map((service) => ({
								value: service.service_name,
								label: service.service_name,
							}))}
							onChange={handleServiceChange}
							placeholder="서비스 선택"
							className="w-full"
						/>
					</div>

					{/* 오퍼레이션 선택 */}
					{selectedService && (
						<div className="mb-4 flex items-center">
							<div className="text-lg mr-1 w-30">오퍼레이션명</div>
							{/* 서비스 선택 */}
							<Select
								options={operations.map((op) => ({
									value: op,
									label: `${op["오퍼레이션명(국문)"]} (${op["오퍼레이션명(영문)"]})`,
								}))}
								onChange={handleOperationChange}
								placeholder="오퍼레이션 선택"
								className="w-full"
							/>
						</div>
					)}

					<hr className={"w-full mt-15"}/>


					{/* 선택된 오퍼레이션 기본정보 렌더링 */}
					{selectedOperation && (
						<div className="mt-6">
							<h2 className="text-xl font-semibold mb-4">📌 선택된 오퍼레이션 정보</h2>
							<table className="w-full border-collapse border border-gray-400 mb-6">
								<thead className="bg-gray-200">
								<tr>
									<th className="border px-4 py-2">일련번호</th>
									<th className="border px-4 py-2">오퍼레이션명(국문)</th>
									<th className="border px-4 py-2">오퍼레이션명(영문)</th>
									<th className="border px-4 py-2">오퍼레이션 설명</th>
								</tr>
								</thead>
								<tbody>
								<tr className="bg-white">
									<td className="border px-4 py-2">{selectedOperation["일련번호"]}</td>
									<td className="border px-4 py-2">{selectedOperation["오퍼레이션명(국문)"]}</td>
									<td className="border px-4 py-2">{selectedOperation["오퍼레이션명(영문)"]}</td>
									<td className="border px-4 py-2">{selectedOperation["오퍼레이션 설명"]}</td>
								</tr>
								</tbody>
							</table>
						</div>
					)}


					{/* 응답 필드 출력 */}
					{selectedOperation && fields.length > 5 && (
						<div className="mt-4">
							<div className="flex items-center justify-between mb-4">
								<h2 className="text-xl font-semibold">
									📌 {selectedOperation["오퍼레이션명(국문)"]} ({selectedOperation["오퍼레이션명(영문)"]}) - 응답 메시지 정보
								</h2>
								{/* DB 저장 버튼 */}
								{selectedOperation && (
									<button
										onClick={handleSaveToDB}
										className="cursor-pointer px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-700"
									>
										📥 DB 저장
									</button>
								)}
							</div>
							<table className="table-auto w-full border-collapse border border-gray-300">
								<thead>
								<tr className="bg-gray-200">
									<th className="w-10 table-cell border text-center align-middle pt-1.5">
										<input type="checkbox" onChange={handleSelectAll}
											   checked={Object.values(checkedFields).every((val) => val)}
											   className="h-6 w-6"
										/>
									</th>
									<th className="border px-4 py-2">항목명(영문)</th>
									<th className="border w-30 px-4 py-2">항목명(국문)</th>
									<th className="border px-4 py-2">설명</th>
								</tr>
								</thead>
								<tbody>
								{fields.slice(5).map((field, index) => (
									<tr key={index} className="border-b">
										<td className="w-10 table-cell border text-center align-middle pt-1.5">
											<input
												type="checkbox"
												checked={checkedFields[field["항목명(영문)"]] || false}
												onChange={() => handleCheckboxChange(field["항목명(영문)"])}
												className="h-6 w-6"
											/>
										</td>
										<td className="border px-4 py-2">{field["항목명(영문)"]}</td>
										<td className="border w-30 px-4 py-2">{field["항목명(국문)"]}</td>
										<td className="border px-4 py-2">{field["항목설명"]}</td>
									</tr>
								))}
								</tbody>
							</table>
						</div>
					)}
					{/* 체크된 필드 상태 출력 (디버깅용) */}
					{Object.keys(checkedFields).length > 0 && (
						<div className="mt-4 p-4 bg-gray-100 border border-gray-300">
							<h3 className="font-semibold">✅ 선택된 필드:</h3>
							<pre className="text-sm">{JSON.stringify(checkedFields, null, 2)}</pre>
						</div>
					)}
				</div>
			}
		</div>
	)
}

export default ApiInfoPage