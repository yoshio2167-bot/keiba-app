import streamlit as st
import pandas as pd

st.title("🏇 マイ競馬予想アプリ (拡張版)")

# サイドバーでレース条件を設定
st.sidebar.header("📍 レース条件設定")
course = st.sidebar.selectbox("競馬場", ["東京", "中山", "京都", "阪神", "小倉", "新潟"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1600m (マイル)", "2000m (中距離)", "2500m以上 (長距離)"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在の条件:** {course}・{distance} / 馬場: **{track_condition}**")

# 初期データの項目に出走間隔と直近5走の平均着順などを追加
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame({
        '馬名': ['サイレンスディープ', 'レッドオーシャン', 'ブルーブレイブ', 'ゴールドアクター', 'ホワイトスピード'],
        'スピード指数': [88, 85, 82, 86, 79],
        '騎手勝率': [0.18, 0.15, 0.12, 0.20, 0.08],
        '距離適性': [90, 80, 85, 75, 70],
        'スタミナ': [80, 85, 90, 85, 75],
        '間隔(週)': [4, 8, 2, 24, 3],          # 出走間隔（中何週か）
        '直近5走平均着順': [2.1, 3.5, 4.2, 1.8, 6.5] # 直近5走の平均着順（数字が小さいほど優秀）
    })

st.subheader("1. 出走馬データの編集")
edited_df = st.data_editor(st.session_state.data, num_rows="dynamic")

if st.button("AI予想（印を付与）を実行"):
    # 直近5走の平均着順を「評価値」に変換（着順が良いほどスコアが高くなるように調整）
    # 例: 平均着順1位なら高得点、平均10位なら低得点
    max_rank = 10.0
    edited_df['直近成績スコア'] = (max_rank - edited_df['直近5走平均着順'].clip(1, 10)) * 10
    
    # 馬場状態や出走間隔（叩き良化型か、休み明けかなど）を考慮したスコア計算
    if track_condition in ["重", "不良"]:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.25 +
            edited_df['騎手勝率'] * 100 * 0.15 +
            edited_df['距離適性'] * 0.15 +
            edited_df['スタミナ'] * 0.25 +
            edited_df['直近成績スコア'] * 0.1 +
            (edited_df['間隔(週)'] * 0.5) * 0.1
        )
        st.info("※重・不良馬場＋ローテーションを考慮して計算しています。")
    else:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.35 +
            edited_df['騎手勝率'] * 100 * 0.2 +
            edited_df['距離適性'] * 0.2 +
            edited_df['直近成績スコア'] * 0.15 +
            (edited_df['間隔(週)'] * 0.5) * 0.1
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
    
    st.subheader("📊 予想・印の結果")
    st.dataframe(result_df[['印', '馬名', 'スコア', '直近5走平均着順', '間隔(週)']])
    
    st.success("予想が完了しました！")
