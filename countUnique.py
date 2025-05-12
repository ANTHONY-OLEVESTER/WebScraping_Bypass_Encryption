import pandas as pd

input_file = r"D:\2Frelance\freelanceC6\Reults\Output SemiFinal.xlsx"
output_file = r"D:\2Frelance\freelanceC6\Reults\uniques.xlsx"

# Read the Excel file
df = pd.read_excel(input_file)

# Get the name of column 3 (assuming it's the 3rd column)
col3_name = df.columns[2]

# Count duplicates and store in new column
df['Duplicate Count'] = df.groupby(col3_name)[col3_name].transform('count')

# Save the modified DataFrame
df.to_excel(output_file, index=False)

print(f"Duplicate counts added in new column. Saved to {output_file}")