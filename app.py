import streamlit as st
import pandas as pd
import zipfile
import io
import random
from datetime import date

st.set_page_config(page_title="中央競馬AI予想・シミュレーションアプリ", layout="wide")

st.title("🏇 中央競馬 AI予想 & 100回シミュレーション")

if 'history' not in st.session_state:
    st.session_state['history'] = []

st.sidebar.header("開催情報・レース設定")
race_date = st.sidebar.date_input("開催日", date(2026, 9, 5))
race_location = st.sidebar.selectbox("開催地", ["中山", "阪神", "東京", "中京", "京都", "新潟", "小倉", "福島", "札幌", "函館"], index=0)
race_number = st.sidebar.selectbox("レース番号", [f"{i}R" for i in range(1, 13)], index=10)

col_dir, col_sur = st.sidebar.columns(2)
with col_dir:
    race_direction = st.selectbox("回り", ["右", "左", "直線"], index=0)
with col_sur:
    race_surface = st.selectbox("コース", ["芝", "ダート", "障害"], index=0)

race_distance = st.sidebar.text_input("距離 (m)", "1600m")
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"], index=0)
weather = st.sidebar.selectbox("天候", ["晴", "曇", "小雨", "雨"], index=0)

race_title = f"{race_location}{race_number}"
full_condition_str = f"{race_surface}{race_distance} ({race_direction}・{track_condition})"

st.sidebar.header("データ入力・管理")
input_mode = st.sidebar.radio("データ読込方法", ["直接テキストペースト", "CSVファイル個別アップロード", "ZIP一括アップロード"])

df = None

if input_mode == "直接テキストペースト":
    pasted_text = st.sidebar.text_area("CSV形式のテキストを貼り付け", height=200, value="")
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
    date_str = race_date.strftime('%Y/%m/%d')
    st.subheader(f"🏁 {date_str} {race_title}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("開催日", date_str)
    with col2:
        st.metric("レース", race_title)
    with col3:
        st.metric("コース", full_condition_str)
    with col4:
        st.metric("馬場状態", track_condition)
    with col5:
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
    
    col_run, col_save = st.columns([1, 1])
    with col_run:
        run_sim = st.button("シミュレーション実行")

    if run_sim:
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
        st.session_state['current_sim'] = sim_df

    if 'current_sim' in st.session_state:
        st.dataframe(st.session_state['current_sim'], use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 アプリ内に結果を保存する"):
                st.session_state['history'].append({
                    '日付': date_str,
                    'レース': race_title,
                    '開催情報': full_condition_str,
                    '結果df': st.session_state['current_sim']
                })
                st.success(f"「{date_str} {race_title}」の結果をアプリ内履歴に保存しました！")
        with col_btn2:
            csv_data = st.session_state['current_sim'].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSVファイルとしてダウンロード",
                data=csv_data,
                file_name=f"simulation_result_{date_str.replace('/','')}_{race_title}.csv",
                mime="text/csv"
            )

    if st.session_state['history']:
        st.markdown("---")
        st.subheader("📂 アプリ内保存履歴（消えずに保持されます）")
        for idx, item in enumerate(st.session_state['history']):
            with st.expander(f"履歴 #{idx+1}: 【{item['日付']} {item['レース']}】 ({item['開催情報']})"):
                st.dataframe(item['結果df'], use_container_width=True)
                if st.button(f"この履歴を削除 #{idx+1}", key=f"del_{idx}"):
                    st.session_state['history'].pop(idx)
                    st.rerun()
else:
    st.info("左側のメニューからデータを読み込んでください。")
