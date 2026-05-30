# model_turn_severity.py

from pymongo import MongoClient
import pandas as pd
import numpy as np
import warnings
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

def predict_turn_severity():
    client = MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
    db = client['El-Plan-STEM']

    lap_times_df = pd.DataFrame(list(db['lap_times'].find())).drop(columns=['_id'], errors='ignore')

    samples = []
    labels = []

    for race_id in lap_times_df['raceId'].unique()[:200]:
        race_data = lap_times_df[lap_times_df['raceId'] == race_id]

        for driver_id in race_data['driverId'].unique():
            driver_data = race_data[(race_data['driverId'] == driver_id)].sort_values(by='lap').head(20)

            if len(driver_data) < 5:
                continue

            lap_times = driver_data['milliseconds'].values
            lap_deltas = np.diff(lap_times)

            for i in range(len(lap_deltas)):
                prev = lap_deltas[i-1] if i > 0 else lap_deltas[i]
                diff = abs(lap_deltas[i] - prev)

                if diff < 100:
                    severity = 0
                elif diff < 300:
                    severity = 1
                else:
                    severity = 2

                if i >= 2:
                    feature = lap_deltas[i-2:i+1]
                    samples.append(feature)
                    labels.append(severity)

    X = np.array(samples)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    result = {
        "accuracy": round(accuracy * 100, 2),
        "mild": int(sum(y_pred == 0)),
        "medium": int(sum(y_pred == 1)),
        "sharp": int(sum(y_pred == 2)),
        "message": "Turn severity model trained and evaluated successfully."
    }

    joblib.dump(clf, "turn_severity_rf_model.joblib")

    return result
