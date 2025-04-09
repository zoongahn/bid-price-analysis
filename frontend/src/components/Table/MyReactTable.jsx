// src/components/MyReactTable.js
import {
	useReactTable,
	getCoreRowModel,
	getSortedRowModel,
	getPaginationRowModel,
	flexRender,
} from '@tanstack/react-table'
import {useMemo, useState} from 'react'

import {RiSkipLeftLine, RiSkipRightLine} from "react-icons/ri"
import {FaAngleRight, FaAngleLeft} from "react-icons/fa6"
import {FaArrowDown, FaArrowUp} from "react-icons/fa"


export default function MyReactTable({
										 columns,
										 tableData,
										 tableStyle = {width: '100%', height: 'auto'},
									 }) {
	const data = useMemo(() => tableData || [], [tableData])
	const cols = useMemo(() => columns || [], [columns])

	const pageSizeList = [10, 50, 100, 500]

	const [pageSize, setPageSize] = useState(pageSizeList[2])


	const table = useReactTable({
		data,
		columns: cols,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		enableColumnResizing: true,
		initialState: {
			pagination: {
				pageSize: pageSize,
				pageIndex: 0
			}
		},
		manualPagination: false
	})

	const applyColumnWidthStyle = (size) => {
		if (!size) return undefined
		return {
			width: `${size}px`,
			minWidth: `${size}px`,
			maxWidth: `${size}px`,
		}
	}

	return (
		<div className="overflow-x-auto border rounded-md w-full" style={tableStyle}>
			<table className="text-sm text-left border-separate table-fixed">
				<thead className="bg-gray-100 text-gray-800">
				{table.getHeaderGroups().map(headerGroup => (
					<tr key={headerGroup.id}>
						{headerGroup.headers.map(header => (
							<th key={header.id}
								className="px-2 py-2 whitespace-nowrap truncate cursor-pointer"
								style={applyColumnWidthStyle(header.column.columnDef.size)}
								onClick={header.column.getToggleSortingHandler()}  // 클릭 시 정렬 토글
							>
								<div className="flex items-center gap-1">
									{flexRender(header.column.columnDef.header, header.getContext())}

									{/* 정렬 아이콘 표시 */}
									{{
										asc: <FaArrowUp/>,
										desc: <FaArrowDown/>,
									}[header.column.getIsSorted()] ?? null}
								</div>

							</th>
						))}
					</tr>
				))}
				</thead>
				<tbody>
				{table.getPaginationRowModel().rows.map(row => (
					<tr
						key={row.id}
						className="hover:bg-blue-50 border border-b-gray-100 rounded"
					>
						{row.getVisibleCells().map(cell => (
							<td key={cell.id}
								className="px-2 py-1 border border-x-0 border-t-0 border-b-gray-300 whitespace-nowrap overflow-x-auto [&::-webkit-scrollbar]:hidden"
								style={applyColumnWidthStyle(cell.column.columnDef.size)}

							>
								{flexRender(cell.column.columnDef.cell, cell.getContext())}
							</td>
						))}
					</tr>
				))}
				</tbody>
			</table>
			{/* 페이지네이션 컨트롤 */}
			<div className="flex justify-end items-center gap-4 text-sm border-t py-1 px-4">

				{/* 페이지 크기 선택 */}
				<div className="flex items-center gap-1">
					<span className="text-gray-600 mr-1">Page Size:</span>
					<select
						value={table.getState().pagination.pageSize}
						onChange={(e) => table.setPageSize(Number(e.target.value))}
						className="border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring"
					>
						{pageSizeList.map(size => (
							<option key={size} value={size}>
								{size}
							</option>
						))}
					</select>
				</div>

				{/* 페이지 범위 표시 */}
				<div className="text-gray-700">
					{`${table.getRowModel().rows.length > 0
						? `${table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}`
						: 0
					} to ${Math.min(
						(table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
						table.getPrePaginationRowModel().rows.length
					)} of ${table.getPrePaginationRowModel().rows.length}`}
				</div>

				{/* 페이지 이동 버튼 */}
				<div className="flex items-center gap-2">
					<button
						className=" py-1 rounded disabled:opacity-40"
						onClick={() => table.setPageIndex(0)}
						disabled={!table.getCanPreviousPage()}
					>
						<RiSkipLeftLine className="text-2xl"/>
					</button>
					<button
						className="py-1 rounded disabled:opacity-40"
						onClick={() => table.previousPage()}
						disabled={!table.getCanPreviousPage()}
					>
						<FaAngleLeft className="text-lg"/>
					</button>
					<span className="text-gray-700 mx-1">
						Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
					</span>
					<button
						className="py-1 rounded disabled:opacity-40"
						onClick={() => table.nextPage()}
						disabled={!table.getCanNextPage()}
					>
						<FaAngleRight className="text-lg"/>
					</button>
					<button
						className="py-1 rounded disabled:opacity-40"
						onClick={() => table.setPageIndex(table.getPageCount() - 1)}
						disabled={!table.getCanNextPage()}
					>
						<RiSkipRightLine className="text-2xl"/>
					</button>
				</div>
			</div>
		</div>
	)
}