DROP TABLE notice;

CREATE TABLE IF NOT EXISTS notice
(
    --- 공고 입찰 데이터(미개찰/기개찰)
    ---------------------------------------------------------------------
    bidNtceNo                     TEXT,
    bidNtceOrd                    TEXT,
    reNtceYn                      TEXT,
    rgstTyNm                      TEXT,
    ntceKindNm                    TEXT,
    intrbidYn                     TEXT,
    bidNtceDt                     TIMESTAMP,
    refNo                         TEXT,
    bidNtceNm                     TEXT,
    ntceInsttCd                   TEXT,
    ntceInsttNm                   TEXT,
    dminsttCd                     TEXT,
    dminsttNm                     TEXT,
    bidMethdNm                    TEXT,
    cntrctCnclsMthdNm             TEXT,
    ntceInsttOfclNm               TEXT,
    ntceInsttOfclTelNo            TEXT,
    ntceInsttOfclEmailAdrs        TEXT,
    exctvNm                       TEXT,
    bidQlfctRgstDt                TIMESTAMP,
    cmmnSpldmdAgrmntRcptdocMethd  TEXT,
    cmmnSpldmdAgrmntClseDt        TEXT,
    cmmnSpldmdCorpRgnLmtYn        TEXT,
    bidBeginDt                    TIMESTAMP,
    bidClseDt                     TIMESTAMP,
    opengDt                       TIMESTAMP,
    ntceSpecDocUrl1               TEXT,
    ntceSpecDocUrl2               TEXT,
    ntceSpecDocUrl3               TEXT,
    ntceSpecDocUrl4               TEXT,
    ntceSpecDocUrl5               TEXT,
    ntceSpecDocUrl6               TEXT,
    ntceSpecDocUrl7               TEXT,
    ntceSpecDocUrl8               TEXT,
    ntceSpecDocUrl9               TEXT,
    ntceSpecDocUrl10              TEXT,
    ntceSpecFileNm1               TEXT,
    ntceSpecFileNm2               TEXT,
    ntceSpecFileNm3               TEXT,
    ntceSpecFileNm4               TEXT,
    ntceSpecFileNm5               TEXT,
    ntceSpecFileNm6               TEXT,
    ntceSpecFileNm7               TEXT,
    ntceSpecFileNm8               TEXT,
    ntceSpecFileNm9               TEXT,
    ntceSpecFileNm10              TEXT,
    rbidPermsnYn                  TEXT,
    pqApplDocRcptMthdNm           TEXT,
    pqApplDocRcptDt               TEXT,
    arsltApplDocRcptMthdNm        TEXT,
    arsltApplDocRcptDt            TEXT,
    jntcontrctDutyRgnNm1          TEXT,
    jntcontrctDutyRgnNm2          TEXT,
    jntcontrctDutyRgnNm3          TEXT,
    rgnDutyJntcontrctRt           TEXT,
    dtlsBidYn                     TEXT,
    bidPrtcptLmtYn                TEXT,
    prearngPrceDcsnMthdNm         TEXT,
    totPrdprcNum                  INTEGER,
    drwtPrdprcNum                 INTEGER,
    bdgtAmt                       BIGINT,
    presmptPrce                   BIGINT,
    govsplyAmt                    BIGINT,
    aplBssCntnts                  TEXT,
    indstrytyEvlRt                TEXT,
    mainCnsttyNm                  TEXT,
    mainCnsttyCnstwkPrearngAmt    TEXT,
    incntvRgnNm1                  TEXT,
    incntvRgnNm2                  TEXT,
    incntvRgnNm3                  TEXT,
    incntvRgnNm4                  TEXT,
    opengPlce                     TEXT,
    dcmtgOprtnDt                  TEXT,
    dcmtgOprtnPlce                TEXT,
    contrctrcnstrtnGovsplyMtrlAmt BIGINT,
    govcnstrtnGovsplyMtrlAmt      BIGINT,
    bidNtceDtlUrl                 TEXT,
    bidNtceUrl                    TEXT,
    bidPrtcptFeePaymntYn          TEXT,
    bidPrtcptFee                  TEXT,
    bidGrntymnyPaymntYn           TEXT,
    crdtrNm                       TEXT,
    cmmnSpldmdCnum                TEXT,
    untyNtceNo                    TEXT,
    sptDscrptDocUrl1              TEXT,
    sptDscrptDocUrl2              TEXT,
    sptDscrptDocUrl3              TEXT,
    sptDscrptDocUrl4              TEXT,
    sptDscrptDocUrl5              TEXT,
    subsiCnsttyNm1                TEXT,
    subsiCnsttyNm2                TEXT,
    subsiCnsttyNm3                TEXT,
    subsiCnsttyNm4                TEXT,
    subsiCnsttyNm5                TEXT,
    subsiCnsttyNm6                TEXT,
    subsiCnsttyNm7                TEXT,
    subsiCnsttyNm8                TEXT,
    subsiCnsttyNm9                TEXT,
    subsiCnsttyIndstrytyEvlRt1    TEXT,
    subsiCnsttyIndstrytyEvlRt2    TEXT,
    subsiCnsttyIndstrytyEvlRt3    TEXT,
    subsiCnsttyIndstrytyEvlRt4    TEXT,
    subsiCnsttyIndstrytyEvlRt5    TEXT,
    subsiCnsttyIndstrytyEvlRt6    TEXT,
    subsiCnsttyIndstrytyEvlRt7    TEXT,
    subsiCnsttyIndstrytyEvlRt8    TEXT,
    subsiCnsttyIndstrytyEvlRt9    TEXT,
    cmmnSpldmdMethdCd             TEXT,
    cmmnSpldmdMethdNm             TEXT,
    stdNtceDocUrl                 TEXT,
    brffcBidprcPermsnYn           TEXT,
    cnsttyAccotShreRateList       TEXT,
    cnstrtnAbltyEvlAmtList        TEXT,
    dsgntCmptYn                   TEXT,
    arsltCmptYn                   TEXT,
    pqEvalYn                      TEXT,
    ntceDscrptYn                  TEXT,
    rsrvtnPrceReMkngMthdNm        TEXT,
    mainCnsttyPresmptPrce         TEXT,
    orderPlanUntyNo               TEXT,
    sucsfbidLwltRate              NUMERIC,
    rgstDt                        TIMESTAMP,
    bfSpecRgstNo                  TEXT,
    sucsfbidMthdCd                TEXT,
    sucsfbidMthdNm                TEXT,
    chgDt                         TEXT,
    dminsttOfclEmailAdrs          TEXT,
    indstrytyLmtYn                TEXT,
    cnstrtsiteRgnNm               TEXT,
    rgnDutyJntcontrctYn           TEXT,
    chgNtceRsn                    TEXT,
    rbidOpengDt                   TEXT,
    ciblAplYn                     TEXT,
    mtltyAdvcPsblYn               TEXT,
    mtltyAdvcPsblYnCnstwkNm       TEXT,
    VAT                           TEXT,
    indutyVAT                     TEXT,
    indstrytyMfrcFldEvlYn         TEXT,
    bidWgrnteeRcptClseDt          TEXT,
    --- 공고 기초금액 오퍼레이션(미개찰/기개찰)
    ---------------------------------------------------------------------
    bssamt                        BIGINT,
    bssamtOpenDt                  TIMESTAMP,
    rsrvtnPrceRngBgnRate          NUMERIC,
    rsrvtnPrceRngEndRate          NUMERIC,
    evlBssAmt                     BIGINT,
    dfcltydgrCfcnt                NUMERIC,
    etcGnrlexpnsBssRate           NUMERIC,
    gnrlMngcstBssRate             NUMERIC,
    prftBssRate                   NUMERIC,
    lbrcstBssRate                 NUMERIC,
    sftyMngcst                    BIGINT,
    sftyChckMngcst                BIGINT,
    rtrfundNon                    BIGINT,
    envCnsrvcst                   BIGINT,
    scontrctPayprcePayGrntyFee    BIGINT,
    mrfnHealthInsrprm             BIGINT,
    npnInsrprm                    BIGINT,
    rmrk1                         TEXT,
    rmrk2                         TEXT,
    odsnLngtrmrcprInsrprm         BIGINT,
    usefulAmt                     BIGINT,
    inptDt                        TIMESTAMP,
    bidPrceCalclAYn               CHAR(1),
    bssAmtPurcnstcst              TEXT,
    qltyMngcst                    BIGINT,
    qltyMngcstAObjYn              CHAR(1),
    --- 공고 낙찰 오퍼레이션(기개찰)
    ---------------------------------------------------------------------
    fnlSucsfAmt                   BIGINT,
    fnlSucsfRt                    NUMERIC,
    fnlSucsfDate                  DATE,
    fnlSucsfCorpNm                TEXT,
    fnlSucsfCorpCeoNm             TEXT,
    fnlSucsfCorpOfclNm            TEXT,
    fnlSucsfCorpBizrno            TEXT,
    fnlSucsfCorpAdrs              TEXT,
    fnlSucsfCorpContactTel        TEXT,

    cntrctCnclsSttusNm            TEXT,
    bidwinrDcsnMthdNm             TEXT,

    PRIMARY KEY (bidNtceNo, bidNtceOrd)
);

--- 공고 입찰 데이터(미개찰/기개찰)
---------------------------------------------------------------------
COMMENT ON COLUMN notice.bidNtceNo IS '입찰공고번호';
COMMENT ON COLUMN notice.bidNtceOrd IS '입찰공고차수';
COMMENT ON COLUMN notice.reNtceYn IS '재공고여부';
COMMENT ON COLUMN notice.rgstTyNm IS '등록유형명';
COMMENT ON COLUMN notice.ntceKindNm IS '공고종류명';
COMMENT ON COLUMN notice.intrbidYn IS '국제입찰여부';
COMMENT ON COLUMN notice.bidNtceDt IS '입찰공고일시';
COMMENT ON COLUMN notice.refNo IS '참조번호';
COMMENT ON COLUMN notice.bidNtceNm IS '입찰공고명';
COMMENT ON COLUMN notice.ntceInsttCd IS '공고기관코드';
COMMENT ON COLUMN notice.ntceInsttNm IS '공고기관명';
COMMENT ON COLUMN notice.dminsttCd IS '수요기관코드';
COMMENT ON COLUMN notice.dminsttNm IS '수요기관명';
COMMENT ON COLUMN notice.bidMethdNm IS '입찰방식명';
COMMENT ON COLUMN notice.cntrctCnclsMthdNm IS '계약체결방법명';
COMMENT ON COLUMN notice.ntceInsttOfclNm IS '공고기관담당자명';
COMMENT ON COLUMN notice.ntceInsttOfclTelNo IS '공고기관담당자전화번호';
COMMENT ON COLUMN notice.ntceInsttOfclEmailAdrs IS '공고기관담당자이메일주소';
COMMENT ON COLUMN notice.exctvNm IS '집행관명';
COMMENT ON COLUMN notice.bidQlfctRgstDt IS '입찰참가자격등록마감일시';
COMMENT ON COLUMN notice.cmmnSpldmdAgrmntRcptdocMethd IS '공동수급협정서접수방식';
COMMENT ON COLUMN notice.cmmnSpldmdAgrmntClseDt IS '공동수급협정마감일시';
COMMENT ON COLUMN notice.cmmnSpldmdCorpRgnLmtYn IS '공동수급업체지역제한여부';
COMMENT ON COLUMN notice.bidBeginDt IS '입찰개시일시';
COMMENT ON COLUMN notice.bidClseDt IS '입찰마감일시';
COMMENT ON COLUMN notice.opengDt IS '개찰일시';
COMMENT ON COLUMN notice.ntceSpecDocUrl1 IS '공고규격서URL1';
COMMENT ON COLUMN notice.ntceSpecDocUrl2 IS '공고규격서URL2';
COMMENT ON COLUMN notice.ntceSpecDocUrl3 IS '공고규격서URL3';
COMMENT ON COLUMN notice.ntceSpecDocUrl4 IS '공고규격서URL4';
COMMENT ON COLUMN notice.ntceSpecDocUrl5 IS '공고규격서URL5';
COMMENT ON COLUMN notice.ntceSpecDocUrl6 IS '공고규격서URL6';
COMMENT ON COLUMN notice.ntceSpecDocUrl7 IS '공고규격서URL7';
COMMENT ON COLUMN notice.ntceSpecDocUrl8 IS '공고규격서URL8';
COMMENT ON COLUMN notice.ntceSpecDocUrl9 IS '공고규격서URL9';
COMMENT ON COLUMN notice.ntceSpecDocUrl10 IS '공고규격서URL10';
COMMENT ON COLUMN notice.ntceSpecFileNm1 IS '공고규격파일명1';
COMMENT ON COLUMN notice.ntceSpecFileNm2 IS '공고규격파일명2';
COMMENT ON COLUMN notice.ntceSpecFileNm3 IS '공고규격파일명3';
COMMENT ON COLUMN notice.ntceSpecFileNm4 IS '공고규격파일명4';
COMMENT ON COLUMN notice.ntceSpecFileNm5 IS '공고규격파일명5';
COMMENT ON COLUMN notice.ntceSpecFileNm6 IS '공고규격파일명6';
COMMENT ON COLUMN notice.ntceSpecFileNm7 IS '공고규격파일명7';
COMMENT ON COLUMN notice.ntceSpecFileNm8 IS '공고규격파일명8';
COMMENT ON COLUMN notice.ntceSpecFileNm9 IS '공고규격파일명9';
COMMENT ON COLUMN notice.ntceSpecFileNm10 IS '공고규격파일명10';
COMMENT ON COLUMN notice.rbidPermsnYn IS '재입찰허용여부';
COMMENT ON COLUMN notice.pqApplDocRcptMthdNm IS 'PQ신청서접수방법명';
COMMENT ON COLUMN notice.pqApplDocRcptDt IS 'PQ신청서접수일시';
COMMENT ON COLUMN notice.arsltApplDocRcptMthdNm IS '실적신청서접수방법명';
COMMENT ON COLUMN notice.arsltApplDocRcptDt IS '실적신청서접수일시';
COMMENT ON COLUMN notice.jntcontrctDutyRgnNm1 IS '공동도급의무지역명1';
COMMENT ON COLUMN notice.jntcontrctDutyRgnNm2 IS '공동도급의무지역명2';
COMMENT ON COLUMN notice.jntcontrctDutyRgnNm3 IS '공동도급의무지역명3';
COMMENT ON COLUMN notice.rgnDutyJntcontrctRt IS '지역의무공동도급비율';
COMMENT ON COLUMN notice.dtlsBidYn IS '내역입찰여부';
COMMENT ON COLUMN notice.bidPrtcptLmtYn IS '입찰참가제한여부';
COMMENT ON COLUMN notice.prearngPrceDcsnMthdNm IS '예정가격결정방법명';
COMMENT ON COLUMN notice.totPrdprcNum IS '총예가건수';
COMMENT ON COLUMN notice.drwtPrdprcNum IS '추첨예가건수';
COMMENT ON COLUMN notice.bdgtAmt IS '예산금액';
COMMENT ON COLUMN notice.presmptPrce IS '추정가격';
COMMENT ON COLUMN notice.govsplyAmt IS '관급금액';
COMMENT ON COLUMN notice.aplBssCntnts IS '적용기준내용';
COMMENT ON COLUMN notice.indstrytyEvlRt IS '업종평가비율';
COMMENT ON COLUMN notice.mainCnsttyNm IS '주공종명';
COMMENT ON COLUMN notice.mainCnsttyCnstwkPrearngAmt IS '주공종공사예정금액';
COMMENT ON COLUMN notice.incntvRgnNm1 IS '가산지역명1';
COMMENT ON COLUMN notice.incntvRgnNm2 IS '가산지역명2';
COMMENT ON COLUMN notice.incntvRgnNm3 IS '가산지역명3';
COMMENT ON COLUMN notice.incntvRgnNm4 IS '가산지역명4';
COMMENT ON COLUMN notice.opengPlce IS '개찰장소';
COMMENT ON COLUMN notice.dcmtgOprtnDt IS '설명회실시일시';
COMMENT ON COLUMN notice.dcmtgOprtnPlce IS '설명회실시장소';
COMMENT ON COLUMN notice.contrctrcnstrtnGovsplyMtrlAmt IS '도급자설치관급자재금액';
COMMENT ON COLUMN notice.govcnstrtnGovsplyMtrlAmt IS '관급자설치관급자재금액';
COMMENT ON COLUMN notice.bidNtceDtlUrl IS '입찰공고상세URL';
COMMENT ON COLUMN notice.bidNtceUrl IS '입찰공고URL';
COMMENT ON COLUMN notice.bidPrtcptFeePaymntYn IS '입찰참가수수료납부여부';
COMMENT ON COLUMN notice.bidPrtcptFee IS '입찰참가수수료';
COMMENT ON COLUMN notice.bidGrntymnyPaymntYn IS '입찰보증금납부여부';
COMMENT ON COLUMN notice.crdtrNm IS '채권자명';
COMMENT ON COLUMN notice.cmmnSpldmdCnum IS '공동수급업체수';
COMMENT ON COLUMN notice.untyNtceNo IS '통합공고번호';
COMMENT ON COLUMN notice.sptDscrptDocUrl1 IS '현장설명서URL1';
COMMENT ON COLUMN notice.sptDscrptDocUrl2 IS '현장설명서URL2';
COMMENT ON COLUMN notice.sptDscrptDocUrl3 IS '현장설명서URL3';
COMMENT ON COLUMN notice.sptDscrptDocUrl4 IS '현장설명서URL4';
COMMENT ON COLUMN notice.sptDscrptDocUrl5 IS '현장설명서URL5';
COMMENT ON COLUMN notice.subsiCnsttyNm1 IS '부대공종명1';
COMMENT ON COLUMN notice.subsiCnsttyNm2 IS '부대공종명2';
COMMENT ON COLUMN notice.subsiCnsttyNm3 IS '부대공종명3';
COMMENT ON COLUMN notice.subsiCnsttyNm4 IS '부대공종명4';
COMMENT ON COLUMN notice.subsiCnsttyNm5 IS '부대공종명5';
COMMENT ON COLUMN notice.subsiCnsttyNm6 IS '부대공종명6';
COMMENT ON COLUMN notice.subsiCnsttyNm7 IS '부대공종명7';
COMMENT ON COLUMN notice.subsiCnsttyNm8 IS '부대공종명8';
COMMENT ON COLUMN notice.subsiCnsttyNm9 IS '부대공종명9';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt1 IS '부공종업종평가비율1';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt2 IS '부공종업종평가비율2';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt3 IS '부공종업종평가비율3';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt4 IS '부공종업종평가비율4';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt5 IS '부공종업종평가비율5';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt6 IS '부공종업종평가비율6';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt7 IS '부공종업종평가비율7';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt8 IS '부공종업종평가비율8';
COMMENT ON COLUMN notice.subsiCnsttyIndstrytyEvlRt9 IS '부공종업종평가비율9';
COMMENT ON COLUMN notice.cmmnSpldmdMethdCd IS '공동수급방식코드';
COMMENT ON COLUMN notice.cmmnSpldmdMethdNm IS '공동수급방식명';
COMMENT ON COLUMN notice.stdNtceDocUrl IS '표준공고서URL';
COMMENT ON COLUMN notice.brffcBidprcPermsnYn IS '지사투찰허용여부';
COMMENT ON COLUMN notice.cnsttyAccotShreRateList IS '공종별지분율목록';
COMMENT ON COLUMN notice.cnstrtnAbltyEvlAmtList IS '시공능력평가금액목록';
COMMENT ON COLUMN notice.dsgntCmptYn IS '지명경쟁여부';
COMMENT ON COLUMN notice.arsltCmptYn IS '실적경쟁여부';
COMMENT ON COLUMN notice.pqEvalYn IS 'PQ심사여부';
COMMENT ON COLUMN notice.ntceDscrptYn IS '공고설명여부';
COMMENT ON COLUMN notice.rsrvtnPrceReMkngMthdNm IS '예비가격재작성방법명';
COMMENT ON COLUMN notice.mainCnsttyPresmptPrce IS '주공종추정가격';
COMMENT ON COLUMN notice.orderPlanUntyNo IS '발주계획통합번호';
COMMENT ON COLUMN notice.sucsfbidLwltRate IS '낙찰하한율';
COMMENT ON COLUMN notice.rgstDt IS '등록일시';
COMMENT ON COLUMN notice.bfSpecRgstNo IS '사전규격등록번호';
COMMENT ON COLUMN notice.sucsfbidMthdCd IS '낙찰방법코드';
COMMENT ON COLUMN notice.sucsfbidMthdNm IS '낙찰방법명';
COMMENT ON COLUMN notice.chgDt IS '변경일시';
COMMENT ON COLUMN notice.dminsttOfclEmailAdrs IS '수요기관담당자이메일주소';
COMMENT ON COLUMN notice.indstrytyLmtYn IS '업종제한여부';
COMMENT ON COLUMN notice.cnstrtsiteRgnNm IS '공사현장지역명';
COMMENT ON COLUMN notice.rgnDutyJntcontrctYn IS '지역의무공동도급여부';
COMMENT ON COLUMN notice.chgNtceRsn IS '변경공고사유';
COMMENT ON COLUMN notice.rbidOpengDt IS '재입찰개찰일시';
COMMENT ON COLUMN notice.ciblAplYn IS '건설산업법적용대상여부';
COMMENT ON COLUMN notice.mtltyAdvcPsblYn IS '상호시장진출허용여부';
COMMENT ON COLUMN notice.mtltyAdvcPsblYnCnstwkNm IS '건설산업법적용대상공사명';
COMMENT ON COLUMN notice.VAT IS '부가가치세';
COMMENT ON COLUMN notice.indutyVAT IS '주공종부가가치세';
COMMENT ON COLUMN notice.indstrytyMfrcFldEvlYn IS '주력분야평가여부';
COMMENT ON COLUMN notice.bidWgrnteeRcptClseDt IS '입찰보증서접수마감일시';
--- 공고 기초금액 오퍼레이션(미개찰/기개찰)
---------------------------------------------------------------------
COMMENT ON COLUMN notice.bssamt IS '기초금액';
COMMENT ON COLUMN notice.bssamtOpenDt IS '기초금액공개일시';
COMMENT ON COLUMN notice.rsrvtnPrceRngBgnRate IS '예비가격범위시작률';
COMMENT ON COLUMN notice.rsrvtnPrceRngEndRate IS '예비가격범위종료율';
COMMENT ON COLUMN notice.evlBssAmt IS '평가기준금액';
COMMENT ON COLUMN notice.dfcltydgrCfcnt IS '난이도계수';
COMMENT ON COLUMN notice.etcGnrlexpnsBssRate IS '기타경비기준율';
COMMENT ON COLUMN notice.gnrlMngcstBssRate IS '일반관리비기준율';
COMMENT ON COLUMN notice.prftBssRate IS '이윤기준율';
COMMENT ON COLUMN notice.lbrcstBssRate IS '노무비기준율';
COMMENT ON COLUMN notice.sftyMngcst IS '산업안전보건관리비';
COMMENT ON COLUMN notice.rtrfundNon IS '퇴직공제부금비';
COMMENT ON COLUMN notice.envCnsrvcst IS '환경보전비';
COMMENT ON COLUMN notice.scontrctPayprcePayGrntyFee IS '하도급대금지급보증수수료';
COMMENT ON COLUMN notice.mrfnHealthInsrprm IS '국민건강보험료';
COMMENT ON COLUMN notice.npnInsrprm IS '국민연금보험료';
COMMENT ON COLUMN notice.rmrk1 IS '비고1';
COMMENT ON COLUMN notice.rmrk2 IS '비고2';
COMMENT ON COLUMN notice.odsnLngtrmrcprInsrprm IS '노인장기요양보험료';
COMMENT ON COLUMN notice.usefulAmt IS '가용금액';
COMMENT ON COLUMN notice.inptDt IS '입력일시';
COMMENT ON COLUMN notice.sftyChckMngcst IS '안전관리비';
COMMENT ON COLUMN notice.bidPrceCalclAYn IS '입찰가격산식A여부';
COMMENT ON COLUMN notice.bssAmtPurcnstcst IS '기초금액순공사비';
COMMENT ON COLUMN notice.qltyMngcst IS '품질관리비';
COMMENT ON COLUMN notice.qltyMngcstAObjYn IS '품질관리비A적용대상여부';
--- 공고 낙찰 오퍼레이션(기개찰)
---------------------------------------------------------------------
COMMENT ON COLUMN notice.fnlSucsfAmt IS '최종낙찰금액';
COMMENT ON COLUMN notice.fnlSucsfRt IS '최종낙찰률';
COMMENT ON COLUMN notice.fnlSucsfDate IS '최종낙찰일자';
COMMENT ON COLUMN notice.fnlSucsfCorpNm IS '최종낙찰업체명';
COMMENT ON COLUMN notice.fnlSucsfCorpCeoNm IS '최종낙찰업체대표자명';
COMMENT ON COLUMN notice.fnlSucsfCorpOfclNm IS '최종낙찰업체담당자명';
COMMENT ON COLUMN notice.fnlSucsfCorpBizrno IS '최종낙찰업체사업자번호';
COMMENT ON COLUMN notice.fnlSucsfCorpAdrs IS '최종낙찰업체주소';
COMMENT ON COLUMN notice.fnlSucsfCorpContactTel IS '최종낙찰업체전화번호';

COMMENT ON COLUMN notice.cntrctCnclsSttusNm IS '계약체결상태명';
COMMENT ON COLUMN notice.bidwinrDcsnMthdNm IS '낙찰자결정방법명';