"""
업종 정보 CSV 데이터를 PostgreSQL에 삽입하는 스크립트

1. 20251110_1157_notice_industry_type_info.csv: 최신 데이터 (우선 삽입)
2. 20100511_notice_industry_type_info.csv: 구 데이터 (PK 중복 시 SKIP)
"""
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import date

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_psql import init_psql
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_table(cursor, conn):
    """테이블 생성"""
    create_table_sql_path = project_root / "sync_data" / "create" / "notice_industry_type_info.sql"
    logger.info(f"테이블 생성 SQL 실행: {create_table_sql_path}")

    with open(create_table_sql_path, 'r', encoding='utf-8') as f:
        create_table_sql = f.read()
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("테이블 생성 완료")


def insert_latest_data(cursor, conn, csv_file_path: str):
    """
    최신 데이터 삽입 (20251110_1157_notice_industry_type_info.csv)

    ON CONFLICT DO UPDATE: 중복 시 업데이트
    """
    logger.info("=" * 80)
    logger.info("Step 1: 최신 데이터 삽입")
    logger.info("=" * 80)
    logger.info(f"파일: {csv_file_path}")

    # CSV 읽기
    df = pd.read_csv(
        csv_file_path,
        encoding='utf-8-sig',
        dtype={
            '분류코드': str,
            '업종코드': str
        }
    )

    logger.info(f"총 {len(df)}개의 레코드를 읽었습니다.")

    insert_sql = """
        INSERT INTO notice_industry_type_info (
            industry_code,
            classification_code,
            classification_name,
            industry_name,
            legal_basis,
            related_regulations,
            last_modified_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (industry_code) DO UPDATE SET
            classification_code = EXCLUDED.classification_code,
            classification_name = EXCLUDED.classification_name,
            industry_name = EXCLUDED.industry_name,
            legal_basis = EXCLUDED.legal_basis,
            related_regulations = EXCLUDED.related_regulations,
            last_modified_date = EXCLUDED.last_modified_date
    """

    insert_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        try:
            # 날짜 변환
            last_modified = pd.to_datetime(row['최종변경일시']).date() if pd.notna(row['최종변경일시']) else None

            cursor.execute(insert_sql, (
                str(row['업종코드']) if pd.notna(row['업종코드']) else None,
                str(row['분류코드']) if pd.notna(row['분류코드']) else None,
                str(row['업종분류명']) if pd.notna(row['업종분류명']) else None,
                str(row['업종명']) if pd.notna(row['업종명']) else None,
                str(row['근거법령']) if pd.notna(row['근거법령']) else None,
                str(row['관련규정']) if pd.notna(row['관련규정']) else None,
                last_modified
            ))
            insert_count += 1

            if insert_count % 100 == 0:
                conn.commit()
                logger.info(f"진행 중... {insert_count}/{len(df)}")

        except Exception as e:
            error_count += 1
            logger.error(f"행 {idx} 삽입 실패: {e}")
            continue

    conn.commit()
    logger.info(f"✅ 최신 데이터 삽입 완료: 성공 {insert_count}개, 실패 {error_count}개")

    return insert_count, error_count


def insert_old_data_if_not_exists(cursor, conn, csv_file_path: str):
    """
    구 데이터 삽입 (20100511_notice_industry_type_info.csv)

    ON CONFLICT DO NOTHING: PK 중복 시 SKIP
    last_modified_date는 2010-05-11로 고정
    """
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: 구 데이터 삽입 (PK 중복 시 SKIP)")
    logger.info("=" * 80)
    logger.info(f"파일: {csv_file_path}")

    # CSV 읽기 (컬럼명이 다름)
    df = pd.read_csv(
        csv_file_path,
        encoding='utf-8-sig',
        dtype={
            '분류코드': str,
            '업종코드': str
        }
    )

    logger.info(f"총 {len(df)}개의 레코드를 읽었습니다.")

    insert_sql = """
        INSERT INTO notice_industry_type_info (
            industry_code,
            classification_code,
            classification_name,
            industry_name,
            legal_basis,
            related_regulations,
            last_modified_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (industry_code) DO NOTHING
    """

    insert_count = 0
    skip_count = 0
    error_count = 0

    # 고정 날짜
    fixed_date = date(2010, 5, 11)

    for idx, row in df.iterrows():
        try:
            cursor.execute(insert_sql, (
                str(row['업종코드']) if pd.notna(row['업종코드']) else None,
                str(row['분류코드']) if pd.notna(row['분류코드']) else None,
                str(row['업종분류명']) if pd.notna(row['업종분류명']) else None,
                str(row['업종명']) if pd.notna(row['업종명']) else None,
                str(row['근거법령']) if pd.notna(row['근거법령']) else None,
                str(row['관련규정']) if pd.notna(row['관련규정']) else None,
                fixed_date
            ))

            # rowcount로 실제 삽입 여부 확인
            if cursor.rowcount > 0:
                insert_count += 1
            else:
                skip_count += 1

            if (insert_count + skip_count) % 100 == 0:
                conn.commit()
                logger.info(f"진행 중... 삽입: {insert_count}, SKIP: {skip_count}/{len(df)}")

        except Exception as e:
            error_count += 1
            logger.error(f"행 {idx} 처리 실패: {e}")
            continue

    conn.commit()
    logger.info(f"✅ 구 데이터 처리 완료: 신규 삽입 {insert_count}개, SKIP {skip_count}개, 실패 {error_count}개")

    return insert_count, skip_count, error_count


def main():
    """메인 함수"""
    logger.info("\n" + "=" * 80)
    logger.info("업종 정보 데이터 삽입 스크립트")
    logger.info("=" * 80)

    # 파일 경로 설정
    data_dir = project_root / "data"
    latest_csv = data_dir / "20251110_1157_notice_industry_type_info.csv"
    old_csv = data_dir / "20100511_notice_industry_type_info.csv"

    # 파일 존재 확인
    if not latest_csv.exists():
        logger.error(f"최신 CSV 파일을 찾을 수 없습니다: {latest_csv}")
        sys.exit(1)

    if not old_csv.exists():
        logger.error(f"구 CSV 파일을 찾을 수 없습니다: {old_csv}")
        sys.exit(1)

    server = None
    conn = None

    try:
        # PostgreSQL 연결
        logger.info("PostgreSQL 연결 중...")
        server, conn = init_psql()
        cursor = conn.cursor()

        # 테이블 생성
        create_table(cursor, conn)

        # Step 1: 최신 데이터 삽입
        latest_insert, latest_error = insert_latest_data(cursor, conn, str(latest_csv))

        # Step 2: 구 데이터 삽입 (중복 SKIP)
        old_insert, old_skip, old_error = insert_old_data_if_not_exists(cursor, conn, str(old_csv))

        # 최종 결과
        logger.info("\n" + "=" * 80)
        logger.info("최종 결과")
        logger.info("=" * 80)

        cursor.execute("SELECT COUNT(*) FROM notice_industry_type_info")
        total_count = cursor.fetchone()[0]
        logger.info(f"테이블 총 레코드 수: {total_count:,}")

        logger.info(f"\n📊 삽입 통계:")
        logger.info(f"  - 최신 데이터: {latest_insert:,}개 삽입, {latest_error}개 실패")
        logger.info(f"  - 구 데이터: {old_insert:,}개 신규 삽입, {old_skip:,}개 SKIP, {old_error}개 실패")
        logger.info(f"  - 총 신규 삽입: {latest_insert + old_insert:,}개")

        # 샘플 데이터 조회
        cursor.execute("""
            SELECT industry_code, classification_name, industry_name, last_modified_date
            FROM notice_industry_type_info
            ORDER BY last_modified_date DESC
            LIMIT 5
        """)
        sample_data = cursor.fetchall()
        logger.info("\n📋 샘플 데이터 (최신순 5개):")
        for row in sample_data:
            logger.info(f"  코드: {row[0]}, 분류: {row[1]}, 업종: {row[2]}, 수정일: {row[3]}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 스크립트 실행 완료!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            logger.info("PostgreSQL 연결 종료")
        if server:
            server.stop()
            logger.info("SSH 터널 종료")


if __name__ == "__main__":
    main()
