#removing warnings from pymongo/cryptography
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from pymongo import MongoClient
import pandas as pd

#initialising client variable
client = MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
db = client['El-Plan-STEM']

#creating dataframes for the collections
results_df = pd.DataFrame(list(db['results'].find()))
races_df = pd.DataFrame(list(db['races'].find()))
drivers_df = pd.DataFrame(list(db['drivers'].find()))

#removing id columns so it doesnt give any issues later
results_df = results_df.drop(columns=['_id'], errors='ignore')
races_df = races_df.drop(columns=['_id'], errors='ignore')
drivers_df = drivers_df.drop(columns=['_id'], errors='ignore')

#merging collections for full context
merged_df = results_df.merge(races_df[['raceId', 'year', 'date', 'name']], on='raceId', how='left')
merged_df = merged_df.merge(drivers_df[['driverId', 'surname', 'forename']], on='driverId', how='left')
merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')

#ask user for driver full name
driver_input = input("Enter driver's full name (e.g., lewis hamilton): ").strip().lower()

#split name to match both parts
if len(driver_input.split()) < 2:
    print("Please enter both forename and surname.")
else:
    forename_input, surname_input = driver_input.split()[0], driver_input.split()[1]
    matching_driver = drivers_df[
        (drivers_df['forename'].str.lower() == forename_input) &
        (drivers_df['surname'].str.lower() == surname_input)
    ]

    if matching_driver.empty:
        print("Leave the hope for him buddy.")
    else:
        driver_id = matching_driver.iloc[0]['driverId']
        full_name = matching_driver.iloc[0]['forename'] + " " + matching_driver.iloc[0]['surname']

        driver_results = merged_df[merged_df['driverId'] == driver_id].sort_values(by='date', ascending=False)

        if len(driver_results) < 5:
            print(f"Not enough races found for {full_name}.")
        else:
            recent_24 = driver_results.head(24)
            podiums = recent_24[recent_24['positionOrder'] <= 3]

            if len(podiums) >= 2:
                print(f"{full_name}: Podium likely based on last 24 races.")
            else:
                print(f"{full_name}: Podium unlikely based on last 24 races.")
