import pandas as pd
import numpy as np
import warnings
import os
warnings.filterwarnings("ignore")

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# TensorFlow imports for LSTM model
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split

def get_df(collection_name):
    from pymongo import MongoClient
    client = MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
    db = client['El-Plan-STEM']
    return pd.DataFrame(list(db[collection_name].find()))

def load_data():
    """Load all required data from MongoDB"""
    laps = get_df("lap_times")
    pits = get_df("pit_stops")
    results = get_df("results")
    races = get_df("races")
    status = get_df("status")
    return laps, pits, results, races, status

def prepare_race_data(race_id, target_laps=24, target_drivers=20):
    """Prepare race data with better handling of missing drivers/laps"""
    lap_chunk = laps[laps['raceId'] == race_id]
    
    if lap_chunk.empty:
        return None, "No lap data"
    
    pivot = lap_chunk.pivot(index='lap', columns='driverId', values='milliseconds')
    
    # Get actual race participants from results to fill missing drivers
    race_participants = results[results['raceId'] == race_id]['driverId'].unique()
    
    # Extend pivot to include all race participants (even those with no lap times)
    all_drivers = sorted(set(list(pivot.columns) + list(race_participants)))
    pivot = pivot.reindex(columns=all_drivers)
    
    # Ensure we have enough laps (pad or trim)
    max_lap = min(pivot.index.max() if not pivot.empty else 0, target_laps)
    if max_lap < 5:
        return None, f"Insufficient lap data: only {max_lap} laps"
    
    pivot = pivot.reindex(index=range(1, target_laps + 1))
    
    if len(pivot.columns) < target_drivers:
        dummy_drivers = [f"dummy_{i}" for i in range(len(pivot.columns), target_drivers)]
        for dummy in dummy_drivers:
            pivot[dummy] = np.nan
    else:
        pivot = pivot.iloc[:, :target_drivers]
    
    pivot = pivot.fillna(method='ffill').fillna(method='bfill')
    
    race_median = pivot.median().median()
    if pd.isna(race_median):
        race_median = 90000
    pivot = pivot.fillna(race_median)
    
    return pivot, "Success"

def train_and_save_model():
    """Train the model and save it for future use"""
    global laps, pits, results, races, status
    laps, pits, results, races, status = load_data()
    
    X = []
    y = []

    race_ids = laps['raceId'].unique()
    status_map = dict(status[['statusId', 'status']].values)

    print("Training model...")

    for i, race in enumerate(race_ids):
        pivot, status_msg = prepare_race_data(race)
        if pivot is None:
            continue
        
        if pivot.shape != (24, 20):
            continue
        
        norm_laps = (pivot - pivot.mean()) / (pivot.std() + 1e-8)
        
        pit_count = pits[pits['raceId'] == race]['driverId'].nunique()
        
        result_slice = results[results['raceId'] == race]
        result_slice['actual_status'] = result_slice['statusId'].map(status_map)
        dnf_count = result_slice['actual_status'].apply(
            lambda s: isinstance(s, str) and any(x in s.lower() for x in ['dnf', 'dsq', 'accident', 'engine', 'retired', 'withdrawal'])
        ).sum()
        
        extra = np.array([pit_count, dnf_count]) / 20.0
        extra_repeated = np.tile(extra, (24, 1))
        
        combo = np.hstack([norm_laps.values, extra_repeated])
        X.append(combo)
        
        lap_variation = np.std(np.diff(norm_laps.values, axis=0))
        dnf_rate = dnf_count / len(result_slice)
        lap_spread = np.std(norm_laps.values, axis=1).mean()
        
        base_momentum = (dnf_rate * 5) + (lap_spread * 2.5)
        
        if dnf_count > 0 or lap_spread > 0.3:
            base_momentum += (lap_variation * 1.0)
        
        if dnf_count > 0 and pit_count > 15:
            base_momentum += 0.3
        
        y.append(1 if base_momentum > 1.5 else 0)

    X = np.array(X)
    y = np.array(y)

    print("Model ready!")

    if len(X) < 10:
        print("Not enough data to train model")
        return None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    X_train = X_train.reshape((-1, 24, X.shape[2]))
    X_test = X_test.reshape((-1, 24, X.shape[2]))

    model = Sequential()
    model.add(Conv1D(64, kernel_size=3, activation='relu', input_shape=(24, X.shape[2])))
    model.add(MaxPooling1D(pool_size=2))
    model.add(LSTM(64))
    model.add(Dropout(0.3))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
    history = model.fit(X_train, y_train, epochs=20, batch_size=16, verbose=0, validation_data=(X_test, y_test))

    model.save('f1_momentum_model.h5')
    print("Model trained and saved!")
    return model

def load_or_train_model():
    """Load existing model or train a new one if it doesn't exist"""
    model_path = 'f1_momentum_model.h5'
    
    if os.path.exists(model_path):
        print("Loading existing model...")
        model = load_model(model_path)
        print("Model loaded successfully!")
        return model
    else:
        print("No existing model found. Training new model...")
        return train_and_save_model()

def predict_race_momentum(race_name):
    """Main function to predict race momentum"""
    model = load_or_train_model()
    if model is None:
        return
    
    laps, pits, results, races, status = load_data()
    status_map = dict(status[['statusId', 'status']].values)
    
    if ' ' not in race_name:
        print("Invalid format. Please use 'Location Year' format (e.g., 'Monaco 2021')")
        return

    place, year = race_name.rsplit(' ', 1)
    try:
        year = int(year)
    except ValueError:
        print("Invalid year format")
        return

    found = races[(races['name'].str.contains(place, case=False)) & (races['year'] == year)]

    if found.empty:
        print(f"No race found matching '{place} {year}'. Check spelling and year.")
        return

    race_id = found.iloc[0]['raceId']
    race_name_full = found.iloc[0]['name']
    print(f"Found race: {race_name_full} ({year})")

    pivot, status_msg = prepare_race_data(race_id)
    if pivot is None:
        print(f"Cannot analyze race: {status_msg}")
        return

    if pivot.shape != (24, 20):
        print(f"Race data shape issue: {pivot.shape}, expected (24, 20)")
        return

    norm = (pivot - pivot.mean()) / (pivot.std() + 1e-8)

    pit_count = pits[pits['raceId'] == race_id]['driverId'].nunique()
    result_race = results[results['raceId'] == race_id]
    result_race['actual_status'] = result_race['statusId'].map(status_map)
    dnf_count = result_race['actual_status'].apply(
        lambda s: isinstance(s, str) and any(x in s.lower() for x in ['dnf', 'dsq', 'accident', 'engine', 'retired', 'withdrawal'])
    ).sum()

    print(f"Race stats: {pit_count} drivers made pit stops, {dnf_count} DNFs out of {len(result_race)} drivers")

    norm_variation = np.std(np.diff(norm.values, axis=0))
    dnf_rate = dnf_count / len(result_race)
    lap_spread = np.std(norm.values, axis=1).mean()

    base_momentum = (dnf_rate * 5) + (lap_spread * 2.5)
    variation_counted = False
    pit_bonus = 0

    if dnf_count > 0 or lap_spread > 0.3:
        base_momentum += (norm_variation * 1.0)
        variation_counted = True

    if dnf_count > 0 and pit_count > 15:
        base_momentum += 0.3
        pit_bonus = 0.3

    extra = np.array([pit_count, dnf_count]) / 20.0
    extra = np.tile(extra, (24, 1))

    final_input = np.hstack([norm.values, extra]).reshape(1, 24, norm.values.shape[1] + 2)
    pred = model.predict(final_input, verbose=0)[0][0]

    print(f"\nRace Analysis:")
    print(f"• Lap time variation: {norm_variation:.3f} {'(counted)' if variation_counted else '(not counted - no incidents)'}")
    print(f"• DNF rate: {dnf_rate:.1%}")  
    print(f"• Driver performance spread: {lap_spread:.3f}")
    print(f"• Pit stops: {pit_count} drivers {'(bonus: +0.3)' if pit_bonus > 0 else '(normal strategy)'}")
    print(f"• Combined momentum factors: {base_momentum:.3f}")
    print(f"• Neural network prediction: {pred:.3f}")

    if pred > 0.5:
        print("\n🔥 HIGH MOMENTUM RACE: Elbows out, drama loaded!")
    else:
        print("\n😴 LOW MOMENTUM RACE: Parade mode enabled.")

# Main execution
if __name__ == "__main__":
    race_input = input("Enter race name (format: 'Location Year'): ").strip()
    predict_race_momentum(race_input)
