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