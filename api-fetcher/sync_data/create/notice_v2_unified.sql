-- notice_v2_unified.sql
-- 통합 입찰공고 테이블 (공사/물품/외자/용역 통합)
-- 4개 대분류의 모든 필드를 포함하며, 해당되지 않는 컬럼은 NULL
-- 생성일: 2025-12-18

DROP TABLE IF EXISTS notice CASCADE;

CREATE TABLE IF NOT EXISTS notice (
    -- ========================================
    -- Primary Key
    -- ========================================
    bidntceno VARCHAR(20) NOT NULL,           -- 입찰공고번호
    bidntceord VARCHAR(5) NOT NULL,           -- 입찰공고차수
    
    -- ========================================
    -- 업종 구분 (공사/물품/외자/용역)
    -- ========================================
    bsns_div VARCHAR(10),                     -- 업종구분 (공사/물품/외자/용역)

    -- ========================================
    -- 공통 필드 (4개 대분류 공통)
    -- ========================================
    arsltappldocrcptmthdnm TEXT, -- 실적신청서접수방법명
    bfspecrgstno TEXT, -- 사전규격등록번호
    bidbegindt TIMESTAMP, -- 입찰개시일시
    bidclsedt TIMESTAMP, -- 입찰마감일시
    bidgrntymnypaymntyn TEXT, -- 입찰보증금납부여부
    bidmethdnm TEXT, -- 입찰방식명
    bidntcedt TIMESTAMP, -- 입찰공고일시
    bidntcedtlurl TEXT, -- 입찰공고상세URL
    bidntcenm TEXT, -- 입찰공고명
    bidntceurl TEXT, -- 입찰공고URL
    bidprtcptfee BIGINT, -- 입찰참가수수료
    bidprtcptfeepaymntyn BIGINT, -- 입찰참가수수료납부여부
    bidqlfctrgstdt TIMESTAMP, -- 입찰참가자격등록마감일시
    brffcbidprcpermsnyn TEXT, -- 지사투찰허용여부
    chgdt TIMESTAMP, -- 변경일시
    chgntcersn TEXT, -- 변경공고사유
    cmmnspldmdagrmntclsedt TIMESTAMP, -- 공동수급협정마감일시
    cmmnspldmdagrmntrcptdocmethd TEXT, -- 공동수급협정서접수방식
    cmmnspldmdcorprgnlmtyn TEXT, -- 공동수급업체지역제한여부
    cmmnspldmdmethdcd TEXT, -- 공동수급방식코드
    cmmnspldmdmethdnm TEXT, -- 공동수급방식명
    cntrctcnclsmthdnm NUMERIC, -- 계약체결방법명
    crdtrnm TEXT, -- 채권자명
    dminsttcd TEXT, -- 수요기관코드
    dminsttnm TEXT, -- 수요기관명
    dminsttofclemailadrs TEXT, -- 수요기관담당자이메일주소
    drwtprdprcnum NUMERIC, -- 추첨예가건수
    dsgntcmptyn TEXT, -- 지명경쟁여부
    exctvnm TEXT, -- 집행관명
    indstrytylmtyn TEXT, -- 업종제한여부
    intrbidyn TEXT, -- 국제입찰여부
    ntceinsttcd TEXT, -- 공고기관코드
    ntceinsttnm TEXT, -- 공고기관명
    ntceinsttofclemailadrs TEXT, -- 공고기관담당자이메일주소
    ntceinsttofclnm TEXT, -- 공고기관담당자명
    ntceinsttofcltelno TEXT, -- 공고기관담당자전화번호
    ntcekindnm TEXT, -- 공고종류명
    ntcespecdocurl1 TEXT, -- 공고규격서URL1
    ntcespecdocurl10 TEXT, -- 공고규격서URL10
    ntcespecdocurl2 TEXT, -- 공고규격서URL2
    ntcespecdocurl3 TEXT, -- 공고규격서URL3
    ntcespecdocurl4 TEXT, -- 공고규격서URL4
    ntcespecdocurl5 TEXT, -- 공고규격서URL5
    ntcespecdocurl6 TEXT, -- 공고규격서URL6
    ntcespecdocurl7 TEXT, -- 공고규격서URL7
    ntcespecdocurl8 TEXT, -- 공고규격서URL8
    ntcespecdocurl9 TEXT, -- 공고규격서URL9
    ntcespecfilenm1 TEXT, -- 공고규격파일명1
    ntcespecfilenm10 TEXT, -- 공고규격파일명10
    ntcespecfilenm2 TEXT, -- 공고규격파일명2
    ntcespecfilenm3 TEXT, -- 공고규격파일명3
    ntcespecfilenm4 TEXT, -- 공고규격파일명4
    ntcespecfilenm5 TEXT, -- 공고규격파일명5
    ntcespecfilenm6 TEXT, -- 공고규격파일명6
    ntcespecfilenm7 TEXT, -- 공고규격파일명7
    ntcespecfilenm8 TEXT, -- 공고규격파일명8
    ntcespecfilenm9 TEXT, -- 공고규격파일명9
    opengdt TIMESTAMP, -- 개찰일시
    opengplce TEXT, -- 개찰장소
    orderplanuntyno TEXT, -- 발주계획통합번호
    prearngprcedcsnmthdnm BIGINT, -- 예정가격결정방법명
    presmptprce BIGINT, -- 추정가격
    rbidopengdt TIMESTAMP, -- 재입찰개찰일시
    rbidpermsnyn TEXT, -- 재입찰허용여부
    rentceyn TEXT, -- 재공고여부
    refno TEXT, -- 참조번호
    rgstdt TIMESTAMP, -- 등록일시
    rgsttynm TEXT, -- 등록유형명
    rsrvtnprceremkngmthdnm BIGINT, -- 예비가격재작성방법명
    stdntcedocurl TEXT, -- 표준공고서URL
    sucsfbidlwltrate NUMERIC, -- 낙찰하한율
    sucsfbidmthdcd TEXT, -- 낙찰방법코드
    sucsfbidmthdnm TEXT, -- 낙찰방법명
    totprdprcnum NUMERIC, -- 총예가건수
    untyntceno TEXT, -- 통합공고번호

    -- ========================================
    -- 공사 관련 필드
    -- ========================================
    aplbsscntnts NUMERIC, -- 적용기준내용 [공사전용]
    bdgtamt BIGINT, -- 예산금액 [공사전용]
    ciblaplyn TEXT, -- 건설산업법적용대상여부 [공사전용]
    cmmnspldmdcnum NUMERIC, -- 공동수급업체수 [공사전용]
    cnstrtnabltyevlamtlist BIGINT, -- 시공능력평가금액목록 [공사전용]
    cnstrtsitergnnm NUMERIC, -- 공사현장지역명 [공사전용]
    cnsttyaccotshreratelist NUMERIC, -- 공종별지분율목록 [공사전용]
    contrctrcnstrtngovsplymtrlamt BIGINT, -- 도급자설치관급자재금액 [공사전용]
    govcnstrtngovsplymtrlamt BIGINT, -- 관급자설치관급자재금액 [공사전용]
    govsplyamt BIGINT, -- 관급금액 [공사전용]
    incntvrgnnm1 NUMERIC, -- 가산지역명1 [공사전용]
    incntvrgnnm2 NUMERIC, -- 가산지역명2 [공사전용]
    incntvrgnnm3 NUMERIC, -- 가산지역명3 [공사전용]
    incntvrgnnm4 NUMERIC, -- 가산지역명4 [공사전용]
    indstrytyevlrt NUMERIC, -- 업종평가비율 [공사전용]
    indstrytymfrcfldevlyn TEXT, -- 주력분야평가여부 [공사전용]
    maincnsttycnstwkprearngamt BIGINT, -- 주공종공사예정금액 [공사전용]
    maincnsttynm TEXT, -- 주공종명 [공사전용]
    maincnsttypresmptprce BIGINT, -- 주공종추정가격 [공사전용]
    mtltyadvcpsblyn TEXT, -- 상호시장진출허용여부 [공사전용]
    mtltyadvcpsblyncnstwknm TEXT, -- 건설산업법적용대상공사명 [공사전용]
    rgndutyjntcontrctyn TEXT, -- 지역의무공동도급여부 [공사전용]
    sptdscrptdocurl1 TEXT, -- 현장설명서URL1 [공사전용]
    sptdscrptdocurl2 TEXT, -- 현장설명서URL2 [공사전용]
    sptdscrptdocurl3 TEXT, -- 현장설명서URL3 [공사전용]
    sptdscrptdocurl4 TEXT, -- 현장설명서URL4 [공사전용]
    sptdscrptdocurl5 TEXT, -- 현장설명서URL5 [공사전용]
    subsicnsttyindstrytyevlrt1 NUMERIC, -- 부공종업종평가비율1 [공사전용]
    subsicnsttyindstrytyevlrt2 NUMERIC, -- 부공종업종평가비율2 [공사전용]
    subsicnsttyindstrytyevlrt3 NUMERIC, -- 부공종업종평가비율3 [공사전용]
    subsicnsttyindstrytyevlrt4 NUMERIC, -- 부공종업종평가비율4 [공사전용]
    subsicnsttyindstrytyevlrt5 NUMERIC, -- 부공종업종평가비율5 [공사전용]
    subsicnsttyindstrytyevlrt6 NUMERIC, -- 부공종업종평가비율6 [공사전용]
    subsicnsttyindstrytyevlrt7 NUMERIC, -- 부공종업종평가비율7 [공사전용]
    subsicnsttyindstrytyevlrt8 NUMERIC, -- 부공종업종평가비율8 [공사전용]
    subsicnsttyindstrytyevlrt9 NUMERIC, -- 부공종업종평가비율9 [공사전용]
    subsicnsttynm1 TEXT, -- 부대공종명1 [공사전용]
    subsicnsttynm2 TEXT, -- 부대공종명2 [공사전용]
    subsicnsttynm3 TEXT, -- 부대공종명3 [공사전용]
    subsicnsttynm4 TEXT, -- 부대공종명4 [공사전용]
    subsicnsttynm5 TEXT, -- 부대공종명5 [공사전용]
    subsicnsttynm6 TEXT, -- 부대공종명6 [공사전용]
    subsicnsttynm7 TEXT, -- 부대공종명7 [공사전용]
    subsicnsttynm8 TEXT, -- 부대공종명8 [공사전용]
    subsicnsttynm9 TEXT, -- 부대공종명9 [공사전용]

    -- ========================================
    -- 물품 관련 필드
    -- ========================================
    rgnlmtbidlocplcjdgmbsscd TEXT, -- [물품전용]
    rgnlmtbidlocplcjdgmbssnm TEXT, -- [물품전용]

    -- ========================================
    -- 외자 관련 필드
    -- ========================================
    prdctsno TEXT, -- 물품순번 [외자전용]

    -- ========================================
    -- 용역 관련 필드
    -- ========================================
    arsltreqstdocrcptdt TIMESTAMP, -- 실적신청서접수일시 [용역전용]
    ppswgnrlsrvceyn TEXT, -- 조달청일반용역여부 [용역전용]
    srvcedivnm TEXT, -- 용역구분명 [용역전용]
    tpevalapplclsedt TIMESTAMP, -- TP심사신청마감일시 [용역전용]
    tpevalapplmthdnm TEXT, -- TP심사신청방법명 [용역전용]
    tpevalyn TEXT, -- TP심사여부 [용역전용]

    -- ========================================
    -- 복수 대분류 공통 필드
    -- ========================================
    vat TEXT, -- 부가가치세 [공사,물품,용역]
    arsltappldocrcptdt TIMESTAMP, -- 실적신청서접수일시 [공사,물품,외자]
    arsltcmptyn TEXT, -- 실적경쟁여부 [공사,용역]
    asignbdgtamt BIGINT, -- 배정예산금액 [물품,외자,용역]
    bidprceevlrt BIGINT, -- [물품,외자]
    bidprtcptlmtyn NUMERIC, -- 입찰참가제한여부 [공사,용역]
    bidwgrnteercptclsedt TIMESTAMP, -- 입찰보증서접수마감일시 [공사,물품,외자]
    dcmtgoprtndt NUMERIC, -- 설명회실시일시 [공사,용역]
    dcmtgoprtnplce NUMERIC, -- 설명회실시장소 [공사,용역]
    dlvrdaynum NUMERIC, -- 납품일수 [물품,외자]
    dlvrtmlmtdt NUMERIC, -- 납품기한일시 [물품,외자]
    dlvrycndtnnm TEXT, -- 인도조건명 [물품,외자]
    dtilprdctclsfcno TEXT, -- 세부품명번호 [물품,외자]
    dtilprdctclsfcnonm TEXT, -- 세부품명 [물품,외자]
    dtlsbidyn TEXT, -- 내역입찰여부 [공사,용역]
    indutyvat TEXT, -- 주공종부가가치세 [공사,물품,용역]
    infobizyn TEXT, -- 정보화사업여부 [물품,용역]
    jntcontrctdutyrgnnm1 TEXT, -- 공동도급의무지역명1 [공사,용역]
    jntcontrctdutyrgnnm2 TEXT, -- 공동도급의무지역명2 [공사,용역]
    jntcontrctdutyrgnnm3 TEXT, -- 공동도급의무지역명3 [공사,용역]
    mnfctyn TEXT, -- 제조여부 [물품,외자,용역]
    ntcedscrptyn TEXT, -- 공고설명여부 [공사,용역]
    pqappldocrcptdt TIMESTAMP, -- PQ신청서접수일시 [공사,용역]
    pqappldocrcptmthdnm TEXT, -- PQ신청서접수방법명 [공사,용역]
    pqevalyn TEXT, -- PQ심사여부 [공사,용역]
    prdctclsfclmtyn TEXT, -- 물품분류제한여부 [물품,외자,용역]
    prdctqty NUMERIC, -- 물품수량 [물품,외자]
    prdctspecnm TEXT, -- 물품규격명 [물품,외자]
    prdctunit TEXT, -- 물품단위 [물품,외자]
    prdctuprc NUMERIC, -- 물품단가 [물품,외자]
    purchsobjprdctlist TEXT, -- 구매대상물품목록 [물품,외자,용역]
    rgndutyjntcontrctrt NUMERIC, -- 지역의무공동도급비율 [공사,용역]
    techabltevlrt NUMERIC, -- [물품,외자]

    -- ========================================
    -- 기초금액 정보 (입찰공고목록정보에대한공사기초금액조회)
    -- ========================================
    bssamt BIGINT,                            -- 기초금액
    bssamtopendt TIMESTAMP,                   -- 기초금액공개일시
    rsrvtnprcerngbgnrate NUMERIC,             -- 예비가격범위시작률
    rsrvtnprcerngendrate NUMERIC,             -- 예비가격범위종료율
    evlbssamt BIGINT,                         -- 평가기준금액
    dfcltydgrcfcnt NUMERIC,                   -- 난이도계수
    etcgnrlexpnsbssrate NUMERIC,              -- 기타경비기준율
    gnrlmngcstbssrate NUMERIC,                -- 일반관리비기준율
    prftbssrate NUMERIC,                      -- 이윤기준율
    lbrcstbssrate NUMERIC,                    -- 노무비기준율
    sftymngcst BIGINT,                        -- 산업안전보건관리비
    sftychckmngcst BIGINT,                    -- 안전관리비
    rtrfundnon BIGINT,                        -- 퇴직공제부금비
    envcnsrvcst BIGINT,                       -- 환경보전비
    scontrctpayprcepaygrntyfee BIGINT,        -- 하도급대금지급보증수수료
    mrfnhealthinsrprm BIGINT,                 -- 국민건강보험료
    npninsrprm BIGINT,                        -- 국민연금보험료
    rmrk1 TEXT,                               -- 비고1
    rmrk2 TEXT,                               -- 비고2
    odsnlngtrmrcprinsrprm BIGINT,             -- 노인장기요양보험료
    usefulamt BIGINT,                         -- 가용금액
    inptdt TIMESTAMP,                         -- 입력일시
    bidprcecalclayn CHAR(1),                  -- 입찰가격산식A여부
    bssamtpurcnstcst NUMERIC,                 -- 기초금액순공사비
    qltymngcst BIGINT,                        -- 품질관리비 (공사)
    qltymngcstaobjyn CHAR(1),                 -- 품질관리비A적용대상여부 (공사)
    industsftyhelthMngcst BIGINT,             -- 산업안전보건관리비 (물품)
    smkpamt BIGINT,                           -- 표준시장단가금액
    smkpamtyn CHAR(1),                        -- 표준시장단가금액A적용대상여부

    -- ========================================
    -- 낙찰 정보 (공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보)
    -- ========================================
    opengdate DATE,                           -- 개찰일자
    opengtm TIME,                             -- 개찰시간
    opengrsltdivnm TEXT,                      -- 개찰결과구분명
    fnlsucsfamt BIGINT,                       -- 최종낙찰금액
    fnlsucsfrt NUMERIC,                       -- 최종낙찰률
    fnlsucsfdate DATE,                        -- 최종낙찰일자
    fnlsucsfcorpnm TEXT,                      -- 최종낙찰업체명
    fnlsucsfcorpceonm TEXT,                   -- 최종낙찰업체대표자명
    fnlsucsfcorpofclnm TEXT,                  -- 최종낙찰업체담당자명
    fnlsucsfcorpbizrno TEXT,                  -- 최종낙찰업체사업자번호
    fnlsucsfcorpadrs TEXT,                    -- 최종낙찰업체주소
    fnlsucsfcorpcontacttel TEXT,              -- 최종낙찰업체전화번호
    cntrctcnclssttusNm TEXT,                  -- 계약체결상태명
    bidwinrdcsnmthdnm TEXT,                   -- 낙찰자결정방법명

    -- ========================================
    -- 메타 정보 (동기화 시점)
    -- ========================================
    synced_at TIMESTAMPTZ,                    -- 기본 공고정보 동기화 시점
    bssamt_synced_at TIMESTAMPTZ,             -- 기초금액 동기화 시점
    win_synced_at TIMESTAMPTZ,                -- 낙찰정보 동기화 시점

    -- ========================================
    -- 계산 컬럼 (후처리)
    -- ========================================
    a_value NUMERIC GENERATED ALWAYS AS (
        COALESCE(sftymngcst, 0) +
        COALESCE(sftychckmngcst, 0) +
        COALESCE(rtrfundnon, 0) +
        COALESCE(mrfnhealthinsrprm, 0) +
        COALESCE(npninsrprm, 0) +
        COALESCE(odsnlngtrmrcprinsrprm, 0) +
        CASE WHEN qltymngcstaobjyn = 'Y' THEN COALESCE(qltymngcst, 0) ELSE 0 END +
        CASE WHEN smkpamtyn = 'Y' THEN COALESCE(smkpamt, 0) ELSE 0 END
    ) STORED,                                 -- A값 (안전관리비+보험료 합산)
    bid_count INTEGER,                        -- 참여업체수 (후처리)
    answer_rate NUMERIC,                      -- 사정률 (후처리)
    min_winning_price NUMERIC,                -- 낙찰하한가 (후처리)

    -- ========================================
    -- 제약 조건
    -- ========================================
    PRIMARY KEY (bidntceno, bidntceord)
);

-- 테이블 코멘트
COMMENT ON TABLE notice IS '입찰공고 통합 테이블 (공사/물품/외자/용역)';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_notice_bsns_div ON notice (bsns_div);
CREATE INDEX IF NOT EXISTS idx_notice_bidntcedt ON notice (bidntcedt);
CREATE INDEX IF NOT EXISTS idx_notice_ntceinsttnm ON notice (ntceinsttnm);
CREATE INDEX IF NOT EXISTS idx_notice_fnlsucsfcorpbizrno ON notice (fnlsucsfcorpbizrno);
