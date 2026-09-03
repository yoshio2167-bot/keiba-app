import streamlit as st
import pandas as pd

st.title("🏇 マイ競馬予想アプリ (枠番・オッズ対応版)")

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
    # 表示項目に枠番・馬番・オッズを追加
    st.dataframe(result_df[['印', '枠番', '馬番', '馬名', '単勝オッズ', 'スコア']])
    
    # 焼き鳥防止（的中率重視）の買い目自動生成
    st.subheader("🎫 焼き鳥防止！おすすめ買い目シミュレーション")
    
    if len(result_df) >= 3:
        本命行 = result_df.loc[result_df['印'] == "◎ 本命"].iloc[0]
        対抗行 = result_df.loc[result_df['印'] == "○ 対抗"].iloc[0]
        単穴行 = result_df.loc[result_df['印'] == "▲ 単穴"].iloc[0]
        
        st.markdown(f"""
        * **【絶対焼き鳥回避】複勝（手堅く的中狙い）**
          * 複勝: **{本命行['馬番']}番 {本命行['馬名']}** （オッズ {本命行['単勝オッズ']}倍の軸）
        * **【本命軸・流し】ワイド（的中重視のバランス型）**
          * 流し： **{本命行['馬番']}番 － {対抗行['馬番']}番, {単穴行['馬番']}番** （計2点）
        * **【手堅く狙う】馬連流し**
          * 流し： **{本命行['馬番']}番 － {対抗行['馬番']}番, {単穴行['馬番']}番** （計2点）
        """)
        st.success("枠番・馬番・オッズを反映した買い目を出力しました！")
    else:
        st.warning("馬のデータが3頭以上必要です。")
