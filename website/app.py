from flask import Flask, request, send_file, render_template
import pandas as pd
from datetime import datetime, timedelta
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    funding_file = request.files['file-funding']
    chick_file = request.files['file-chick']
    df_funding = pd.read_excel(funding_file)
    df_chick = pd.read_excel(chick_file)

    # Filter CHICK data
    df_chick = df_chick[(df_chick['All Claims Confirmed by Parent?'] == 'Yes')]

    # Transform the funding data
    transformed_data = []
    for index, row in df_funding.iterrows():
        child_name = row["Child"]
        allocation_date = datetime.strptime(row["Allocation Date"], "%d/%m/%Y")
        month = allocation_date.strftime("%b")
        if allocation_date < datetime(2024, 8, 1) or allocation_date > datetime(2025, 7, 31):
            continue
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
    output_columns = ["Name", "Date of Birth", "CHICK", "Claim Until", "Term/Non-Term/Changes", "Allocation Value"] + months
    output_df = pd.DataFrame(columns=output_columns)

    # Populate the final output DataFrame
    for name, group in grouped.groupby("Child Name"):
        hours_info = identify_term_non_term_times(group["Hours"].explode().tolist())
        allocation_value = group["Allocation Value"].sum()
        chick_info = df_chick[df_chick['Child'] == name]
        if chick_info.empty:
            continue
        dob = chick_info['Date of Birth'].values[0]
        chick = chick_info['CHICK'].values[0]
        claim_until = chick_info['Claim Until'].values[0]
        row = {
            "Name": name,
            "Date of Birth": dob,
            "CHICK": chick,
            "Claim Until": claim_until,
            "Term/Non-Term/Changes": hours_info,
            "Allocation Value": f"€{allocation_value:.2f}"
        }
        for month in months:
            if month in group["Month"].values:
                row[month] = f"€{group[group['Month'] == month]['Allocation Value'].values[0]:.2f}"
            else:
                row[month] = ""
        output_df = pd.concat([output_df, pd.DataFrame([row])], ignore_index=True)

    # Convert DataFrame to Excel file with formatting
    output = io.BytesIO()
    workbook = Workbook()
    worksheet = workbook.active

    for r in dataframe_to_rows(output_df, index=False, header=True):
        worksheet.append(r)

    # Apply conditional formatting
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    amber_fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=4, max_col=4):
        for cell in row:
            if cell.value:
                claim_until_date = pd.to_datetime(cell.value, format="%d/%m/%Y", dayfirst=True)
                days_diff = (claim_until_date - datetime.now()).days
                if days_diff <= 7:
                    cell.fill = red_fill
                elif days_diff <= 14:
                    cell.fill = amber_fill
                elif days_diff <= 30:
                    cell.fill = yellow_fill

    workbook.save(output)
    output.seek(0)

    return send_file(output, download_name="funding_data_summary.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)