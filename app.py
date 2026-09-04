import streamlit as st
import pandas as pd
import zipfile
import io
import random

st.set_page_config(page_title="中央競馬AI予想・シミュレーションアプリ", layout="wide")

st.title("🏇 中央競馬 AI予想 & 100回シミュレーション")

st.sidebar.header("開催情報・データ設定")
race_location = st.sidebar.selectbox("開催地", ["中山", "阪神", "東京", "中京", "京都", "新潟", "小倉", "福島", "札幌", "函館"], index=0)
race_distance = st.sidebar.text_input("距離", "ダート1200m")
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"], index=0)
weather = st.sidebar.selectbox("天候", ["晴", "曇", "小雨", "雨"], index=0)

st.sidebar.header("データ入力・管理")
input_mode = st.sidebar.radio("データ読込方法", ["直接テキストペースト", "CSVファイル個別アップロード", "ZIP一括アップロード"])

df = None

if input_mode == "直接テキストペースト":
    pasted_text = st.sidebar.text_area("CSV形式のテキストを貼り付け（クリックで全選択・削除可能）", height=200, value="")
    if pasted_text:
        try:
            df = pd.read_csv(io.StringIO(pasted_text))
        except Exception as e:
            st.error(f"パースエラー: {e}")
elif input_mode == "CSVファイル個別アップロード":
    uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
elif input_mode == "ZIP一括アップロード":
    zip_file = st.sidebar.file_uploader("全レースZIPファイルをアップロード", type=["zip"])
    if zip_file is not None:
        with zipfile.ZipFile(zip_file, 'r') as z:
            namelist = z.namelist()
            csv_files = [n for n in namelist if n.endswith('.csv')]
            selected_csv = st.sidebar.selectbox("レースを選択", csv_files)
            if selected_csv:
                with z.open(selected_csv) as f:
                    df = pd.read_csv(f, encoding='utf-8-sig')

if df is not None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("開催地", race_location)
    with col2:
        st.metric("距離", race_distance)
    with col3:
        st.metric("馬場状態", track_condition)
    with col4:
        st.metric("天候", weather)

    st.markdown("---")
    st.subheader("📋 出馬表データ")
    st.dataframe(df, use_container_width=True)

    st.subheader("🤖 AI予想スコア算出")
    df['AIスコア'] = (
        df['スピード指数'] * 0.4 +
        df['距離適性'] * 0.2 +
        df['スタミナ'] * 0.1 +
        (df['騎手勝率'] * 100) * 0.15 +
        (10 / df['直近5走平均着順']) * 0.15
    ).round(1)

    df_sorted = df.sort_values(by='AIスコア', ascending=False).reset_index(drop=True)
    st.dataframe(df_sorted[['馬番', '馬名', '単勝オッズ', '脚質', 'AIスコア', 'スピード指数', '騎手勝率']], use_container_width=True)

    st.subheader("🎲 100回レースシミュレーション")
    if st.button("シミュレーション実行"):
        stats = {}
        for _, row in df.iterrows():
            stats[row['馬名']] = {'馬番': row['馬番'], '単勝オッズ': row['単勝オッズ'], '勝利回数': 0, '3位以内回数': 0}

        sim_count = 100
        for _ in range(sim_count):
            scores = [row['AIスコア'] + random.gauss(0, 5) for _, row in df.iterrows()]
            sim_df_temp = pd.DataFrame({'馬名': df['馬名'], 'スコア': scores})
            sim_df_temp = sim_df_temp.sort_values(by='スコア', ascending=False).reset_index(drop=True)
            
            winner_name = sim_df_temp.loc[0, '馬名']
            stats[winner_name]['勝利回数'] += 1

            top3_names = sim_df_temp.loc[:2, '馬名'].tolist()
            for name in top3_names:
                stats[name]['3位以内回数'] += 1

        sim_list = []
        for name, info in stats.items():
            sim_list.append({
                '馬番': info['馬番'],
                '馬名': name,
                '単勝オッズ': info['単勝オッズ'],
                '勝利回数': info['勝利回数'],
                '勝率(%)': (info['勝利回数'] / sim_count) * 100,
                '3位以内回数': info['3位以内回数'],
                '複勝率(%)': (info['3位以内回数'] / sim_count) * 100
            })

        sim_df = pd.DataFrame(sim_list).sort_values(by='勝利回数', ascending=False).reset_index(drop=True)
        st.dataframe(sim_df, use_container_width=True)

        # Save simulation result to session state & provide download button
        st.session_state['sim_result'] = sim_df

    if 'sim_result' in st.session_state:
        csv_data = st.session_state['sim_result'].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 シミュレーション結果をCSVとして保存（ダウンロード）",
            data=csv_data,
            file_name=f"simulation_result_{race_location}.csv",
            mime="text/csv"
        )
else:
    st.info("左側のメニューからデータを読み込んでください。")
