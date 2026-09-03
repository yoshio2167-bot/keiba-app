import streamlit as st
import pandas as pd
import random
import os

st.title("🏇 阪神競馬場・全12レース予想シミュレーター (自動読込対応版)")

# サイドバーで競馬場とレース選択
st.sidebar.header("📍 2026.9.6 開催選択")
selected_course = st.sidebar.selectbox("競馬場", ["阪神", "東京", "中山", "京都", "小倉", "新潟", "中京"])

if selected_course == "阪神":
    race_options = [f"第{i}レース (R{i})" for i in range(1, 13)]
    selected_race = st.sidebar.selectbox("阪神全12R 選択", race_options)
else:
    selected_race = st.sidebar.selectbox("レース選択", ["第1レース", "第11レース メイン"])

surface = st.sidebar.radio("コース種別", ["芝", "ダート"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1400m", "1600m (マイル)", "1800m", "2000m (中距離)", "2400m以上 (長距離)"])
weather = st.sidebar.selectbox("天候", ["晴", "曇", "雨", "雪"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在表示中:** 2026/9/6(日) {selected_course} **{selected_race}** ({surface}・{distance}) / 天候: **{weather}** / 馬場: **{track_condition}**")

# 1. 任意のCSVファイルアップロード
st.subheader("1. 出馬表データ（自動ロード または CSV追加）")
uploaded_file = st.file_uploader("特定のCSVファイルをアップロードする場合はこちら", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='shift-jis')
    st.success(f"{uploaded_file.name} を読み込みました！")
else:
    race_num = int(selected_race.replace("第", "").replace("レース", "").split(" ")[0]) if "第" in selected_race else 1
    filename = f"hanshin_r{race_num}.csv"
    
    # 自動更新されたCSVファイルが存在すればそれを読み込み、なければ自動生成する
    if selected_course == "阪神" and os.path.exists(filename):
        try:
            df = pd.read_csv(filename, encoding='utf-8')
            st.info(f"※自動更新されたサーバー上の **{filename}** を読み込みました。")
        except:
            df = pd.read_csv(filename, encoding='shift-jis')
    else:
        random.seed(20260906 + race_num * 17)
        horse_names = [
            'テーオーロイヤル', 'ロードフォース', 'リバティヴェール', 'コントレイルハート', 
            'イクイノックス2', 'ダノンデイス', 'ドウデュースマン', 'グランブリッジ', 
            'セリフォスアイ', 'ソダシホワイト', 'スターズオンアース', 'ジャスティンパレス',
            'シャドウアイ', 'レッドヴァイス', 'ファントムレイヴン', 'ブルーブレイブ'
        ]
        num_horses = 12 if race_num != 11 else 16
        selected_names = random.sample(horse_names, min(num_horses, len(horse_names)))
        if len(selected_names) < num_horses:
            selected_names += [f"阪神馬{i}" for i in range(len(selected_names), num_horses)]
        
        df = pd.DataFrame({
            '枠番': [(i % 8) + 1 for i in range(num_horses)],
            '馬番': [i + 1 for i in range(num_horses)],
            '馬名': selected_names,
            '単勝オッズ': [round(random.uniform(1.8, 65.0), 1) for _ in range(num_horses)],
            '脚質': [random.choice(['逃げ', '先行', '差し', '追込']) for _ in range(num_horses)],
            '上がり3F': [round(random.uniform(33.1, 35.5), 1) for _ in range(num_horses)],
            'スピード指数': [random.randint(76, 96) for _ in range(num_horses)],
            '騎手勝率': [round(random.uniform(0.07, 0.23), 2) for _ in range(num_horses)],
            '距離適性': [random.randint(78, 95) for _ in range(num_horses)],
            'スタミナ': [random.randint(78, 95) for _ in range(num_horses)],
            '間隔(週)': [random.randint(2, 12) for _ in range(num_horses)],
            '直近5走平均着順': [round(random.uniform(1.5, 7.2), 1) for _ in range(num_horses)]
        })
        st.info(f"※選択中の **{selected_race}** の標準データを使用中です。")

# 安全セーフティ機能
default_columns = {
    '枠番': 1, '馬番': 1, '馬名': '不明馬', '単勝オッズ': 10.0,
    '脚質': '先行', '上がり3F': 35.0, 'スピード指数': 80,
    '騎手勝率': 0.10, '距離適性': 80, 'スタミナ': 80,
    '間隔(週)': 4, '直近5走平均着順': 5.0
}
for col, default_val in default_columns.items():
    if col not in df.columns:
        df[col] = default_val

# 2. データの編集画面
st.subheader("2. 出馬馬データの確認・調整")
edited_df = st.data_editor(df, num_rows="dynamic")

if 'result_df' not in st.session_state:
    st.session_state.result_df = None

if st.button("AI予想＆買い目を実行"):
    max_rank = 10.0
    edited_df['直近成績スコア'] = (max_rank - edited_df['直近5走平均着順'].clip(1, 10)) * 10
    edited_df['上がり3Fスコア'] = (40.0 - edited_df['上がり3F'].clip(32, 40)) * 10
    
    long_straight_courses = ["東京", "新潟", "阪神"]
    is_long_straight = selected_course in long_straight_courses
    is_power_cond = (track_condition in ["重", "不良"]) or (weather in ["雨", "雪"])
    
    if surface == "ダート" or is_power_cond:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.15 +
            edited_df['騎手勝率'] * 100 * 0.15 +
            edited_df['距離適性'] * 0.15 +
            edited_df['スタミナ'] * 0.30 +
            edited_df['直近成績スコア'] * 0.10 +
            edited_df['上がり3Fスコア'] * 0.10 +
            (edited_df['間隔(週)'] * 0.5) * 0.05
        )
    elif is_long_straight and surface == "芝":
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.25 +
            edited_df['騎手勝率'] * 100 * 0.15 +
            edited_df['距離適性'] * 0.15 +
            edited_df['スタミナ'] * 0.10 +
            edited_df['直近成績スコア'] * 0.10 +
            edited_df['上がり3Fスコア'] * 0.20 +
            (edited_df['間隔(週)'] * 0.5) * 0.05
        )
    else:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.30 +
            edited_df['騎手勝率'] * 100 * 0.20 +
            edited_df['距離適性'] * 0.20 +
            edited_df['スタミナ'] * 0.10 +
            edited_df['直近成績スコア'] * 0.10 +
            edited_df['上がり3Fスコア'] * 0.05 +
            (edited_df['間隔(週)'] * 0.5) * 0.05
        )
    
    result_df = edited_df.sort_values(by='スコア', ascending=False).reset_index(drop=True)
    
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
