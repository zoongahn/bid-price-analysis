import os
from openai import OpenAI
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import argparse
from tqdm import tqdm  # 진행 상황 표시를 위한 라이브러리


def generate_data_catalog_with_chatgpt_v2(csv_path: str, openai_api_key: str, model: str = "gpt-4"):
    """
    최신 OpenAI SDK를 사용하여 CSV 파일의 데이터를 분석하고 카탈로그를 생성하는 함수.
    ChatGPT API를 활용하여 데이터 컬럼별 분석 내용을 요약 및 설명.

    Parameters:
    -----------
    csv_path : str
        입력 CSV 파일 경로.
    openai_api_key : str
        OpenAI API Key.
    model : str
        사용할 OpenAI 모델 이름. 기본값은 "gpt-4".

    Returns:
    --------
    None
        분석 결과를 엑셀 파일로 저장.
    """
    
    # OpenAI API Key 설정
    client = OpenAI(api_key=openai_api_key)

    # 1. CSV 파일 로드
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"CSV 파일 로드 실패: {e}")
        return

    total_columns = len(df.columns)  # 전체 컬럼 개수
    print(f"총 {total_columns}개의 컬럼을 분석합니다...")

    # 2. 데이터 카탈로그 생성
    catalog_data = []
    for col in df.columns:
        col_info = {
            "Column Name": col,
            "Data Type": str(df[col].dtype),
            "Unique Count": df[col].nunique(),
            "Missing Count": df[col].isnull().sum(),
            "Min Value": df[col].min() if pd.api.types.is_numeric_dtype(df[col]) else None,
            "Max Value": df[col].max() if pd.api.types.is_numeric_dtype(df[col]) else None,
            "Sample Values": df[col].dropna().sample(min(3, len(df[col].dropna())), random_state=42).tolist()
        }
        catalog_data.append(col_info)

    catalog_df = pd.DataFrame(catalog_data)

    # 3. ChatGPT를 활용한 분석 요청
    analysis_results = []
    print("ChatGPT를 사용하여 컬럼을 분석합니다...")
    for col_info in tqdm(catalog_data, desc="진행 상황", unit="column"):
        prompt = f"""
        Here is information about the column "{col_info['Column Name']}":
        - Data Type: {col_info['Data Type']}
        - Unique Values: {col_info['Unique Count']}
        - Missing Values: {col_info['Missing Count']}
        - Min Value: {col_info['Min Value']}
        - Max Value: {col_info['Max Value']}
        - Sample Data: {col_info['Sample Values']}

        Based on this information, summarize the possible meaning of this column
        in 2-3 descriptive words. Keep the response brief and concise.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a skilled data analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            # 응답 내용 추출 방식 수정
            gpt_output = response.choices[0].message.content.strip()
            gpt_output_short = " ".join(gpt_output.split()[:3])  # 첫 2~3 단어로 제한
        except Exception as e:
            gpt_output_short = f"Error: {e}"

        analysis_results.append({
            "Column Name": col_info["Column Name"],
            "Prompt": prompt,
            "GPT-4 Analysis (Short)": gpt_output_short
        })

    analysis_df = pd.DataFrame(analysis_results)

    # 4. 결과 저장
    today_str = datetime.now().strftime("%Y%m%d")
    base_name = os.path.basename(csv_path)
    file_root, _ = os.path.splitext(base_name)
    output_path = f"{file_root}_catalog_{today_str}.xlsx"

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        catalog_df.to_excel(writer, sheet_name="Catalog", index=False)
        analysis_df.to_excel(writer, sheet_name="GPT Analysis", index=False)

    print(f"Catalog and analysis saved to {output_path}")


# ===== 실행 예시 =====
if __name__ == "__main__":
    # 사용자 설정
    parser = argparse.ArgumentParser(description="Generate a data catalog and analysis using OpenAI GPT.")
    parser.add_argument("csv_path", type=str, help="Path to the input CSV file.")
    args = parser.parse_args()
    csv_file_path = args.csv_path
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # 실행
    generate_data_catalog_with_chatgpt_v2(csv_path=csv_file_path, openai_api_key=OPENAI_API_KEY)