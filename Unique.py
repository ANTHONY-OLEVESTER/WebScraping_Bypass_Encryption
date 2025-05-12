import pandas as pd

# Define input and output file paths
input_file = r"D:\2Frelance\freelanceC6\Reults\Output SemiFinal.xlsx"
output_file = r"D:\2Frelance\freelanceC6\Reults\uniques.xlsx"

# Load the input Excel
df = pd.read_excel(input_file)

# Check if we have at least 3 columns
if df.shape[1] < 3:
    raise Exception("The input file does not have a third column!")

# Drop duplicate rows based on the 3rd column (index 2)
df_unique = df.drop_duplicates(df)

# Save to output
df_unique.to_excel(output_file, index=False)

print(f"✅ Unique rows based on company links saved to {output_file}!")
