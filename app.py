import streamlit as st
import pandas as pd
import time
import random

st.title("🏇 マイ競馬予想アプリ (レース実況ゲーム版)")

# サイドバーでレース条件を設定
st.sidebar.header("📍 レース条件設定")
course = st.sidebar.selectbox("競馬場", ["東京", "中山", "京都", "阪神", "小倉", "新潟"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1600m (マイル)", "2000m (中距離)", "2500m以上 (長距離)"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在の条件:** {course}・{distance} / 馬場: **{track_condition}**")

# ファイルアップロード機能
st.subheader("1. 出馬表データの読み込み")
uploaded_file = st.file_uploader("出馬表のCSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSVファイルを読み込みました！")
else:
    st.info("※サンプルデータを使用中です。CSVをアップロードすると入れ替わります。")
    df = pd.DataFrame({
        '枠番': [1, 2, 3, 4, 5],
        '馬番': [1, 3, 5, 7, 9],
        '馬名': ['サイレンスディープ', 'レッドオーシャン', 'ブルーブレイブ', 'ゴールドアクター', 'ホワイトスピード'],
        '単勝オッズ': [2.4, 4.1, 7.8, 12.5, 25.0],
        'スピード指数': [88, 85, 82, 86, 79],
        '騎手勝率': [0.18, 0.15, 0.12, 0.20, 0.08],
        '距離適性': [90, 80, 85, 75, 70],
        'スタミナ': [80, 85, 90, 85, 75],
        '間隔(週)': [4, 8, 2, 24, 3],
        '直近5走平均着順': [2.1, 3.5, 4.2, 1.8, 6.5]
    })

# データの編集画面
st.subheader("2. 出馬馬データの確認・調整")
edited_df = st.data_editor(df, num_rows="dynamic")

# 予想結果を記憶する箱を用意
if 'result_df' not in st.session_state:
    st.session_state.result_df = None

if st.button("AI予想＆買い目を実行"):
    max_rank = 10.0
    edited_df['直近成績スコア'] = (max_rank - edited_df['直近5走平均着順'].clip(1, 10)) * 10
    
    if track_condition in ["重", "不良"]:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.25 +
            edited_df['騎手勝率'] * 100 * 0.15 +
            edited_df['距離適性'] * 0.15 +
            edited_df['スタミナ'] * 0.25 +
            edited_df['直近成績スコア'] * 0.1 +
            (edited_df['間隔(週)'] * 0.5) * 0.1
        )
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
    # 結果をメモリに保存
    st.session_state.result_df = result_df

# 予想結果がメモリにある場合は、いつでも表示する
if st.session_state.result_df is not None:
    res_df = st.session_state.result_df
    
    st.subheader("📊 予想・印の結果")
    st.dataframe(res_df[['印', '枠番', '馬番', '馬名', '単勝オッズ', 'スコア']])
    
    # 焼き鳥防止の買い目
    st.subheader("🎫 焼き鳥防止！おすすめ買い目シミュレーション")
    if len(res_df) >= 3:
        本命行 = res_df.loc[res_df['印'] == "◎ 本命"].iloc[0]
        対抗行 = res_df.loc[res_df['印'] == "○ 対抗"].iloc[0]
        単穴行 = res_df.loc[res_df['印'] == "▲ 単穴"].iloc[0]
        
        st.markdown(f"""
        * **複勝:** **{本命行['馬番']}番 {本命行['馬名']}**
        * **ワイド流し:** **{本命行['馬番']}番 － {対抗行['馬番']}番, {単穴行['馬番']}番**
        """)
    
    # ── レース実況ゲーム機能 ──
    st.subheader("🎮 3D風レース実況シミュレーター")
    if st.button("🚀 レーススタート！"):
        st.write("各馬、一斉にスタートしました！ゲートイン完了、発走！")
        
        race_df = res_df[['枠番', '馬番', '馬名', 'スコア']].copy()
        race_progress = st.empty()
        
        for phase in ["【スタート〜向こう正面】", "【第3コーナーを通過】", "【最後の直線に入った！】", "【ゴール前、激しい叩き合い！】"]:
            time.sleep(1.2)
            race_df['current_pos'] = race_df['スコア'] + [random.uniform(-10, 10) for _ in range(len(race_df))]
            race_df = race_df.sort_values(by='current_pos', ascending=False).reset_index(drop=True)
            
            with race_progress.container():
                st.markdown(f"### {phase}")
                st.info(f"1位: {race_df.loc[0, '馬番']}番 {race_df.loc[0, '馬名']} / 2位: {race_df.loc[1, '馬番']}番 {race_df.loc[1, '馬名']} / 3位: {race_df.loc[2, '馬番']}番 {race_df.loc[2, '馬名']}")
        
        time.sleep(1.0)
        st.success(f"🏆 ィーーーゴール！！ 優勝したのは **{race_df.loc[0, '馬番']}番 {race_df.loc[0, '馬名']}** だぁーーー！！")
        
        st.write("【正式結果】")
        final_result = []
        for i, row in race_df.iterrows():
            final_result.append(f"第{i+1}着: {row['馬番']}番 {row['馬名']}")
        st.text("\n".join(final_result))
