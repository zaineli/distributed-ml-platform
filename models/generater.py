import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

num_samples = 1000

# Generate synthetic data for each feature
temperature = np.random.uniform(20, 40, num_samples)           # Temperature between 20 and 40
humidity = np.random.uniform(30, 70, num_samples)              # Humidity between 30 and 70
hour_of_day = np.random.randint(0, 24, num_samples)            # Hour of day between 0 and 23
day_of_week = np.random.randint(0, 7, num_samples)             # Day of week (0 - 6)
temp_change_rate = np.random.uniform(-1, 1, num_samples)       # Temperature rate change between -1 and 1
humidity_change_rate = np.random.uniform(-0.5, 0.5, num_samples) # Humidity rate change between -0.5 and 0.5
avg_temp_last_5min = temperature - np.random.uniform(0, 2, num_samples)  # Simulated average temperature
status_flag = np.random.randint(0, 2, num_samples)             # Binary label (0 or 1)

# Create a DataFrame with the generated data
df = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "hour_of_day": hour_of_day,
    "day_of_week": day_of_week,
    "temp_change_rate": temp_change_rate,
    "humidity_change_rate": humidity_change_rate,
    "avg_temp_last_5min": avg_temp_last_5min,
    "status_flag": status_flag
})

# Save DataFrame to CSV
df.to_csv("training_data.csv", index=False)
print("✅ training_data.csv generated with 1000 rows.")
