-- 002_add_bizstt_status_columns.sql
-- company 테이블에 국세청 사업자등록 상태조회 결과 컬럼 추가

-- 컬럼 추가
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_b_stt TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_b_stt_cd TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_tax_type TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_tax_type_cd TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_end_dt DATE;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_utcc_yn TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_tax_type_change_dt DATE;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_invoice_apply_dt DATE;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_rbf_tax_type TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_rbf_tax_type_cd TEXT;
ALTER TABLE data.company ADD COLUMN IF NOT EXISTS bizstt_status_updated_at TIMESTAMPTZ;

-- 컬럼 주석
COMMENT ON COLUMN data.company.bizstt_b_stt IS '국세청 납세자상태 (계속사업자/휴업자/폐업자)';
COMMENT ON COLUMN data.company.bizstt_b_stt_cd IS '국세청 납세자상태 코드 (01/02/03)';
COMMENT ON COLUMN data.company.bizstt_tax_type IS '국세청 과세유형 명칭';
COMMENT ON COLUMN data.company.bizstt_tax_type_cd IS '국세청 과세유형 코드';
COMMENT ON COLUMN data.company.bizstt_end_dt IS '국세청 폐업일';
COMMENT ON COLUMN data.company.bizstt_utcc_yn IS '국세청 단위과세전환폐업여부 (Y/N)';
COMMENT ON COLUMN data.company.bizstt_tax_type_change_dt IS '국세청 최근과세유형전환일자';
COMMENT ON COLUMN data.company.bizstt_invoice_apply_dt IS '국세청 세금계산서적용일자';
COMMENT ON COLUMN data.company.bizstt_rbf_tax_type IS '국세청 직전과세유형 명칭';
COMMENT ON COLUMN data.company.bizstt_rbf_tax_type_cd IS '국세청 직전과세유형 코드';
COMMENT ON COLUMN data.company.bizstt_status_updated_at IS '국세청 상태 조회 시각';

-- 인덱스 (폐업자 필터링용)
CREATE INDEX IF NOT EXISTS idx_company_bizstt_b_stt_cd ON data.company(bizstt_b_stt_cd);
