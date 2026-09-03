import streamlit as st
import pandas as pd

st.title("🏇 マイ競馬予想アプリ (買い目自動生成版)")

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
        '馬名': ['サイレンスディープ', 'レッドオーシャン', 'ブルーブレイブ', 'ゴールドアクター', 'ホワイトスピード'],
        'スピード指数': [88, 85, 82, 86, 79],
        '騎手勝率': [0.18, 0.15, 0.12, 0.20, 0.08],
        '距離適性': [90, 80, 85, 75, 70],
        'スタミナ': [80, 85, 90, 85, 75],
        '間隔(週)': [4, 8, 2, 24, 3],
        '直近5走平均着順': [2.1, 3.5, 4.2, 1.8, 6.5]
    })

# データの編集画面
st.subheader("2. 出走馬データの確認・調整")
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
    st.dataframe(result_df[['印', '馬名', 'スコア', '直近5走平均着順', '間隔(週)']])
    
    # 焼き鳥防止（的中率重視）の買い目自動生成
    st.subheader("🎫 焼き鳥防止！おすすめ買い目シミュレーション")
    
    if len(result_df) >= 3:
        本命馬 = result_df.loc[result_df['印'] == "◎ 本命", '馬名'].values
        対抗馬 = result_df.loc[result_df['印'] == "○ 対抗", '馬名'].values
        単穴馬 = result_df.loc[result_df['印'] == "▲ 単穴", '馬名'].values
        
        本命名 = 本命馬[0] if len(本命馬) > 0 else result_df.loc[0, '馬名']
        対抗名 = 対抗馬[0] if len(対抗馬) > 0 else result_df.loc[1, '馬名']
        単穴名 = 単穴馬[0] if len(単穴馬) > 0 else result_df.loc[2, '馬名']
        
        st.markdown(f"""
        * **【絶対焼き鳥回避】単勝・複勝（手堅く1点勝負）**
          * 複勝: **{本命名}** （まずはここを軸にすれば大崩れしにくい！）
        * **【本命軸・流し】ワイド（的中重視のバランス型）**
          * 流し： **{本命名} － {対抗名}、{単穴名}** （計2点）
        * **【手堅く狙う】馬連流し**
          * 流し： **{本命名} － {対抗名}、{単穴名}** （計2点）
        """)
        st.success("的中率と回収率のバランスを考えた買い目を出力しました！")
    else:
        st.warning("馬のデータが3頭以上必要です。")
