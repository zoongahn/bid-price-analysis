import matplotlib.pyplot as plt
import os
import pandas as pd
import random

def plot_histogram(csv_paths, df):
    try:
        # Get filename without extension for saving
        # Create output directory if it doesn't exist
        filename = os.path.splitext(os.path.basename(csv_paths))[0]
        output_dir = f"{filename}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # Extract numeric values from the string format
        df['기초대비사정률'] = df['기초대비 사정률(%)  A'].str.extract(r'(-?\d+\.\d+)')[0].astype(float)
        
        # Plot histograms with different bin sizes
        bins = [50, 100, 200, 500]
        colors = ['red', 'orange', 'blue', 'green']
        range_min = -2.5
        range_max = 2.5
        for j, num_bins in enumerate(bins):
            # Create figure for this CSV
            fig, ax = plt.subplots(figsize=(10, 6))
            # Create figure for this CSV
            # Calculate scaled data
            scaled_data = df['기초대비사정률']
            
            if j == 0:  # Only plot the first histogram normally
                ax.hist(scaled_data, bins=num_bins, alpha=0.3, 
                        label=f'scale={num_bins/100}x (bins={num_bins})',
                        range=(range_min, range_max), color=colors[j])
            else:  # Stack subsequent histograms
                ax.hist(scaled_data, bins=num_bins, alpha=0.3, 
                        label=f'scale={num_bins/100}x (bins={num_bins})',
                        range=(range_min, range_max ), color=colors[j])
                    
            ax.set_xlim(range_min, range_max)
            ax.set_title(f'Distribution for {filename}')
            ax.set_xlabel('기초대비사정률')
            ax.set_ylabel('Frequency')
            ax.legend()
            
            plt.tight_layout()
            
            # Save figure
            save_path = os.path.join(output_dir, f'{num_bins}_histogram.png')
            plt.savefig(save_path)
            plt.close()
        
    except Exception as e:
        print(f"Error processing file {i+1}: {e}")

def simulate(n, seed=42):
    random.seed(seed)

    # 1~8 번: -0.03 ~ 0.0 까지 8등분
    # 9~15번: 0.0 ~ 0.03 까지 7등분
    ranges = []

    # 1~8
    neg_start, neg_end = -0.03, 0.0
    neg_step = (neg_end - neg_start) / 8.0
    for i in range(1, 9):
        low = neg_start + (i-1)*neg_step
        high = neg_start + i*neg_step
        ranges.append((low, high))

    # 9~15
    pos_start, pos_end = 0.0, 0.03
    pos_step = (pos_end - pos_start) / 7.0
    for i in range(9, 16):
        j = i - 9
        low = pos_start + j*pos_step
        high = pos_start + (j+1)*pos_step
        ranges.append((low, high))

    results = []
    for _ in range(n):
        # 15개 중 4개 랜덤 추출
        chosen_indices = random.sample(range(15), 4)

        # 각 선택된 인덱스에 해당하는 범위 내의 랜덤 값
        values = []
        for idx in chosen_indices:
            low, high = ranges[idx]
            val = random.uniform(low, high)
            values.append(val)

        # 평균 계산
        avg_val = sum(values) * 25.0
        results.append(avg_val)

    return results

def preprocess_data(basic_info_df, csv_dir_path):
    """
    basic_info_df 의 각 공고번호를 기준으로,
    1) 참여업체수가 100 이상이고 예가범위가 '+3% ~ -3%' 인 경우에만
    2) 해당 공고번호와 동일한 이름의 CSV 파일을 csv_dir_path에서 읽어
    3) '기초대비 사정률(%)  A' 칼럼에서 앞부분 (예: -0.95811 (99.04189) 중 -0.95811)을 float로 파싱
    4) 파싱된 값을 -3~+3 구간으로 나누어 각각 10, 20, 50, 100개의 bin에 대해 히스토그램(총 180개 bin)을 계산
    5) hist 결과(각 bin count)를 기본 DataFrame(basic_info_df)에 새로운 컬럼(예: 010_001, 010_002, ..., 100_100)으로 추가
    6) 가공 완료된 DataFrame 을 반환
    
    Parameters
    ----------
    basic_info_df : pd.DataFrame
        '공고번호', '참여업체수', '예가범위' 등을 포함하는 DataFrame
    csv_dir_path : str
        공고번호에 해당하는 csv 파일들이 저장된 디렉토리 경로

    Returns
    -------
    pd.DataFrame
        기존의 basic_info_df에 180개 히스토그램 bin count 컬럼이 추가된 DataFrame.
        (조건에 맞지 않는 row에 대해서는 bin 값이 모두 0 또는 NaN이 들어갈 수 있음)
    """
    import os
    import re
    import numpy as np
    import pandas as pd

    # 기본 컬럼들로 빈 DataFrame 생성
    filtered_df = pd.DataFrame(columns=basic_info_df.columns)
    
    # 모든 bin 컬럼들을 미리 준비
    bin_list = [10, 20, 50, 100]
    bin_columns = {}
    for bc in bin_list:
        for i in range(bc):
            col_name = f"{bc:03}_{i+1:03}"
            bin_columns[col_name] = 0
    
    # 한 번에 모든 컬럼 추가
    for col, value in bin_columns.items():
        filtered_df[col] = value

    # 각 row를 순회하며 조건 만족 시 CSV 파일 처리
    rows_list = []  # 새로운 row들을 저장할 리스트

    for idx, row in basic_info_df.iterrows():
        참여업체수 = row.get('참여업체수', 0)
        예가범위 = row.get('예가범위', '')
        공고번호 = str(row.get('공고번호', ''))

        # 조건 체크: 참여업체수 >= 100 AND 예가범위 == '+3% ~ -3%'
        if (참여업체수 >= 100) and (예가범위 == '+3% ~ -3%'):
            csv_file_path = os.path.join(csv_dir_path, f"{공고번호}.csv")
            if not os.path.isfile(csv_file_path):
                continue

            try:
                df_csv = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False)
                if '기초대비 사정률(%)  A' not in df_csv.columns:
                    continue

                df_csv['parsed_rate'] = (
                    df_csv['기초대비 사정률(%)  A']
                    .astype(str)
                    .str.extract(r'(-?\d+\.\d+)')[0]
                    .astype(float, errors='ignore')
                )
                
                parsed_data = df_csv['parsed_rate'].dropna()
                if len(parsed_data) == 0:
                    continue

                # 새로운 row 데이터 준비
                new_row = row.to_dict()
                
                # histogram 계산 및 컬럼 추가
                for bc in bin_list:
                    bin_edges = np.linspace(-3.0, 3.0, bc + 1)
                    hist_counts, _ = np.histogram(parsed_data, bins=bin_edges)
                    
                    for i in range(bc):
                        col_name = f"{bc:03}_{i+1:03}"
                        new_row[col_name] = hist_counts[i]
                
                # 리스트에 새로운 row 추가
                rows_list.append(new_row)

            except Exception as e:
                print(f"Error processing file {공고번호}: {str(e)}")
                continue

    # 모든 row를 한 번에 DataFrame으로 변환
    if rows_list:
        filtered_df = pd.DataFrame(rows_list)

    return filtered_df