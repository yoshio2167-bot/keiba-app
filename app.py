import streamlit as st
import pandas as pd

st.title("🏇 マイ競馬予想アプリ")

st.markdown("スマホから出馬表データを調整して、AIの印（◎○▲△）を即座に確認できます。")

# 出走馬データの初期値
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame({
        '馬名': ['サイレンスディープ', 'レッドオーシャン', 'ブルーブレイブ', 'ゴールドアクター', 'ホワイトスピード'],
        'スピード指数': [88, 85, 82, 86, 79],
        '騎手勝率': [0.18, 0.15, 0.12, 0.20, 0.08],
        '距離適性': [90, 80, 85, 75, 70]
    })

st.subheader("1. 出走馬データの編集")
# スマホでも表形式で直感的に数値を変更できます
edited_df = st.data_editor(st.session_state.data, num_rows="dynamic")

if st.button("AI予想（印を付与）を実行"):
    # スコア計算（各要素の重み付け）
    edited_df['スコア'] = (
        edited_df['スピード指数'] * 0.4 +
        edited_df['騎手勝率'] * 100 * 0.3 +
        edited_df['距離適性'] * 0.3
    )
    
    # スコアが高い順に並び替え
    result_df = edited_df.sort_values(by='スコア', ascending=False).reset_index(drop=True)
    
    # 印の自動割り振り
    印リスト = []
    for i in range(len(result_df)):
        if i == 0: 印リスト.append("◎ 本命")
        elif i == 1: 印リスト.append("○ 対抗")
        elif i == 2: 印リスト.append("▲ 単穴")
        elif 3 <= i <= 4: 印リスト.append("△ 連下")
        else: 印リスト.append("-")
    
    result_df['印'] = 印リスト
    
    st.subheader("📊 予想・印の結果")
    # 見やすいように列を絞って表示
    st.dataframe(result_df[['印', '馬名', 'スコア', 'スピード指数']])
    
    st.success("予想が完了しました！")
