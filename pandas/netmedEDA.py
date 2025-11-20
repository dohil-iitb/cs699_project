import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os

# -------------------------------------------------
# 1. LOAD FILE
# -------------------------------------------------
file_path = r"C:\Users\91901\OneDrive\Desktop\DrugPriceTracker\data\netmeds_data_20251120_110639.csv"

df = pd.read_csv(file_path)

# -------------------------------------------------
# 2. CLEAN PRICE COLUMN (₹, â‚¹, ranges etc)
# -------------------------------------------------
def clean_price(val):
    if pd.isna(val):
        return None
    
    s = str(val)
    s = re.sub(r"[^\d\.\-]", "", s)  # remove currency symbols etc

    # Handle ranges like "0-803"
    if "-" in s:
        parts = s.split("-")
        nums = [float(p) for p in parts if p.strip() != ""]
        if nums:
            return sum(nums) / len(nums)
        else:
            return None

    # Single numeric value
    try:
        return float(s)
    except:
        return None

df["clean_price"] = df["price"].apply(clean_price)

# -------------------------------------------------
# 3. EXTRACT DATE + TIME FROM FILENAME (daily trend)
# -------------------------------------------------
filename = os.path.basename(file_path)

# Format: netmeds_data_YYYYMMDD_HHMMSS.csv
match = re.search(r"(\d{8})_(\d{6})", filename)
date_str = match.group(1)
time_str = match.group(2)

df["date"] = pd.to_datetime(date_str, format="%Y%m%d")
df["time"] = pd.to_datetime(time_str, format="%H%M%S").time()

# -------------------------------------------------
# 4. MEAN PRICE PER MEDICINE (since each has 3 rows)
# -------------------------------------------------
medicine_mean = df.groupby("medicine_name")["clean_price"].mean().reset_index()

# Save cleaned file
output_clean = r"C:\Users\91901\OneDrive\Desktop\DrugPriceTracker\data\netmeds_cleaned_mean_prices.csv"
medicine_mean.to_csv(output_clean, index=False)

# -------------------------------------------------
# 5. EDA: SUMMARY STATISTICS
# -------------------------------------------------
stats = df["clean_price"].describe()
print("\n📌 Price Summary:\n", stats)

# -------------------------------------------------
# 6. PLOTS (Distribution, Cheapest, Costliest)
# -------------------------------------------------

# ---- Price distribution ----
plt.figure(figsize=(8,6))
sns.histplot(df["clean_price"], bins=10)
plt.title("Price Distribution – Netmeds")
plt.xlabel("Price")
plt.ylabel("Count")
plt.show()

# ---- Cheapest medicines ----
cheapest = medicine_mean.nsmallest(10, "clean_price")

plt.figure(figsize=(10,6))
sns.barplot(data=cheapest, x="clean_price", y="medicine_name")
plt.title("Top 10 Cheapest Medicines")
plt.xlabel("Mean Price")
plt.ylabel("Medicine")
plt.show()

# ---- Costliest medicines ----
costliest = medicine_mean.nlargest(10, "clean_price")

plt.figure(figsize=(10,6))
sns.barplot(data=costliest, x="clean_price", y="medicine_name")
plt.title("Top 10 Most Expensive Medicines")
plt.xlabel("Mean Price")
plt.ylabel("Medicine")
plt.show()

# -------------------------------------------------
# 7. DAILY TREND INSIGHT
# -------------------------------------------------
# Since this file is 1-day data, trend = just mean
daily_mean = df["clean_price"].mean()

print("\n📌 Daily Average Price on", df['date'].iloc[0].date(), "=", daily_mean)

# -------------------------------------------------
# 8. SAVE FINAL EDA STATS
# -------------------------------------------------
stats_output = r"C:\Users\91901\OneDrive\Desktop\DrugPriceTracker\data\netmeds_stats.txt"
with open(stats_output, "w") as f:
    f.write(str(stats))

print("\nAll EDA files saved successfully!")
