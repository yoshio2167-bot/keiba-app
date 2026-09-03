import pandas as pd
import random
import datetime

today = datetime.date.today()
print(f"Updating weekend race data for around: {today}")

courses = {
    "hanshin": "阪神",
    "nakayama": "中山",
    "tokyo": "東京"
}

days = ["sat", "sun"]

for day in days:
    for course_key, course_name in courses.items():
        for r in range(1, 13):
            random.seed(today.toordinal() + hash(day) + hash(course_key) + r)
            num_horses = 14 if r == 11 else 12
            
            df_r = pd.DataFrame({
                '枠番': [(i % 8) + 1 for i in range(num_horses)],
                '馬番': [i + 1 for i in range(num_horses)],
                '馬名': [f"{course_name}({day.upper()})馬{r}_{i+1}" for i in range(num_horses)],
                '単勝オッズ': [round(random.uniform(1.8, 50.0), 1) for _ in range(num_horses)],
                '脚質': [random.choice(['逃げ', '先行', '差し', '追込']) for _ in range(num_horses)],
                '上がり3F': [round(random.uniform(33.2, 35.8), 1) for _ in range(num_horses)],
                'スピード指数': [random.randint(75, 96) for _ in range(num_horses)],
                '騎手勝率': [round(random.uniform(0.07, 0.23), 2) for _ in range(num_horses)],
                '距離適性': [random.randint(78, 95) for _ in range(num_horses)],
                'スタミナ': [random.randint(78, 95) for _ in range(num_horses)],
                '間隔(週)': [random.randint(2, 10) for _ in range(num_horses)],
                '直近5走平均着順': [round(random.uniform(1.5, 7.5), 1) for _ in range(num_horses)]
            })
            
            df_r.to_csv(f"{day}_{course_key}_r{r}.csv", index=False, encoding='utf-8-sig')

print("All Saturday and Sunday race files updated successfully!")
