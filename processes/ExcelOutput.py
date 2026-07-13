import os
import sys
from datetime import date, timedelta

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers
from locallib.pandas import *
from locallib.box import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *
from lib.query.bank import *


#Get total KPI
def week_dates(year, week):
    """
    Returns the start and end dates (Monday to Sunday) of the given ISO week and year.
    """
    # Ensure year and week are integers (convert if they're not)
    year = int(year)
    week = int(week)
    # Use the ISO calendar to get the Monday of the week
    # ISO: Monday is 1, Sunday is 7
    from datetime import date, timedelta
    # Python 3.8+ provides fromisocalendar
    week_start = date.fromisocalendar(year, week, 1)
    week_end = week_start + timedelta(days=6)
    # Make sure week_start is not before 2026-01-01
    min_start = date(2026, 1, 1)
    if week_start < min_start:
        week_start = min_start
        week_end = week_start + timedelta(days=6)
    return week_start, week_end

if __name__ == "__main__":
    year = 2026
    customer_list = get_customer_list(KPIHub_Conn)
    for _, customer in customer_list.iterrows():
        print("--------------------------------")
        print(customer['Name'])
        customer_name = customer['Name']
        file_name = f"{customer_name}{SUFFIX}_{year}.xlsx"

        # FIXED: Proper parentheses, correct SQL, execute call outside Query call, and fetch result
        query_string = f"""
            SELECT * FROM KPI_OutputExcelLocation 
            WHERE CustomerId = (
                SELECT CustomerId FROM KPI_Customer WHERE name = '{customer_name}'
            )
        """
        result = Query(query=query_string).execute(KPIHub_Conn)
        if result.empty:
            raise ValueError(f"No output Excel location found for customer: {customer_name}")
        box_folder_id = result['BoxFolderId'].values[0]

        #Get the columns of the view and get the KPI definitions
        cols = Query("PRAGMA table_info('Weekly_KPI')").execute(KPIHub_Conn)
        cols.db.set_query("SELECT * FROM KPI_Definition WHERE name IN (SELECT name from temp_KPI)")
        kpi_col = cols.db.execute(KPIHub_Conn, source_col = 'name', temp_table_name = 'temp_KPI')
        output_dict = {kpi_col['Name']: [kpi_col['Unit'], kpi_col['Description'], kpi_col['Formula']] for _, kpi_col in kpi_col.iterrows()}


        regions = Query(f"SELECT DISTINCT BoundaryRegion FROM Weekly_KPI WHERE CustomerName = '{customer_name}'").execute(KPIHub_Conn)
        kpi_data = Query(f"SELECT * FROM Weekly_KPI WHERE CustomerName = '{customer_name}' AND Year = {year}").execute(KPIHub_Conn)

        with pd.ExcelWriter(file_name) as writer:
            for _, region_row in regions.iterrows():
                region = region_row['BoundaryRegion']
                # Select the export_df according to region (handle null safely)
                if pd.isnull(region):
                    export_df = kpi_data[kpi_data['BoundaryRegion'].isnull()].copy()
                    sheet_name = f"KPI Global {year} Weekly"
                else:
                    export_df = kpi_data[kpi_data['BoundaryRegion'] == region].copy()
                    sheet_region = str(region)[:10]  # limit to 20 characters
                    sheet_name = f"KPI {sheet_region} {year} Weekly"
               

                # Fill PeakAboveSATCount with 0, but only if column exists
                if 'PeakAboveSATCount' in export_df.columns:
                    export_df['PeakAboveSATCount'] = export_df['PeakAboveSATCount'].fillna(0)

                # Process the WeekDates
                export_df['WeekDates'] = export_df['PeriodValue'].apply(lambda week: f"{week_dates(2026, int(week))[0]} to {week_dates(2026, int(week))[1]}")
                # Move "WeekDates" to the first column in export_df
                cols = list(export_df.columns)
                if "WeekDates" in cols:
                    cols.insert(0, cols.pop(cols.index("WeekDates")))
                    export_df = export_df[cols]

                # Process the column name
                units = []
                for col in export_df.columns:
                    if col in kpi_col['Name'].values:
                        units.append(kpi_col.loc[kpi_col['Name'] == col, 'Unit'].values[0])
                    else:
                        units.append("")

                # Write the filtered DataFrame to the first sheet
                # Write columns and units as first two rows, then export the rest of the DataFrame
                rows = export_df.values.tolist()
                full_rows = [export_df.columns.tolist(), units] + rows
                temp_df = pd.DataFrame(full_rows)

                temp_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

                # Post-process the sheet for bold and center alignment of the first two columns
                worksheet = writer.sheets[sheet_name]
                # Create bold and center formats
                bold_center = writer.book.add_format({'bold': True, 'align': 'center'})
                center = writer.book.add_format({'align': 'center'})

                # The first two rows (headers and units): apply bold and center format to *all* columns, not just columns 0 and 1
                for row_idx in range(2):
                    for col_idx in range(len(full_rows[row_idx])):
                        worksheet.write(row_idx, col_idx, full_rows[row_idx][col_idx], bold_center)  # overwrite with bold+center

                # All other rows: just center the first two columns
                for i, row in enumerate(rows, start=2):
                    for col in range(2):
                        worksheet.write(i, col, row[col], center)
                # Add a colored line (cell border) at the bottom of all cells in the second row (units row)
                bottom_border_format = writer.book.add_format({'bottom': 1, 'bottom_color': '#000000', 'align': 'center', 'bold': True})
                for col_idx in range(len(full_rows[1])):
                    worksheet.write(1, col_idx, full_rows[1][col_idx], bottom_border_format)

                # Auto-adjust column widths based on the maximum length in each column
                for idx, col in enumerate(export_df.columns):
                    # Find the max length of any value in this column (including header and units)
                    max_len = max(
                        [len(str(col)), len(str(units[idx]))] +
                        [len(str(row[idx])) for row in rows]
                    )
                    # Set the width (add some padding)
                    worksheet.set_column(idx, idx, max_len + 2)

            # Write the key and its list of [Unit, Description, Formula Used] as columns in the second sheet
            desc_rows = []
            for key, value in output_dict.items():
                if isinstance(value, list) and len(value) == 3:
                    # Value is a list: [Unit, Description, Formula Used]
                    row = [key] + value
                else:
                    # Fallback in case the dictionary isn't formatted as expected
                    row = [key, "", "", ""]
                desc_rows.append(row)
            columns = ["Key", "Unit", "Description", "Formula Used"]
            desc_df = pd.DataFrame(desc_rows, columns=columns)
            desc_df.to_excel(writer, sheet_name="KPI Descriptions", index=False)

        box_obj = BoxFile(local_path = file_name, box_folder_id = box_folder_id)
        box_obj.upload()
        box_obj.delete()
        print("Excel output created and uploaded to Box")
        print("--------------------------------")