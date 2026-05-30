# model_podium_prediction.py

import warnings
from pymongo import MongoClient
import pandas as pd
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

def predict_driver_podium(driver_name: str):
    client = MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
    db = client['El-Plan-STEM']

    results_df = pd.DataFrame(list(db['results'].find())).drop(columns=['_id'], errors='ignore')
    races_df = pd.DataFrame(list(db['races'].find())).drop(columns=['_id'], errors='ignore')
    drivers_df = pd.DataFrame(list(db['drivers'].find())).drop(columns=['_id'], errors='ignore')

    merged_df = results_df.merge(races_df[['raceId', 'year', 'date', 'name']], on='raceId', how='left')
    merged_df = merged_df.merge(drivers_df[['driverId', 'surname', 'forename']], on='driverId', how='left')
    merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')

    name_parts = driver_name.strip().lower().split()
    if len(name_parts) < 2:
        return {"error": "Please provide both forename and surname."}

    forename, surname = name_parts
    match = drivers_df[(drivers_df['forename'].str.lower() == forename) & (drivers_df['surname'].str.lower() == surname)]

    if match.empty:
        return {"result": f"No records found for {driver_name.title()}. Sorry champ."}

    driver_id = match.iloc[0]['driverId']
    full_name = match.iloc[0]['forename'] + " " + match.iloc[0]['surname']

    driver_results = merged_df[merged_df['driverId'] == driver_id].sort_values(by='date', ascending=False)
    if len(driver_results) < 5:
        return {"result": f"Not enough race history for {full_name}."}

    recent_24 = driver_results.head(24)
    podiums = recent_24[recent_24['positionOrder'] <= 3]

    return {
        "driver": full_name,
        "podiums_last_24": int(len(podiums)),
        "prediction": "Podium likely!" if len(podiums) >= 2 else "Podium unlikely!"
    }
