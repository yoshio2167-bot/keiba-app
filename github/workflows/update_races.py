import pandas as pd
import random
import datetime

# 実行日の取得（今週末の開催日想定）
today = datetime.date.today()
print(f"Updating race data for weekend around: {today}")

# 阪神競馬場全12レースの最新データを自動生成して上書き保存するサンプル
for r in range(1, 13):
    random.seed(today.toordinal() + r)
    num_horses = 12 if r != 11 else 16
    
    df_r = pd.DataFrame({
        '枠番': [(i % 8) + 1 for i in range(num_horses)],
        '馬番': [i + 1 for i in range(num_horses)],
        '馬名': [f"自動更新馬{r}_{i+1}" for i in range(num_horses)],
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
    
    df_r.to_csv(f"hanshin_r{r}.csv", index=False, encoding='utf-8-sig')

print("All Hanshin race files updated successfully!")
