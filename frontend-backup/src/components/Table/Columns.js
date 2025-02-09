export const NOTICE_COLUMNS = [
	{headerName: "공고번호", field: "공고번호", width: 150},
	{headerName: "입찰년도", field: "입찰년도", width: 50},
	{headerName: "공고제목", field: "공고제목", width: 500},
	{headerName: "발주처", field: "발주처", width: 150},
	{headerName: "지역제한", field: "지역제한", width: 100},
	{
		headerName: "기초금액",
		field: "기초금액",
		width: 120,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{
		headerName: "예정가격",
		field: "예정가격",
		width: 120,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{headerName: "예가범위", field: "예가범위", width: 120},
	{
		headerName: "A값",
		field: "A값",
		width: 100,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{
		headerName: "투찰률",
		field: "투찰률",
		width: 100,
		valueFormatter: (params) => (params.value ? `${params.value.toFixed(3)}%` : ""),
	},
	{
		headerName: "참여업체수",
		field: "참여업체수",
		width: 100,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{headerName: "공고구분표시", field: "공고구분표시", width: 100},
	{
		headerName: "정답사정률",
		field: "정답사정률",
		width: 100,
		valueFormatter: (params) => (params.value ? params.value.toFixed(5) : ""),
	},
]

export const COMPANY_COLUMNS = [
	{headerName: "사업자등록번호", field: "사업자등록번호", width: 150},
	{headerName: "업체명", field: "업체명", width: 200},
	{headerName: "대표명", field: "대표명", width: 150},
	{
		headerName: "투찰횟수",
		field: "투찰횟수",
		width: 150,
		valueFormatter: (params) => (params.value != null ? params.value.toLocaleString() : ""),
	},
]

// (참조: ForeignKey로 연결된 Notice와 Company의 일부 필드를 같이 보여줄 수도 있음)
export const BID_COLUMNS = [
	{headerName: "순위", field: "순위", width: 80},
	{
		headerName: "투찰금액",
		field: "투찰금액",
		width: 120,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{
		headerName: "가격점수",
		field: "가격점수",
		width: 100,
		valueFormatter: (params) => (params.value ? params.value.toLocaleString() : ""),
	},
	{
		headerName: "예가대비투찰률",
		field: "예가대비투찰률",
		width: 120,
		valueFormatter: (params) => (params.value ? `${params.value.toFixed(2)}%` : ""),
	},
	{
		headerName: "기초대비투찰률",
		field: "기초대비투찰률",
		width: 120,
		valueFormatter: (params) => (params.value ? `${params.value.toFixed(2)}%` : ""),
	},
	{
		headerName: "기초대비사정률",
		field: "기초대비사정률",
		width: 120,
		valueFormatter: (params) => (params.value ? `${params.value.toFixed(2)}%` : ""),
	},
	{headerName: "추첨번호", field: "추첨번호", width: 100},
	{
		headerName: "낙찰여부",
		field: "낙찰여부",
		width: 80,
		cellRenderer: (params) => (params.value ? "Yes" : "No"),
	},
	{
		headerName: "투찰일시",
		field: "투찰일시",
		width: 150,
		valueFormatter: (params) => (params.value ? new Date(params.value).toLocaleString() : ""),
	},
	{headerName: "비고", field: "비고", width: 150},
	// (선택사항) 관련된 Notice와 Company 정보 표시
	{headerName: "공고번호", field: "notice.공고번호", width: 150},
	{headerName: "업체명", field: "company.업체명", width: 150},
]
