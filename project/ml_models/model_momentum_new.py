# model_momentum.py

import pandas as pd
import numpy as np
import warnings
import os
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from pymongo import MongoClient

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def get_df(collection_name):
    client = MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
    db = client['El-Plan-STEM']
    return pd.DataFrame(list(db[collection_name].find()))

def load_data():
    return get_df("lap_times"), get_df("pit_stops"), get_df("results"), get_df("races"), get_df("status")

def prepare_race_data(race_id, target_laps=24, target_drivers=20):
    lap_chunk = laps[laps['raceId'] == race_id]
    if lap_chunk.empty:
        return None, "No lap data"

    pivot = lap_chunk.pivot(index='lap', columns='driverId', values='milliseconds')
    race_participants = results[results['raceId'] == race_id]['driverId'].unique()
    all_drivers = sorted(set(list(pivot.columns) + list(race_participants)))
    pivot = pivot.reindex(columns=all_drivers)
    pivot = pivot.reindex(index=range(1, target_laps + 1))

    if len(pivot.columns) < target_drivers:
        for i in range(len(pivot.columns), target_drivers):
            pivot[f'dummy_{i}'] = np.nan
    else:
        pivot = pivot.iloc[:, :target_drivers]

    pivot = pivot.fillna(method='ffill').fillna(method='bfill')
    median = pivot.median().median()
    if pd.isna(median):
        median = 90000
    pivot = pivot.fillna(median)

    return pivot, "Success"

def load_or_train_model():
    model_path = "f1_momentum_model.h5"
    if os.path.exists(model_path):
        return load_model(model_path)
    else:
        return None  # Optional: implement training if needed

def predict_race_momentum(race_name: str):
    global laps, pits, results, races, status
    laps, pits, results, races, status = load_data()
    status_map = dict(status[['statusId', 'status']].values)

    if ' ' not in race_name:
        return {"error": "Invalid race name format. Use 'Location Year'"}
    place, year = race_name.rsplit(" ", 1)
    try:
        year = int(year)
    except ValueError:
        return {"error": "Year must be an integer"}

    race = races[(races['name'].str.contains(place, case=False)) & (races['year'] == year)]
    if race.empty:
        return {"error": "Race not found"}

    race_id = race.iloc[0]['raceId']
    pivot, status_msg = prepare_race_data(race_id)
    if pivot is None:
        return {"error": status_msg}

    model = load_or_train_model()
    if model is None:
        return {"error": "Model not available"}

    norm = (pivot - pivot.mean()) / (pivot.std() + 1e-8)
    pit_count = pits[pits['raceId'] == race_id]['driverId'].nunique()
    result_race = results[results['raceId'] == race_id]
    result_race['actual_status'] = result_race['statusId'].map(status_map)
    dnf_count = result_race['actual_status'].apply(
        lambda s: isinstance(s, str) and any(x in s.lower() for x in ['dnf', 'dsq', 'accident', 'engine', 'retired', 'withdrawal'])
    ).sum()

    norm_variation = np.std(np.diff(norm.values, axis=0))
    dnf_rate = dnf_count / len(result_race)
    lap_spread = np.std(norm.values, axis=1).mean()

    base_momentum = (dnf_rate * 5) + (lap_spread * 2.5)
    if dnf_count > 0 or lap_spread > 0.3:
        base_momentum += norm_variation
    if dnf_count > 0 and pit_count > 15:
        base_momentum += 0.3

    extra = np.array([pit_count, dnf_count]) / 20.0
    final_input = np.hstack([norm.values, np.tile(extra, (24, 1))]).reshape(1, 24, norm.shape[1] + 2)

    pred = model.predict(final_input, verbose=0)[0][0]
    is_high_momentum = pred > 0.5

    return {
        "race": race.iloc[0]['name'],
        "year": year,
        "prediction": "High Momentum 🔥" if is_high_momentum else "Low Momentum 😴",
        "stats": {
            "pit_count": int(pit_count),
            "dnf_count": int(dnf_count),
            "dnf_rate": round(dnf_rate * 100, 2),
            "lap_spread": round(lap_spread, 3),
            "lap_variation": round(norm_variation, 3),
            "momentum_score": round(pred, 3)
        }
    }
