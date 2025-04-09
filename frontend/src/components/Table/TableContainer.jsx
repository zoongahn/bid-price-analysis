import MyAgGridTable from "./MyAgGridTable"
import {useCallback, useRef} from "react"
import ServerAgGridTable from "./ServerAgGridTable.jsx"
import MyReactTable from "./MyReactTable.jsx"

// CSV 내보내기 함수

export default function TableContainer({columns, tableData, server = false}) {
	const gridRef = useRef(null)

	const onBtnExport = useCallback(() => {
		gridRef.current.exportDataAsCsv()
	}, [])

	return (
		<div className="table-container flex flex-col">
			<div className="top-info mt-10 flex flex-row justify-between pl-10">
				<ul className="mb-2">
					<li className="list-disc text-lg items-center">
						<kbd>⇧ Shift</kbd>를 누른 채로 헤더를 클릭하여 다중정렬을 사용할 수 있습니다.
					</li>
				</ul>
				<button
					className="export-button bg-sky-300 px-5 py-2 my-2 self-end cursor-pointer rounded-xl"
					onClick={onBtnExport}
				>
					CSV파일 다운로드
				</button>
			</div>
			{server ? (
				<ServerAgGridTable columns={columns} tableData={tableData}/>
			) : (
				<MyReactTable columns={columns} tableData={tableData}/>
			)}
		</div>
	)
}
