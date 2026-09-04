import streamlit as st
import pandas as pd
import zipfile
import io
import random
from datetime import date

st.set_page_config(page_title="中央競馬AI予想・複数レースシミュレーション", layout="wide")

st.title("🏇 中央競馬 AI予想 & 複数レース同時シミュレーション（最大5レース）")

if 'history' not in st.session_state:
    st.session_state['history'] = []

st.sidebar.header("⚙️ レース数・タブ設定")
num_races = st.sidebar.slider("シミュレーションするレース数", min_value=1, max_value=5, value=3)

race_tabs = st.tabs([f"第{i+1}レース設定" for i in range(num_races)])

race_configs = []

distances = ["1000m", "1200m", "1400m", "1600m", "1800m", "2000m", "2200m", "2400m", "2500m", "3000m", "3200m"]
locations = ["中山", "阪神", "東京", "中京", "京都", "新潟", "小倉", "福島", "札幌", "函館"]

for i, tab in enumerate(race_tabs):
    with tab:
        st.subheader(f"🏁 第 {i+1} レースの条件とデータ入力")
        c1, c2, c3 = st.columns(3)
        with c1:
            r_date = st.date_input(f"開催日 #{i+1}", date(2026, 9, 5), key=f"date_{i}")
            r_loc = st.selectbox(f"開催地 #{i+1}", locations, index=0 if i==0 else (1 if i==1 else 2), key=f"loc_{i}")
        with c2:
            r_num = st.selectbox(f"レース番号 #{i+1}", [f"{n}R" for n in range(1, 13)], index=9+i if i<3 else i, key=f"num_{i}")
            r_surface = st.selectbox(f"コース #{i+1}", ["芝", "ダート", "障害"], index=0 if i!=1 else 1, key=f"surf_{i}")
        with c3:
            r_dist = st.selectbox(f"距離 #{i+1}", distances, index=3 if i!=1 else 2, key=f"dist_{i}")
            r_cond = st.selectbox(f"馬場 #{i+1}", ["良", "稍重", "重", "不良"], index=0, key=f"cond_{i}")

        r_title = f"{r_loc}{r_num}"
        r_cond_str = f"{r_surface}{r_dist} ({r_direction if 'r_direction' in locals() else '右'}・{r_cond})"

        st.markdown("##### 📥 出馬表データの読込")
        input_mode = st.radio(f"読込方法 #{i+1}", ["直接テキストペースト", "CSVファイルアップロード"], key=f"mode_{i}")

        df = None
        if input_mode == "直接テキストペースト":
            pasted = st.text_area(f"CSVテキストペースト #{i+1}", height=150, value="", key=f"text_{i}")
            if pasted:
                try:
                    df = pd.read_csv(io.StringIO(pasted))
                except Exception as e:
                    st.error(f"パースエラー (#{i+1}): {e}")
        else:
            up_file = st.file_uploader(f"CSVアップロード #{i+1}", type=["csv"], key=f"up_{i}")
            if up_file is not None:
                df = pd.read_csv(up_file, encoding='utf-8-sig')

        race_configs.append({
            'index': i+1,
            'date': r_date.strftime('%Y/%m/%d'),
            'title': r_title,
            'condition': f"{r_surface}{r_dist} ({r_cond})",
            'df': df
        })

st.markdown("---")
st.header("🎲 一括シミュレーション実行（100回試行）")

if st.button("🚀 すべてのレースでシミュレーションを一斉実行", type="primary"):
    batch_results = []
    
    for rc in race_configs:
        if rc['df'] is not None:
            df = rc['df'].copy()
            df['AIスコア'] = (
                df['スピード指数'] * 0.4 +
                df['距離適性'] * 0.2 +
                df['スタミナ'] * 0.1 +
                (df['騎手勝率'] * 100) * 0.15 +
                (10 / df['直近5走平均着順']) * 0.15
            ).round(1)

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
            batch_results.append({
                '日付': rc['date'],
                'レース': rc['title'],
                '開催情報': rc['condition'],
                '結果df': sim_df
            })

    if batch_results:
        for res in batch_results:
            st.session_state['history'].append(res)
        st.success(f"🎉 {len(batch_results)}レース分のシミュレーションが完了し、アプリ内履歴に保存されました！")
    else:
        st.warning("有効なデータが入力されているレースがありません。各タブでCSVデータを入力してください。")

if st.session_state['history']:
    st.markdown("---")
    st.subheader("📂 アプリ内保存履歴（全レース分・消えずに保持されます）")
    
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️ すべての履歴をクリア"):
            st.session_state['history'] = []
            st.rerun()

    for idx, item in enumerate(st.session_state['history']):
        with st.expander(f"履歴 #{idx+1}: 【{item['日付']} {item['レース']}】 ({item['開催情報']})", expanded=(idx==len(st.session_state['history'])-1)):
            st.dataframe(item['結果df'], use_container_width=True)
            
            c_d, c_del = st.columns([2, 1])
            with c_d:
                csv_data = item['結果df'].to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"📥 この結果をCSVダウンロード (#{idx+1})",
                    data=csv_data,
                    file_name=f"sim_result_{item['日付'].replace('/','')}_{item['レース']}.csv",
                    mime="text/csv",
                    key=f"dl_{idx}"
                )
            with c_del:
                if st.button(f"この履歴を削除 #{idx+1}", key=f"del_{idx}"):
                    st.session_state['history'].pop(idx)
                    st.rerun()
else:
    st.info("上のタブで各レースのデータを入力し、「シミュレーション実行」を押してください。結果はここに自動で蓄積されます。")
