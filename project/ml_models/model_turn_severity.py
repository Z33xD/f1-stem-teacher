from pymongo import MongoClient
import pandas as pd
import numpy as np

#warnings are irritating me so yea removing em
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

#initialising client variable
client=MongoClient("mongodb+srv://Z33xD:MxVEi2OTvIs4HfjM@el-plan-stem.12pthvy.mongodb.net/?retryWrites=true&w=majority&appName=El-Plan-STEM")
db=client['El-Plan-STEM']

#creating dataframes for the collections so that can be easily accessed via pandas
lap_times_df=pd.DataFrame(list(db['lap_times'].find()))
results_df=pd.DataFrame(list(db['results'].find()))
driver_standings_df=pd.DataFrame(list(db['driver_standings'].find()))

#removing id columns so it doesnt give any issues later (OCD wali problem)
lap_times_df = lap_times_df.drop(columns=['_id'], errors='ignore')

# now we simulate turn severity based on lap time spikes
samples=[]
labels=[]

#looping over limited races so RAM doesn't blow up
for race_id in lap_times_df['raceId'].unique()[:200]:
    race_data = lap_times_df[lap_times_df['raceId'] == race_id]

    # now loop over drivers for this race
    for driver_id in race_data['driverId'].unique():
        driver_data = race_data[(race_data['driverId'] == driver_id)].sort_values(by='lap').head(20)

        #skip if data too small
        if len(driver_data) < 5:
            continue

        lap_times = driver_data['milliseconds'].values
        lap_deltas = np.diff(lap_times)

        # simulating turn severity based on lap delta jump
        for i in range(len(lap_deltas)):
            prev = lap_deltas[i-1] if i > 0 else lap_deltas[i]
            diff = abs(lap_deltas[i] - prev)

            #define labels (0 = mild, 1 = medium, 2 = sharp)
            if diff < 100:
                severity = 0
            elif diff < 300:
                severity = 1
            else:
                severity = 2

            #building features using sliding window of 3 deltas
            if i >= 2:
                feature = lap_deltas[i-2:i+1]
                samples.append(feature)
                labels.append(severity)

#convert to np arrays cz scikit
X = np.array(samples)
y = np.array(labels)

#train test split cz it's not 1990
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

#random forest cz it's fast and reliable
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

#eval
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
mild = sum(y_pred == 0)
medium = sum(y_pred == 1)
sharp = sum(y_pred == 2)

print("🔥 Turn Severity Prediction Model Trained")
print(f"Accuracy: {accuracy * 100:.2f}%")
print(f"Mild turns predicted: {mild}")
print(f"Medium turns predicted: {medium}")
print(f"Sharp turns predicted: {sharp}")

#optional saving cz you’ll need this later
import joblib
joblib.dump(clf, "turn_severity_rf_model.joblib")
