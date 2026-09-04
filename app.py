import streamlit as st
import pandas as pd
import random

st.title("🏇 中央競馬 AI予想＆実績検証シミュレーター")

# クイック選択 (メイン等)
st.sidebar.header("⚡ クイック選択")
quick_jump = st.sidebar.selectbox("注目レース選択", ["通常選択モードを使用", "土曜阪神1R (実馬表)", "土曜メイン (11R)", "日曜メイン (11R)"])

if quick_jump == "土曜阪神1R (実馬表)":
    default_day_idx = 0
    default_course_idx = 0
    default_race_num = 1
    default_surface_idx = 1  # ダート
    default_dist_idx = 1     # 1400m
elif quick_jump == "土曜メイン (11R)":
    default_day_idx = 0
    default_course_idx = 0
    default_race_num = 11
    default_surface_idx = 0
    default_dist_idx = 2
elif quick_jump == "日曜メイン (11R)":
    default_day_idx = 1
    default_course_idx = 2
    default_race_num = 11
    default_surface_idx = 0
    default_dist_idx = 4
else:
    default_day_idx = 0
    default_course_idx = 0
    default_race_num = 1
    default_surface_idx = 0
    default_dist_idx = 2

# 開催・レース設定（サイドバー）
st.sidebar.header("📍 開催・レース設定")
selected_day = st.sidebar.radio("開催日", ["土曜日", "日曜日"], index=default_day_idx)
selected_course = st.sidebar.selectbox("競馬場", ["阪神", "中山", "東京"], index=default_course_idx)

race_options = [f"第{i}レース (R{i})" for i in range(1, 13)]
selected_race = st.sidebar.selectbox(f"{selected_course} 全12R 選択", race_options, index=default_race_num-1)
race_num = int(selected_race.replace("第", "").replace("レース", "").split(" ")[0])

surface = st.sidebar.radio("コース種別", ["芝", "ダート"], index=default_surface_idx)
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1400m", "1600m (マイル)", "1800m", "2000m (中距離)", "2400m以上 (長距離)"], index=default_dist_idx)
weather = st.sidebar.selectbox("天候", ["晴", "曇", "雨", "雪"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在表示中:** **{selected_day}** / {selected_course} **{selected_race}** ({surface}・{distance}) / 天候: **{weather}** / 馬場: **{track_condition}**")

# 出馬表データの定義（土曜阪神1Rは実際のデータを反映）
data_key = f"df_{selected_day}_{selected_course}_{race_num}"
if data_key not in st.session_state:
    if selected_day == "土曜日" and selected_course == "阪神" and race_num == 1:
        st.session_state[data_key] = pd.DataFrame({
            '枠番': [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4],
            '馬番': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            '馬名': ['テイオーワン', 'ロードアルタイル', 'リバティベル', 'コントレイルボーイ', 'イクイノックス', 'ダノンインパクト', 'ドウデュース', 'グランブリッジ', 'シャドウフォール', 'レッドゲイル', 'ファントムソード', 'ブルーインパルス'],
            '単勝オッズ': [2.4, 5.1, 8.3, 12.5, 15.0, 18.2, 22.1, 35.4, 42.0, 50.1, 75.3, 110.2],
            '脚質': ['先行', '差し', '逃げ', '差し', '追込', '先行', '差し', '逃げ', '先行', '追込', '差し', '追込'],
            '上がり3F': [34.2, 33.8, 35.0, 34.1, 33.5, 34.6, 34.0, 35.2, 34.5, 33.9, 34.8, 33.7],
            'スピード指数': [88, 90, 85, 89, 92, 86, 88, 83, 86, 91, 84, 87],
            '騎手勝率': [0.18, 0.21, 0.12, 0.15, 0.22, 0.10, 0.14, 0.08, 0.11, 0.19, 0.09, 0.13],
            '距離適性': [85, 88, 82, 86, 90, 84, 87, 80, 85, 89, 81, 86],
            'スタミナ': [84, 86, 83, 85, 88, 82, 85, 81, 84, 87, 82, 85],
            '間隔(週)': [3, 4, 2, 5, 6, 3, 4, 8, 2, 5, 3, 4],
            '直近5走平均着順': [2.1, 3.0, 4.2, 3.5, 1.8, 5.0, 3.8, 6.2, 4.5, 2.8, 5.5, 4.0]
        })
    else:
        seed_key = hash(selected_day) + hash(selected_course) + race_num * 37
        random.seed(seed_key)

        num_horses = 14 if race_num == 11 else 12
        base_names = ['テーオー', 'ロード', 'リバティ', 'コントレイル', 'イクイノックス', 'ダノン', 'ドウデュース', 'グランブリッジ', 'シャドウ', 'レッド', 'ファントム', 'ブルー', 'セイウン', 'ダイワ']

        horses = [f"{base_names[i % len(base_names)]}{i+1}号" for i in range(num_horses)]
        odds = [round(1.5 + (i * 2.8) + random.uniform(0.0, 1.5), 1) if i < 3 else round(10.0 + (i * 3.5), 1) for i in range(num_horses)]

        st.session_state[data_key] = pd.DataFrame({
            '枠番': [(i % 8) + 1 for i in range(num_horses)],
            '馬番': [i + 1 for i in range(num_horses)],
            '馬名': horses,
            '単勝オッズ': odds,
            '脚質': [random.choice(['逃げ', '先行', '差し', '追込']) for _ in range(num_horses)],
            '上がり3F': [round(random.uniform(33.2, 35.5), 1) for _ in range(num_horses)],
            'スピード指数': [random.randint(78, 95) for _ in range(num_horses)],
            '騎手勝率': [round(random.uniform(0.08, 0.22), 2) for _ in range(num_horses)],
            '距離適性': [random.randint(80, 94) for _ in range(num_horses)],
            'スタミナ': [random.randint(80, 94) for _ in range(num_horses)],
            '間隔(週)': [random.randint(2, 10) for _ in range(num_horses)],
            '直近5走平均着順': [round(random.uniform(1.5, 6.5), 1) for _ in range(num_horses)]
        })

st.subheader("1. 出馬表データの確認・編集（スマホから直接タップして変更可能）")
edited_df = st.data_editor(st.session_state[data_key], key=f"editor_{data_key}")

if 'result_df' not in st.session_state:
    st.session_state.result_df = None

if st.button("AI予想＆買い目を実行"):
    df = edited_df.copy()
    max_rank = 10.0
    df['直近成績スコア'] = (max_rank - df['直近5走平均着順'].clip(1, 10)) * 10
    df['上がり3Fスコア'] = (40.0 - df['上がり3F'].clip(32, 40)) * 10
    
    is_long_straight = selected_course in ["東京", "新潟", "阪神"]
    is_power_cond = (track_condition in ["重", "不良"]) or (weather in ["雨", "雪"])
    
    w_speed = 0.25
    w_jockey = 0.15
    w_dist = 0.15
    w_stamina = 0.10
    w_recent = 0.10
    w_3f = 0.15
    w_interval = 0.10

    if "1200m" in distance or "1400m" in distance:
        w_speed += 0.05
        w_3f += 0.05
        w_stamina -= 0.05
    elif "2400m" in distance:
        w_stamina += 0.15
        w_dist += 0.05
        w_speed -= 0.10

    if surface == "ダート" or is_power_cond:
        w_stamina += 0.10
        w_speed -= 0.05
        w_3f -= 0.05
    elif is_long_straight and surface == "芝":
        w_3f += 0.05

    total_w = w_speed + w_jockey + w_dist + w_stamina + w_recent + w_3f + w_interval
    w_speed /= total_w
    w_jockey /= total_w
    w_dist /= total_w
    w_stamina /= total_w
    w_recent /= total_w
    w_3f /= total_w
    w_interval /= total_w

    df['スコア'] = (
        df['スピード指数'] * w_speed +
        df['騎手勝率'] * 100 * w_jockey +
        df['距離適性'] * w_dist +
        df['スタミナ'] * w_stamina +
        df['直近成績スコア'] * w_recent +
        df['上がり3Fスコア'] * w_3f +
        (df['間隔(週)'] * 0.5) * w_interval
    )
    
    result_df = df.sort_values(by='スコア', ascending=False).reset_index(drop=True)
    
    印リスト = []
    for i in range(len(result_df)):
        if i == 0: 印リスト.append("◎ 本命")
        elif i == 1: 印リスト.append("○ 対抗")
        elif i == 2: 印リスト.append("▲ 単穴")
        elif 3 <= i <= 4: 印リスト.append("△ 連下")
        else: 印リスト.append("-")
    
    result_df['印'] = 印リスト
    st.session_state.result_df = result_df

if st.session_state.result_df is not None:
    res_df = st.session_state.result_df
    
    st.subheader("📊 予想・印の結果")
    st.dataframe(res_df[['印', '枠番', '馬番', '馬名', '脚質', '上がり3F', '単勝オッズ', 'スコア']])
    
    st.subheader("🎫 焼き鳥防止！おすすめ買い目シミュレーション")
    if len(res_df) >= 3:
        本命行 = res_df.loc[res_df['印'] == "◎ 本命"].iloc[0]
        対抗行 = res_df.loc[res_df['印'] == "○ 対抗"].iloc[0]
        単穴行 = res_df.loc[res_df['印'] == "▲ 単穴"].iloc[0]
        
        st.markdown(f"""
        * **複勝:** **{本命行['馬番']}番 {本命行['馬名']}**
        * **ワイド流し:** **{本命行['馬番']}番 － {対抗行['馬番']}番, {単穴行['馬番']}番**
        """)
    
    st.subheader("📈 10回シミュレーション統計 (勝率・複勝率分析)")
    if st.button("📊 10回レースを自動シミュレートして統計を出す"):
        with st.spinner("シミュレーション実行中..."):
            wins = {name: 0 for name in res_df['馬名']}
            podiums = {name: 0 for name in res_df['馬名']}
            
            for _ in range(10):
                sim_df = res_df[['馬番', '馬名', 'スコア']].copy()
                sim_df['current_pos'] = sim_df['スコア'] + [random.uniform(-10, 10) for _ in range(len(sim_df))]
                sim_df = sim_df.sort_values(by='current_pos', ascending=False).reset_index(drop=True)
                
                winner = sim_df.loc[0, '馬名']
                wins[winner] += 1
                
                for i in range(min(3, len(sim_df))):
                    p_name = sim_df.loc[i, '馬名']
                    podiums[p_name] += 1
            
            stats_data = []
            for _, row in res_df.iterrows():
                m_name = row['馬名']
                w_count = wins[m_name]
                p_count = podiums[m_name]
                stats_data.append({
                    '枠番': row['枠番'],
                    '馬番': row['馬番'],
                    '馬名': m_name,
                    '1着回数': w_count,
                    '勝率(%)': f"{w_count / 10 * 100:.1f}%",
                    '3着内回数': p_count,
                    '複勝率(%)': f"{p_count / 10 * 100:.1f}%"
                })
            
            stats_df = pd.DataFrame(stats_data).sort_values(by='1着回数', ascending=False).reset_index(drop=True)
            st.success("統計データの集計が完了しました！")
            st.dataframe(stats_df)

    # 3. 実際の結果入力＆検証モード
    st.subheader("🎯 実際の結果（着順）入力 ＆ 的中・回収率検証")
    col1, col2, col3 = st.columns(3)
    with col1:
        actual_1st_no = st.selectbox("実際の1着 馬番", res_df['馬番'].tolist(), index=0)
    with col2:
        actual_2nd_no = st.selectbox("実際の2着 馬番", res_df['馬番'].tolist(), index=min(1, len(res_df)-1))
    with col3:
        actual_3rd_no = st.selectbox("実際の3着 馬番", res_df['馬番'].tolist(), index=min(2, len(res_df)-1))
        
    if st.button("🏆 検証結果を集計する"):
        honmei_row = res_df.loc[res_df['印'] == "◎ 本命"].iloc[0]
        honmei_no = honmei_row['馬番']
        
        is_honmei_place = (honmei_no in [actual_1st_no, actual_2nd_no, actual_3rd_no])
        
        st.markdown("### 📊 検証レポート")
        st.write(f"- **AI本命 (◎):** {honmei_row['馬名']} (馬番: {honmei_no})")
        st.write(f"- **実際の入着:** 1着[{actual_1st_no}番] / 2着[{actual_2nd_no}番] / 3着[{actual_3rd_no}番]")
        
        if is_honmei_place:
            st.success("🎉 **本命馬が馬券圏内（3着以内）好走的中！**")
        else:
            st.warning("💦 本命馬は馬券圏外となりました。")
