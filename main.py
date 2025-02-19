import pandas as pd
from datetime import datetime

# Function to parse allocation description and identify term/non-term times
def parse_allocation_description(description):
    hours, rate = description.split(" x ")
    hours = int(float(hours.split()[0]))  # Convert to float first and then to int
    rate = float(rate.replace("€", ""))
    return hours, rate

# Identify term and non-term times
def identify_term_non_term_times(hours_list):
    hours_list = sorted(set(hours_list))  # Remove duplicates and sort
    if len(hours_list) == 1:
        return str(hours_list[0])
    
    # Group hours into term/non-term pairs
    pairs = []
    used = set()
    for i in range(len(hours_list)):
        for j in range(i + 1, len(hours_list)):
            if abs(hours_list[j] - hours_list[i]) in [9, 12, 15] and hours_list[i] not in used and hours_list[j] not in used:
                pairs.append((hours_list[i], hours_list[j]))
                used.add(hours_list[i])
                used.add(hours_list[j])

    # If there are pairs, format them
    if pairs:
        pairs_str = [f"{pair[0]}/{pair[1]}" for pair in pairs]
        return ", ".join(pairs_str)

    # If no pairs, format as changing hours
    remaining_hours = [str(hour) for hour in hours_list if hour not in used]
    return "-".join(remaining_hours)

# Read the input data from an Excel file
input_file = "funding_data.xlsx"
df = pd.read_excel(input_file)

# Transform the data
transformed_data = []

for index, row in df.iterrows():
    child_name = row["Child"]
    allocation_date = datetime.strptime(row["Allocation Date"], "%d/%m/%Y")
    month = allocation_date.strftime("%b")
    hours, rate = parse_allocation_description(row["Allocation Description"])
    allocation_value = row["Allocation Value"]
    
    transformed_data.append({
        "Child Name": child_name,
        "Month": month,
        "Hours": hours,
        "Rate": rate,
        "Allocation Value": allocation_value,
        "Allocation Date": allocation_date
    })

# Create DataFrame for transformed data
transformed_df = pd.DataFrame(transformed_data)

# Group by child and month and summarize allocation values and hours
grouped = transformed_df.groupby(["Child Name", "Month"]).agg({
    "Allocation Value": "sum",
    "Hours": list,
    "Rate": list,
    "Allocation Date": list
}).reset_index()

# Initialize the final output DataFrame
months = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
output_columns = ["Name", "Term/Non-Term/Changes", "Allocation Value"] + months
output_df = pd.DataFrame(columns=output_columns)

# Populate the final output DataFrame
for name, group in grouped.groupby("Child Name"):
    hours_info = identify_term_non_term_times(group["Hours"].explode().tolist())
    allocation_value = group["Allocation Value"].sum()
    row = {
        "Name": name,
        "Term/Non-Term/Changes": hours_info,
        "Allocation Value": f"€{allocation_value:.2f}"
    }
    for month in months:
        if month in group["Month"].values:
            row[month] = f"€{group[group['Month'] == month]['Allocation Value'].values[0]:.2f}"
        else:
            row[month] = ""
    output_df = pd.concat([output_df, pd.DataFrame([row])], ignore_index=True)

# Export to Excel
output_file = "funding_data_summary.xlsx"
output_df.to_excel(output_file, index=False)

print(f"Data successfully transformed and exported to {output_file}")