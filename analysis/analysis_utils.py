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

def get_csv_files(basic_info_df, csv_dir_path):
    """
    basic_info_df의 공고번호에 해당하는 CSV 파일들을 찾아서 반환합니다.
    
    Parameters
    ----------
    basic_info_df : pd.DataFrame
        '공고번호'를 포함하는 DataFrame
    csv_dir_path : str
        CSV 파일들이 저장된 디렉토리 경로
        
    Returns
    -------
    dict
        {공고번호: 파일경로} 형태의 딕셔너리
    """
    csv_files = {}
    not_found = []
    
    for idx, row in basic_info_df.iterrows():
        공고번호 = str(row.get('공고번호', ''))
        csv_file_path = os.path.join(csv_dir_path, f"{공고번호}.csv")
        
        if os.path.isfile(csv_file_path):
            csv_files[공고번호] = csv_file_path
        else:
            not_found.append(공고번호)
    
    # 결과 출력
    print(f"총 공고 수: {len(basic_info_df)}")
    print(f"찾은 CSV 파일 수: {len(csv_files)}")
    print(f"찾지 못한 파일 수: {len(not_found)}")
    
    if len(not_found) > 0:
        print("\n처음 5개 찾지 못한 공고번호:")
        print(not_found[:5])
        
    return csv_files

def validate_histogram_data(result_df, csv_dir_path):
    """
    히스토그램 데이터의 유효성을 검증합니다.
    """
    # 1. 히스토그램 bin 컬럼 식별
    bin_columns = [col for col in result_df.columns if col.startswith(('010_', '020_', '050_', '100_'))]
    
    # 2. 각 row의 히스토그램 합계가 0인 경우 찾기
    hist_sums = result_df[bin_columns].sum(axis=1)
    zero_rows = hist_sums == 0
    problematic_rows = result_df[zero_rows]
    
    if len(problematic_rows) > 0:
        print(f"\n경고: {len(problematic_rows)}개의 행에서 모든 히스토그램 bin이 0입니다.")
        
        # 문제가 있는 행들의 상세 정보 출력
        for idx, row in problematic_rows.iterrows():
            print(f"\n문제 발견된 행 #{idx}")
            print(f"공고번호: {row['공고번호']}")
            print(f"참여업체수: {row['참여업체수']}")
            
            # 원본 CSV 파일 확인
            csv_path = os.path.join(csv_dir_path, f"{row['공고번호']}.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                print(f"원본 파일 행 수: {len(df)}")
                print("사용 가능한 컬럼:", df.columns.tolist())
                
                # 사정률 데이터 샘플 확인
                rate_columns = [col for col in df.columns if '사정률' in col]
                if rate_columns:
                    print("\n사정률 데이터 샘플:")
                    for col in rate_columns:
                        print(f"\n{col}:")
                        print(df[col].head())
        
        return False
    
    return True

def preprocess_datas(basic_info_df, csv_dir_path, percent_range = '+3% ~ -3%'):
    """
    CSV 파일들을 처리하여 히스토그램 데이터를 생성합니다.
    """
    if percent_range == '+3% ~ -3%':
        max_percent = 3
    elif percent_range == '+2% ~ -2%':
        max_percent = 2


    # 1. CSV 파일 찾기
    csv_files = get_csv_files(basic_info_df, csv_dir_path)
    if not csv_files:
        print("처리할 CSV 파일이 없습니다.")
        return None

    # 2. 기본 DataFrame 및 bin 설정 준비
    bin_list = [10, 20, 50, 100]
    
    # bin 컬럼들을 위한 빈 DataFrame 생성
    bin_dfs = []
    for bc in bin_list:
        columns = [f"{bc:03}_{i+1:03}" for i in range(bc)]
        temp_df = pd.DataFrame(0, index=np.arange(len(basic_info_df)), columns=columns)
        bin_dfs.append(temp_df)
    
    # 모든 DataFrame을 한 번에 결합
    filtered_df = pd.concat(
        [basic_info_df] + bin_dfs, 
        axis=1
    ).copy()  # copy()를 통해 메모리 최적화

    # 3. 데이터 처리
    rows_list = []
    processed_count = 0
    error_count = 0

    for idx, row in basic_info_df.iterrows():
        공고번호 = str(row.get('공고번호', ''))
        
        # 1. CSV 파일 존재 확인
        assert 공고번호 in csv_files, f"CSV 파일을 찾을 수 없음: {공고번호}"
        
        참여업체수 = row.get('참여업체수', 0)
        예가범위 = row.get('예가범위', '')

        # 2. 기본 조건 확인
        if not ((참여업체수 >= 100) and (예가범위 == percent_range)):
            error_count += 1
            continue

        # 3. CSV 파일 읽기 및 컬럼 확인
        df_csv = pd.read_csv(csv_files[공고번호], encoding='utf-8', low_memory=False)
        
        # 4. 사정률 컬럼 확인 및 데이터 파싱
        rate_column = None
        for col in ['기초대비 사정률(%)  A', '기초대비 사정률(%)', '순공사대비 사정률(%)']:
            if col in df_csv.columns:
                rate_column = col
                break
        
        assert rate_column is not None, f"사정률 컬럼을 찾을 수 없음: {공고번호}"
        
        try:
            parsed_rates = (
                df_csv[rate_column]
                .astype(str)
                .str.extract(r'(-?\d+\.\d+)')[0]
                .astype(float)
            )
            
            # 5. 파싱된 데이터 검증
            assert not parsed_rates.empty, f"파싱된 데이터가 비어있음: {공고번호}"
            assert parsed_rates.notna().any(), f"유효한 사정률 데이터가 없음: {공고번호}"
            
            parsed_data = parsed_rates.dropna()
            
            # 6. 히스토그램 계산 및 검증
            new_row = row.to_dict()
            for bc in bin_list:
                bin_edges = np.linspace(-max_percent, max_percent, bc + 1)
                hist_counts, _ = np.histogram(parsed_data, bins=bin_edges)
                
                # 히스토그램이 모두 0인지 확인
                assert hist_counts.sum() > 0, f"히스토그램이 모두 0임: {공고번호}"
                
                for i in range(bc):
                    col_name = f"{bc:03}_{i+1:03}"
                    new_row[col_name] = hist_counts[i]
            
            rows_list.append(new_row)
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {공고번호}: {str(e)}")
            error_count += 1
            continue

    # 7. 최종 결과 생성 및 검증
    if rows_list:
        result_df = pd.DataFrame(rows_list)
        
        # 결과 데이터 검증
        is_valid = validate_histogram_data(result_df, csv_dir_path)
        if not is_valid:
            print("경고: 결과 데이터에 문제가 있습니다.")
        
        return result_df
    else:
        return None

def merge_csv_files(csv_dir_path):
    count = 0
    csv_paths = glob.glob(os.path.join(csv_dir_path, "*.csv"))
    df = pd.read_csv(csv_paths[0])
    for i in range(1, len(csv_paths)):
        concat_df = pd.read_csv(csv_paths[i])
        if len(concat_df) > 100:
            count += 1
            df = pd.concat([df, concat_df], ignore_index=True)
    print(count)
    return df

