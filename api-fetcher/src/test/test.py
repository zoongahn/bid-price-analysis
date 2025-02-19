from src.logger import setup_loggers

# ✅ 로그 설정 실행
loggers = setup_loggers()

# ✅ 사용 예시 (커스텀 레벨 적용)
loggers["application"].year("========== 2025년도 데이터 수집 시작 ==========")
loggers["application"].fetch("이것은 일반 fetch 로그입니다.")
loggers["day"].warning("이것은 WARNING 로그입니다.")
loggers["day"].day("이것은 day 로그입니다.")
loggers["year"].year("2025년도 데이터 수집이 완료되었습니다.")
loggers["application"].error("이것은 ERROR 로그입니다.")
