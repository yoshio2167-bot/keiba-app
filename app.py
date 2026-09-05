import streamlit as st
import pandas as pd
import io
import random
from datetime import date

st.set_page_config(page_title="中央競馬AI予想", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding: 0.5rem 0.5rem !important;
        max-width: 100% !important;
    }
    table {
        font-size: 11px !important;
    }
    th, td {
        padding: 4px 6px !important;
        text-align: center !important;
    }
    h1 {
        font-size: 1.1rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 4px 8px;
        font-size: 11px;
    }
    p, label {
        font-size: 11px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏇 AI予想シミュレータ")

if 'history' not in st.session_state:
    st.session_state['history'] = []

st.sidebar.header("⚙️ 設定")
num_races = st.sidebar.slider("レース数", min_value=1, max_value=5, value=3)

race_tabs = st.tabs([f"第{i+1}R" for i in range(num_races)])

race_configs = []

distances = ["1000m", "1200m", "1400m", "1600m", "1800m", "2000m", "2200m", "2400m", "2500m", "3000m", "3200m"]
locations = ["中山", "阪神", "東京", "中京", "京都", "新潟", "小倉", "福島", "札幌", "函館"]
classes = ["新馬", "未勝利", "1勝クラス", "2勝クラス", "3勝クラス", "オープン", "L", "G3", "G2", "G1"]
conds = ["良", "稍重", "重", "不良"]
paces = ["ミドル", "スロー", "ハイ"]

for i, tab in enumerate(race_tabs):
    with tab:
        pasted = st.text_area(f"ペースト #{i+1}", height=70, value="", key=f"text_{i}", placeholder="CSVデータをここにペースト")

        loc_idx = 1
        if pasted:
            if "札幌" in pasted: loc_idx = locations.index("札幌")
            elif "東京" in pasted: loc_idx = locations.index("東京")
            elif "中山" in pasted: loc_idx = locations.index("中山")
            elif "京都" in pasted: loc_idx = locations.index("京都")
            elif "中京" in pasted: loc_idx = locations.index("中京")
            elif "新潟" in pasted: loc_idx = locations.index("新潟")
            elif "小倉" in pasted: loc_idx = locations.index("小倉")
            elif "福島" in pasted: loc_idx = locations.index("福島")
            elif "函館" in pasted: loc_idx = locations.index("函館")
            elif "阪神" in pasted: loc_idx = locations.index("阪神")

        class_idx = 1
        if pasted:
            if "新馬" in pasted: class_idx = classes.index("新馬")
            elif "G3" in pasted: class_idx = classes.index("G3")
            elif "G2" in pasted: class_idx = classes.index("G2")
            elif "G1" in pasted: class_idx = classes.index("G1")
            elif "オープン" in pasted or "OP" in pasted: class_idx = classes.index("オープン")
            elif "1勝クラス" in pasted: class_idx = classes.index("1勝クラス")
            elif "2勝クラス" in pasted: class_idx = classes.index("2勝クラス")
            elif "3勝クラス" in pasted: class_idx = classes.index("3勝クラス")

        df = None
        if pasted:
            try:
                df = pd.read_csv(io.StringIO(pasted))
            except Exception as e:
                pass

        auto_pace_index = 0
        if df is not None and '脚質' in df.columns:
            kyaku_list = df['脚質'].astype(str).tolist()
            nige_count = sum(1 for k in kyaku_list if '逃げ' in k)
            senko_count = sum(1 for k in kyaku_list if '先行' in k)
            if nige_count >= 2 or (nige_count + senko_count) >= 5:
                auto_pace_index = 2
            elif nige_count <= 1 and senko_count <= 2:
                auto_pace_index = 1

        c1, c2, c3 = st.columns(3)
        with c1:
            r_loc = st.selectbox(f"場#{i+1}", locations, index=loc_idx, key=f"loc_{i}")
            r_class = st.selectbox(f"級#{i+1}", classes, index=class_idx, key=f"class_{i}")
        with c2:
            r_num = st.selectbox(f"R#{i+1}", [f"{n}R" for n in range(1, 13)], index=9+i if i<3 else i, key=f"num_{i}")
            r_surface = st.selectbox(f"コ#{i+1}", ["芝", "ダート", "障害"], index=0 if i!=1 else 1, key=f"surf_{i}")
        with c3:
            r_dist = st.selectbox(f"距#{i+1}", distances, index=3 if i!=1 else 2, key=f"dist_{i}")
            r_cond = st.selectbox(f"天#{i+1}", conds, index=0, key=f"cond_{i}")

        r_pace = st.selectbox(f"ペース #{i+1}", paces, index=auto_pace_index, key=f"pace_{i}")

        r_title = f"{r_loc}{r_num} ({r_class})"
        r_cond_str = f"{r_surface}{r_dist} ({r_cond}・{r_pace}ペース)"

        race_configs.append({
            'index': i+1,
            'date': date(2026, 9, 5).strftime('%Y/%m/%d'),
            'title': r_title,
            'condition': r_cond_str,
            'pace': r_pace,
            'df': df
        })

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 一括シミュレーション実行", type="primary", use_container_width=True):
    batch_results = []
    
    for rc in race_configs:
        if rc['df'] is not None:
            df = rc['df'].copy()
            
            if '間隔(週)' in df.columns:
                df['間隔スコア'] = df['間隔(週)'].apply(lambda w: 10 if 2 <= w <= 8 else (8 if w <= 16 else 6))
            else:
                df['間隔スコア'] = 8

            if '前走不利' in df.columns:
                df['不利補正'] = df['前走不利'].apply(lambda x: 1.05 if x == 1 or x == True or str(x).lower()=='true' else 1.0)
            else:
                df['不利補正'] = 1.0

            def calc_kishou(val):
                if pd.isna(val):
                    return 1.0
                s = str(val).strip()
                if s in ['気性難', '悪', '入れ込み']:
                    return 0.95
                elif s in ['おっとり', '優', '穏和', '安定']:
                    return 1.03
                try:
                    return float(val)
                except:
                    return 1.0

            if '気性' in df.columns:
                df['気性補正'] = df['気性'].apply(calc_kishou)
            else:
                df['気性補正'] = 1.0

            def calc_pace_coeff(row, pace_type):
                kyaku = str(row.get('脚質', '差し'))
                if pace_type == 'スロー':
                    if '逃げ' in kyaku: return 1.08
                    elif '先行' in kyaku: return 1.04
                    elif '追込' in kyaku: return 0.95
                    else: return 1.0
                elif pace_type == 'ハイ':
                    if '追込' in kyaku or '差し' in kyaku: return 1.06
                    elif '逃げ' in kyaku: return 0.93
                    else: return 0.98
                else:
                    return 1.0

            pace_type = rc['pace']
            df['展開補正'] = df.apply(lambda r: calc_pace_coeff(r, pace_type), axis=1)

            df['AIスコア'] = (
                (
                    df['スピード指数'] * 0.30 +
                    df['距離適性'] * 0.15 +
                    df['スタミナ'] * 0.10 +
                    (df['騎手勝率'] * 100) * 0.13 +
                    (10 / df['直近5走平均着順']) * 0.10 +
                    df['間隔スコア'] * 0.10
                ) * df['不利補正'] * df['気性補正'] * df['展開補正']
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
                    '馬番': int(info['馬番']) if pd.notna(info['馬番']) else 0,
                    '馬名': name,
                    'オッズ': info['単勝オッズ'],
                    '勝回': info['勝利回数'],
                    '複回': info['3位以内回数']
                })

            sim_df = pd.DataFrame(sim_list).sort_values(by='勝回', ascending=False).reset_index(drop=True)
            
            # 3連複5点買い目の自動算出
            top_horses = sim_df.head(5)
            trio_bets = []
            if len(top_horses) >= 4:
                b1 = top_horses.iloc[0]['馬番']
                b2 = top_horses.iloc[1]['馬番']
                b3 = top_horses.iloc[2]['馬番']
                b4 = top_horses.iloc[3]['馬番']
                b5 = top_horses.iloc[4]['馬番'] if len(top_horses) >= 5 else b4
                trio_bets = [
                    f"① 軸: {b1} - 相手: {b2}, {b3}",
                    f"② 軸: {b1} - 相手: {b2}, {b4}",
                    f"③ 軸: {b1} - 相手: {b3}, {b4}",
                    f"④ 軸: {b1} - 相手: {b2}, {b5}",
                    f"⑤ 軸2頭: {b1},{b2} - 相手: {b3},{b4},{b5}"
                ]

            sim_df = sim_df.set_index('馬番')

            batch_results.append({
                '日付': rc['date'],
                'レース': rc['title'],
                '開催情報': rc['condition'],
                '結果df': sim_df,
                '買い目': trio_bets
            })

    if batch_results:
        for res in batch_results:
            st.session_state['history'].append(res)
        st.success("🎉 シミュレーション完了！")
    else:
        st.warning("有効なデータがありません。")

if st.session_state['history']:
    st.markdown("---")
    st.subheader("📂 予想結果一覧")
    
    if st.button("🗑️ すべての履歴をクリア", use_container_width=True):
        st.session_state['history'] = []
        st.rerun()

    for idx, item in enumerate(st.session_state['history']):
        with st.expander(f"#{idx+1} {item['レース']} ({item['開催情報']})", expanded=(idx==len(st.session_state['history'])-1)):
            row_count = len(item['結果df'])
            calc_height = row_count * 35 + 38
            
            st.dataframe(item['結果df'], use_container_width=True, height=calc_height)
            
            if item.get('買い目'):
                st.markdown("<span style='font-size:10px; color:#aaa;'>💡 おすすめ3連複5点</span>", unsafe_allow_html=True)
                for bet in item['買い目']:
                    st.markdown(f"<span style='font-size:10px;'>{bet}</span>", unsafe_allow_html=True)
            
            if st.button(f"この結果を削除 (#{idx+1})", key=f"del_{idx}", use_container_width=True):
                st.session_state['history'].pop(idx)
                st.rerun()
