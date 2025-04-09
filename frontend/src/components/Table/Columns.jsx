function dateFormatter(date) {
	const yyyy = date.getFullYear()
	const mm = ("0" + (date.getMonth() + 1)).slice(-2)
	const dd = ("0" + date.getDate()).slice(-2)
	const hh = ("0" + date.getHours()).slice(-2)
	const mi = ("0" + date.getMinutes()).slice(-2)
	const ss = ("0" + date.getSeconds()).slice(-2)
	return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

export const textFilterParams = {
	filterOptions: [
		{
			displayKey: "contains",
			displayName: "포함",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return cellValue.toString().toLowerCase().includes(filterValue.toString().toLowerCase())
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "notContains",
			displayName: "미포함",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return !cellValue.toString().toLowerCase().includes(filterValue.toString().toLowerCase())
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "equals",
			displayName: "일치",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return cellValue.toString().toLowerCase() === filterValue.toString().toLowerCase()
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "notEquals",
			displayName: "불일치",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return cellValue.toString().toLowerCase() !== filterValue.toString().toLowerCase()
			},
			numberOfInputs: 1,
		},
	],
}

export const numberFilterParams = {
	filterOptions: [
		{
			displayKey: "equals",
			displayName: "상등(equal)",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return Number(cellValue) === Number(filterValue)
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "greaterThanOrEqual",
			displayName: "이상",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return Number(cellValue) >= Number(filterValue)
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "lessThanOrEqual",
			displayName: "이하",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return Number(cellValue) <= Number(filterValue)
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "greaterThan",
			displayName: "초과",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return Number(cellValue) > Number(filterValue)
			},
			numberOfInputs: 1,
		},
		{
			displayKey: "lessThan",
			displayName: "미만",
			predicate: ([filterValue], cellValue) => {
				if (cellValue == null || filterValue == null) return false
				return Number(cellValue) < Number(filterValue)
			},
			numberOfInputs: 1,
		},
	],
}

export const NOTICE_COLUMNS = [
	{
		id: "rowNumber",
		header: "#",
		cell: ({row}) => row.index + 1,
		size: 50,
	},
	{
		id: "공고번호",
		accessorKey: "공고번호",
		header: "공고번호",
		size: 150,
	},
	{
		id: "입찰년도",
		accessorKey: "입찰년도",
		header: "입찰년도",
		size: 70,
	},
	{
		id: "공고제목",
		accessorKey: "공고제목",
		header: "공고제목",
		size: 200,
	},
	{
		id: "발주처",
		accessorKey: "발주처",
		header: "발주처",
		size: 150,
		cell: info => (
			<span className="whitespace-nowrap">{info.getValue()}</span>
		),
	},
	{
		id: "지역제한",
		accessorKey: "지역제한",
		header: "지역제한",
		size: 100,
	},
	{
		id: "기초금액",
		accessorKey: "기초금액",
		header: "기초금액",
		size: 120,
		cell: ({getValue}) =>
			<span className="whitespace-nowrap">{getValue() ? Number(getValue()).toLocaleString() : ""}</span>,
	},
	{
		id: "예정가격",
		accessorKey: "예정가격",
		header: "예정가격",
		size: 120,
		cell: ({getValue}) =>
			getValue() ? Number(getValue()).toLocaleString() : "",
	},
	{
		id: "예가범위",
		accessorKey: "예가범위",
		header: "예가범위",
		size: 100,
		cell: info => (
			<span className="whitespace-nowrap">{info.getValue()}</span>
		),
	},
	{
		id: "A값",
		accessorKey: "A값",
		header: "A값",
		size: 120,
		cell: ({getValue}) =>
			getValue() ? Number(getValue()).toLocaleString() : "",
	},
	{
		id: "투찰률",
		accessorKey: "투찰률",
		header: "투찰률",
		size: 80,
		cell: ({getValue}) =>
			getValue() ? `${Number(getValue()).toFixed(3)}%` : "",
	},
	{
		id: "참여업체수",
		accessorKey: "참여업체수",
		header: "참여업체수",
		size: 80,
		cell: ({getValue}) =>
			getValue() ? Number(getValue()).toLocaleString() : "",
	},
	{
		id: "공고구분표시",
		accessorKey: "공고구분표시",
		header: "공고구분표시",
	},
	{
		id: "정답사정률",
		accessorKey: "정답사정률",
		header: "정답사정률",
		cell: ({getValue}) =>
			getValue() ? Number(getValue()).toFixed(5) : "",
	},
]

export const COMPANY_COLUMNS = [
	{headerName: "사업자등록번호", field: "사업자등록번호", width: 150, filterParams: textFilterParams},
	{headerName: "업체명", field: "업체명", width: 200, filterParams: textFilterParams},
	{headerName: "대표명", field: "대표명", width: 150, filterParams: textFilterParams},
	{
		headerName: "투찰횟수",
		field: "투찰횟수",
		width: 150,
		valueFormatter: (params) => (params.value != null ? params.value.toLocaleString() : ""),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
]

export const BID_COLUMNS = [
	{
		headerName: "투찰일시",
		field: "투찰일시",
		width: 200,
		valueFormatter: (params) => (params.value == null ? "" : dateFormatter(new Date(params.value))),
		sort: "desc",
	},

	{headerName: "공고번호", field: "notice.공고번호", width: 150, filterParams: textFilterParams},

	{headerName: "업체명", field: "company.업체명", width: 150, filterParams: textFilterParams},

	{
		headerName: "순위", field: "순위", width: 80, filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{
		headerName: "투찰금액",
		field: "투찰금액",
		width: 120,
		valueFormatter: (params) => (params.value == null ? "" : params.value.toLocaleString()),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{
		headerName: "가격점수",
		field: "가격점수",
		width: 100,
		valueFormatter: (params) => (params.value == null ? "" : params.value.toLocaleString()),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{
		headerName: "예가대비투찰률",
		field: "예가대비투찰률",
		width: 120,
		valueFormatter: (params) => (params.value == null ? "" : `${params.value.toFixed(4)}%`),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{
		headerName: "기초대비투찰률",
		field: "기초대비투찰률",
		width: 120,
		valueFormatter: (params) => (params.value == null ? "" : `${params.value.toFixed(4)}%`),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{
		headerName: "기초대비사정률",
		field: "기초대비사정률",
		width: 120,
		valueFormatter: (params) => (params.value == null ? "" : `${params.value.toFixed(5)}%`),
		filter: "agNumberColumnFilter",
		filterParams: numberFilterParams,
	},
	{headerName: "추첨번호", field: "추첨번호", width: 100, filterParams: textFilterParams},
	{
		headerName: "낙찰여부",
		field: "낙찰여부",
		width: 80,
		cellRenderer: (params) => (params.value ? "O" : "X"),
		filterParams: textFilterParams
	},

	{headerName: "비고", field: "비고", width: 150, filterParams: textFilterParams},
	// (선택사항) 관련된 Notice와 Company 정보 표시
]
