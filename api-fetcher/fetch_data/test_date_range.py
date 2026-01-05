"""
특정 기간 수집 기능 테스트 스크립트
실제 API 호출 없이 DataCollector 초기화 및 파라미터 전달만 테스트
"""
from src.data_collector import DataCollector

def test_date_range_initialization():
    """특정 기간 파라미터가 제대로 초기화되는지 테스트"""

    print("=" * 60)
    print("테스트 1: 특정 기간 수집 모드 (start_date, end_date)")
    print("=" * 60)

    try:
        collector = DataCollector(
            service_name="입찰공고정보서비스",
            operation_number=1,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        print(f"✓ start_date: {collector.start_date}")
        print(f"✓ end_date: {collector.end_date}")
        print(f"✓ executed_year: {collector.executed_year}")
        print(f"✓ service_name: {collector.service_name}")
        print(f"✓ operation_number: {collector.operation_number}")
        print("\n테스트 1 통과!\n")

    except Exception as e:
        print(f"✗ 테스트 1 실패: {e}\n")
        return False

    print("=" * 60)
    print("테스트 2: 특정 연도 수집 모드 (year)")
    print("=" * 60)

    try:
        collector = DataCollector(
            service_name="입찰공고정보서비스",
            operation_number=1,
            year="2023"
        )

        print(f"✓ start_date: {collector.start_date}")
        print(f"✓ end_date: {collector.end_date}")
        print(f"✓ executed_year: {collector.executed_year}")
        print(f"✓ service_name: {collector.service_name}")
        print(f"✓ operation_number: {collector.operation_number}")
        print("\n테스트 2 통과!\n")

    except Exception as e:
        print(f"✗ 테스트 2 실패: {e}\n")
        return False

    print("=" * 60)
    print("테스트 3: 우선순위 확인 (start_date/end_date가 year보다 우선)")
    print("=" * 60)

    try:
        collector = DataCollector(
            service_name="입찰공고정보서비스",
            operation_number=1,
            year="2023",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        print(f"✓ start_date: {collector.start_date} (should be 2024-01-01)")
        print(f"✓ end_date: {collector.end_date} (should be 2024-01-31)")
        print(f"✓ executed_year: {collector.executed_year} (should be 2023)")

        assert collector.start_date == "2024-01-01", "start_date 불일치"
        assert collector.end_date == "2024-01-31", "end_date 불일치"

        print("\n테스트 3 통과!\n")

    except Exception as e:
        print(f"✗ 테스트 3 실패: {e}\n")
        return False

    print("=" * 60)
    print("모든 테스트 통과! ✓")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_date_range_initialization()
