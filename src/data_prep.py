
import pandas as pd
import gridstatus

# 1. Initialize the CAISO ISO interface
caiso = gridstatus.CAISO()

# Define the timeframe
start_date = "2025-07-01"
end_date = "2025-07-08" 

print("Fetching Total Demand...")
# Pull historical 5-minute demand data
demand_df = caiso.get_load(start=start_date, end=end_date)

print("Fetching Solar Generation...")
# Pull historical 5-minute renewable generation data
supply_df = caiso.get_fuel_mix(start=start_date, end=end_date)

# 2. Clean up Datetime Indexes and filter for Solar
# Set the timestamp as the index for time series analysis 
demand_df.set_index('Time', inplace=True)
supply_df.set_index('Time', inplace=True)

# 3. Resample to Hourly Data
print("Resampling to hourly intervals...")
# Average the 5-minute intervals into 1-hour blocks, taking the mean of the MW values 
demand_hourly = demand_df[['Load']].resample('1H').mean()
solar_hourly = supply_df[['Solar']].resample('1H').mean()

# 4. Merge Demand and Generation
caiso_merged = pd.merge(
    demand_hourly, 
    solar_hourly, 
    left_index=True, 
    right_index=True
)
caiso_merged.columns = ['Total_Demand_MW', 'Solar_Generation_MW']

# 5. Load local Curtailment Excel file
print("Loading local curtailment data...")
curtailment_df = pd.read_excel("../data/raw/curtailment_data.xlsx")

# Combine Date and Hour columns into a single Datetime index
curtailment_df['Datetime'] = pd.to_datetime(curtailment_df['Date']) + pd.to_timedelta(curtailment_df['Hour'], unit='h')
curtailment_df.set_index('Datetime', inplace=True)
curtailment_df.index = curtailment_df.index.tz_localize('US/Pacific')

# Aggregate the multiple curtailment events per hour by summing them together
curtailment_hourly = curtailment_df[['Solar Curtailment']].resample('1h').sum()

# 6. Merge the datasets
final_dataset = pd.merge(
    caiso_merged, 
    curtailment_hourly,
    left_index=True, 
    right_index=True, 
    how='left'
)

# Fill hours with zero curtailment where CAISO didn't curtail anything
final_dataset['Solar Curtailment'] = final_dataset['Solar Curtailment'].fillna(0)

# 7. Export to processed data folder
output_path = "../data/processed/pypsa_1week_input.csv"
final_dataset.to_csv(output_path)
print(f"Success! Data saved to {output_path}")