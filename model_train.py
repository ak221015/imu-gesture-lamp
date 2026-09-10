# Trains a gesture classifier from recorded IMU data.
# Reads every recording in gestures/, cuts it into 0.5 s windows,
# trains a random forest and saves it to model.joblib.
# Run this once after adding new recordings.

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report
import joblib

rows = list()

# fmt: off
names = ["mean_ax", "mean_ay", "mean_az", "mean_gx", "mean_gy", "mean_gz",
         "std_ax", "std_ay", "std_az", "std_gx", "std_gy", "std_gz",
         "dif_ax", "dif_ay", "dif_az", "dif_gx", "dif_gy", "dif_gz",
         "label", "record"]
# fmt: on

for name in ["swipe_lr", "swipe_ud", "rotate", "shake", "circle", "nothing"]:
    for j in range(1, 41):
        df = pd.read_csv("gestures/" + name + "/" + name + str(j) + ".csv")
        df = df[["ax", "ay", "az", "gx", "gy", "gz"]]
        # 50 samples = 0.5 s at 100 Hz, step 25 gives 50% overlap
        for i in range(0, len(df) - 49, 25):
            w = df.iloc[i : i + 50]
            # 18 features per window: mean, std and peak-to-peak for 6 channels
            rows.append(list(w.mean()) + list(w.std()) + list(w.max() - w.min()) + [name, name + str(j) + ".csv"])

df2 = pd.DataFrame(rows, columns=names)

# Every 4th recording goes to the test set, so windows from the same
# recording never end up in both train and test
test_files = list()
for name in ["swipe_lr", "swipe_ud", "rotate", "shake", "circle", "nothing"]:
    for j in range(4, 41, 4):
        test_files.append(name + str(j) + ".csv")
mask = df2["record"].isin(test_files)
train_df = df2[~mask]
test_df = df2[mask]
train_df_x = train_df[names[:18]]
train_df_y = train_df["label"]
test_df_x = test_df[names[:18]]
test_df_y = test_df["label"]

model = RandomForestClassifier(random_state=0)
model.fit(train_df_x, train_df_y)
pred = model.predict(test_df_x)
print(confusion_matrix(test_df_y, pred))
print(classification_report(test_df_y, pred))

# Save the trained forest so the main script starts instantly
joblib.dump(model, "model.joblib")
