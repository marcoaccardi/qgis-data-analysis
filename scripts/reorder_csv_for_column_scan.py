import pandas as pd
import os

# Base output directory containing all datasets
base_output_dir = os.path.join(os.path.dirname(__file__), '../output')

# Loop over each dataset folder in the output directory
for dataset_name in os.listdir(base_output_dir):
    dataset_path = os.path.join(base_output_dir, dataset_name)
    if not os.path.isdir(dataset_path):
        continue
    csv_path = os.path.join(dataset_path, 'combined_time_series.csv')
    output_csv_path = os.path.join(dataset_path, 'combined_time_series_columnwise.csv')
    if not os.path.exists(csv_path):
        print(f"No combined_time_series.csv found in {dataset_path}, skipping.")
        continue
    # Load, sort, and save
    df = pd.read_csv(csv_path)
    df_sorted = df.sort_values(by=['X', 'Y'])
    df_sorted.to_csv(output_csv_path, index=False)
    print(f"Reordered CSV saved to {output_csv_path}")
