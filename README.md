BID-PRICE-ANALYSIS/
├── api-fetcher/ # API 수집기 (데이터 수집 및 요청 처리)
    ├── .env # 환경 변수 설정 파일
    ├── .gitignore
    ├── requirements.txt # 패키지 의존성
    ├── setup.py # 패키지 설치 정보
    ├── api_info/                       # 오픈 API 메타 정보 모듈
    │   ├── operation_fields/               # API 응답 필드 정의 (정리용 데이터)
    │   │   ├── raw/                        # 원본 필드 정의
    │   │   ├── processed/                  # 전처리된 필드 정의
    │   │   ├── api_operation_lists.csv
    │   │   ├── api_operation_lists.json
    │   │   └── api_operation_lists.numbers
    ├── common/ # 공통 모듈 및 유틸
    │   ├── init.py
    │   ├── init_mongodb.py # MongoDB SSH 접속/설정
    │   ├── logger.py # 로그 처리 로직
    │   └── utils.py # 유틸리티 모음
    ├── script/                         # 수동 실행 스크립트
    │   ├── delete_logs_dates.py        # 오래된 로그 삭제 스크립트
    │   └── identify_bids.py            # 공고상 참여업체수 vs API 투찰 데이터 수 정합성 검사
    └── src/                            # 핵심 수집 로직
        ├── api_info.py                 # API 목록 관련 클래스(미완)
        ├── data_collector.py           # 데이터 수집 클래스
        ├── download_methods.py         # 데이터 수집 여러 함수
        ├── get_data_by_date_file.py    # 날짜 기록 파일 기반 수집
        ├── main.py                     # 수집기 실행 진입점
        ├── test.py                     # 테스트 스크립트(현재는 투찰데이터 수집 파일로 사용중)
        └── upload_api_info/            # 나라장터 API 목록 업로드 관련
            ├── csv_preprocessing.py    # CSV 가공
            ├── test.py
            └── upload_api_list.py      # 업로드 관련 함수

├── backend/ # 백엔드 (Django)
    ├── api/ # Django app (API 기능 중심)
    │   ├── init.py
    │   ├── admin.py # Django admin 설정
    │   ├── apps.py # 앱 설정(config)
    │   ├── models.py # DB 모델 정의(현재 PostgreSQL)
    │   ├── serializers.py # DRF 직렬화 정의
    │   ├── urls.py # 앱 라우팅 설정
    │   ├── migrations/ # 마이그레이션 파일
    │   │   ├── **init**.py
    │   │   └── 0001_initial.py
    │   ├── view/                   # 기능별 뷰 분리
    │   │   ├── __init__.py
    │   │   ├── analyze/            # 분석 API 관련 뷰
    │   │   ├── api_info/           # API 목록 제공
    │   │   └── refer/              # 데이터 조회 API
    ├── db_config/                  # DB 환경 설정 (다중 환경 지원)
    │   ├── __init__.py
    │   ├── local.py                # 로컬 환경 DB 설정
    │   ├── production.py           # 운영 환경 DB 설정
    ├── gfconDjango/                # Django 프로젝트 설정 디렉토리
    │   ├── __init__.py
    │   ├── asgi.py                 # 비동기 서버 진입점
    │   ├── settings.py             # 전역 설정
    │   ├── urls.py                 # 루트 라우팅 설정
    │   └── wsgi.py                 # WSGI 서버 진입점
    ├── manage.py                   #
    ├── .env                        # 환경 변수 설정 파일
    └── requirements.txt            # 패키지 의존성

├── config/ # 환경 설정 및 공통 설정 정보

├── crawler/ # 전기넷 웹 크롤링 관련
    ├── common/                          # 크롤링 공통 유틸
    │   ├── selenium_junginet.py         # Selenium 기반 크롤링 사전 코드
    │   └── utils.py                     # 유틸리티 함수 모음
    ├── .venv/
    ├── common.egg-info/                 # egg-info (패키징 시 생성)
    ├── setup.py                         # 패키징 스크립트

    ├── scripts/                         # 크롤링 한 데이터를 DB에 업로드
        ├── .venv/
        ├── .idea/
        ├── requirements.txt
        ├── src/                             # 데이터 처리 로직
        │   ├── export_data.py               
        │   ├── process_data.py              # 업로드 전 전처리
        │   └── upload_data.py               # 데이터 업로드
        └── test/                            

    ├── src/                             # 분석 추출 로직
    │   ├── common/                      # 공통 유틸
    │   ├── extract_bid_basic_info/      # 기본 공고 정보 추출
    │   │   ├── config.py
    │   │   ├── extract.py                  # 전기넷 공고 정보 화면에서 실제 크롤링
    │   │   ├── main.py                     # 전기넷 공고 목록 화면에서 진입
    │   │   ├── main_대업종.py
    │   │   ├── main_평가기준금액.py
    │   │   └── merge_year_csv.py        # 연도별 CSV 병합

    │   ├── extract_data_by_bid/         # 공고의 투찰 업체 정보 추출
    │   │   ├── extract.py
    │   │   ├── main.py
    │   │   └── test.py

    │   └── download_history.txt         # 다운로드 기록 로그

    ├── tests/                           # 전체 테스트 모듈
    ├── requirements.txt
    └── setup.py

├── data/ # 수집된 데이터 저장 (로컬 or 정제 데이터)

├── db/ # PostgreSQL(old DB) 초기화 스크립트

├── frontend/ # 프론트엔드 (React + Vite + TailwindCSS)
    ├── node_modules/                     # 의존성 패키지 설치 경로
    ├── public/
    │   └── vite.svg                      # 정적 에셋 (favicon, 이미지 등)
    ├── .env                              # 환경변수 설정
    ├── .gitignore
    ├── eslint.config.js                  # ESLint 규칙
    ├── index.html                        # HTML 템플릿
    ├── package.json                      # 프로젝트 의존성 및 스크립트
    ├── package-lock.json
    ├── README.md
    ├── tailwind.config.js                # Tailwind 설정
    ├── vite.config.js                    # Vite 설정

    ├── src/                              # 소스코드 루트
    │   ├── App.jsx                       # 루트 컴포넌트
    │   ├── index.css                     # 글로벌 스타일
    │   ├── main.jsx                      # 진입점

    │   ├── components/                   # 공통 UI 컴포넌트
    │   │   ├── Chart/                         # 차트 컴포넌트(공고별분석/업체별분석)
    │   │   │   ├── Histogram.jsx
    │   │   │   └── PieChart.jsx
    │   │   ├── Table/                         # 테이블 컴포넌트
    │   │   │   ├── Columns.jsx
    │   │   │   ├── MyAgGridTable.jsx               # client-side 테이블
    │   │   │   ├── ServerAgGridTable.jsx           # server-side 테이블
    │   │   │   └── TableContainer.jsx              # 테이블 wrapper
    │   │   ├── Nav-bar.jsx                    # 상단 메뉴 바
    │   │   └── Search-bar.jsx                 # 검색 바 컴포넌트

    │   ├── pages/                        # 라우트 기반 페이지 구조
    │   │   ├── AnalyzeData/                   # 데이터 분석 화면
    │   │   │   ├── ByCompanyPage.jsx               # 기업별 분석 
    │   │   │   └── ByNoticePage.jsx                # 공고별 분석
    │   │   ├── ApiInfo/                       # 나라장터 API 목록 조회
    │   │   │   └── ApiInfoPage.jsx
    │   │   ├── MainPage/                      # 메인페이지
    │   │   │   └── MainPage.jsx
    │   │   └── Model/                         # 모델 분석 페이지 관련
    │   │       ├── Chart/
    │   │       │   └── components/
    │   │       │       ├── AreaChartWrapper.jsx
    │   │       │       ├── ModelBarChart.jsx
    │   │       │       ├── ModelStackedAreaChart.jsx
    │   │       │       ├── ModelIndices.jsx
    │   │       │       └── OptionSelect.jsx
    │   │       ├── ModelPage.jsx
    │   │       └── components/
    │   │           ├── SelectModel.jsx
    │   │           └── SelectSectionNum.jsx 
        └── ReferData/                   # 데이터 조회 화면
            ├── BidsShow.jsx                # 투찰데이터 조회
            ├── CompaniesShow.jsx           # 업체데이터 조회
            └── NoticesShow.jsx             # 공고데이터 조회



