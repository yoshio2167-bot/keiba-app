import streamlit as st
import pandas as pd
import random

st.title("🏇 マイ競馬予想アプリ (シミュレーション統計版)")

# サイドバーでレース条件を設定
st.sidebar.header("📍 レース条件設定")
course = st.sidebar.selectbox("競馬場", ["東京", "中山", "京都", "阪神", "小倉", "新潟", "中京", "札幌", "函館"])
surface = st.sidebar.radio("コース種別", ["芝", "ダート"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1400m", "1600m (マイル)", "1800m", "2000m (中距離)", "2400m以上 (長距離)"])
weather = st.sidebar.selectbox("天候", ["晴", "曇", "雨", "雪"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在の条件:** {course}・{surface}・{distance} / 天候: **{weather}** / 馬場: **{track_condition}**")

# ファイルアップロード機能
st.subheader("1. 出馬表データの読み込み")
uploaded_file = st.file_uploader("任意のCSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='shift-jis')
    st.success("CSVファイルを正常に読み込みました！")
else:
    st.info("※初期サンプルデータを使用中です。CSVをアップロードすると自動で切り替わります。")
    df = pd.DataFrame({
        '枠番': [1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 8],
        '馬番': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        '馬名': [
            'ボーンディスウェイ', 'サヴォーナ', 'ロデオドライブ', 'ドゥレッツァ', 
            'ゾロアストロ', 'チェルヴィニア', 'ジュンブロッサム', 'ダノンシーマ', 
            'アーバンシック', 'バレエマスター', 'ステレンボッシュ', 'マスカレードディ'
        ],
        '単勝オッズ': [85.1, 26.5, 3.7, 9.2, 3.5, 15.5, 60.5, 3.2, 18.4, 36.9, 13.3, 10.0],
        '脚質': ['先行', '差し', '先行', '先行', '差し', '追込', '追込', '先行', '差し', '追込', '先行', '差し'],
        '上がり3F': [34.5, 34.0, 33.6, 33.5, 33.4, 33.2, 33.1, 33.3, 33.7, 34.2, 33.8, 33.9],
        'スピード指数': [82, 85, 89, 91, 90, 86, 81, 92, 87, 80, 88, 85],
        '騎手勝率': [0.10, 0.12, 0.18, 0.16, 0.19, 0.15, 0.09, 0.21, 0.14, 0.08, 0.17, 0.12],
        '距離適性': [85, 88, 90, 92, 90, 87, 82, 93, 89, 78, 91, 85],
        'スタミナ': [86, 90, 88, 92, 90, 85, 84, 91, 92, 80, 88, 85],
        '間隔(週)': [4, 6, 3, 8, 5, 10, 4, 6, 7, 5, 9, 4],
        '直近5走平均着順': [5.2, 4.0, 2.2, 3.1, 2.0, 4.5, 6.8, 1.8, 4.2, 7.1, 3.8, 3.0]
    })

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
    is_long_straight = course in long_straight_courses
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
    
    # ── 10回レースシミュレーション統計機能 ──
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
