import streamlit as st
import pandas as pd

st.title("🏇 マイ競馬予想アプリ")

# サイドバーでレース条件を設定
st.sidebar.header("📍 レース条件設定")
course = st.sidebar.selectbox("競馬場", ["東京", "中山", "京都", "阪神", "小倉", "新潟"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1600m (マイル)", "2000m (中距離)", "2500m以上 (長距離)"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在の条件:** {course}・{distance} / 馬場: **{track_condition}**")

# 初期データの項目に「スタミナ」を追加
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame({
        '馬名': ['サイレンスディープ', 'レッドオーシャン', 'ブルーブレイブ', 'ゴールドアクター', 'ホワイトスピード'],
        'スピード指数': [88, 85, 82, 86, 79],
        '騎手勝率': [0.18, 0.15, 0.12, 0.20, 0.08],
        '距離適性': [90, 80, 85, 75, 70],
        'スタミナ': [80, 85, 90, 85, 75]
    })

st.subheader("1. 出走馬データの編集")
edited_df = st.data_editor(st.session_state.data, num_rows="dynamic")

if st.button("AI予想（印を付与）を実行"):
    # 馬場状態に応じたロジックの切り替え（重・不良はスタミナ・パワーを重視する）
    if track_condition in ["重", "不良"]:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.3 +
            edited_df['騎手勝率'] * 100 * 0.2 +
            edited_df['距離適性'] * 0.2 +
            edited_df['スタミナ'] * 0.3
        )
        st.info("※重・不良馬場のため、スタミナとパワーの評価ウェイトを高めて計算しています。")
    else:
        edited_df['スコア'] = (
            edited_df['スピード指数'] * 0.4 +
            edited_df['騎手勝率'] * 100 * 0.3 +
            edited_df['距離適性'] * 0.3
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
    st.dataframe(result_df[['印', '馬名', 'スコア', 'スピード指数', 'スタミナ']])
    
    st.success("予想が完了しました！")
