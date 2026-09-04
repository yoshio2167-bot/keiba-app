import streamlit as st
import pandas as pd
import io
import random
from datetime import date

st.set_page_config(page_title="中央競馬AI予想", layout="wide")

# スマホ画面で表が綺麗に収まり、縦スクロールや切れを防ぐすっきりとしたスタイル
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

        df = None
        if pasted:
            try:
                df = pd.read_csv(io.StringIO(pasted))
            except Exception as e:
                pass

        loc_default = 1
        if pasted and "札幌" in pasted:
            loc_default = 8
        elif pasted and "東京" in pasted:
            loc_default = 2
        elif pasted and "中山" in pasted:
            loc_default = 0

        class_default = 1
        if pasted and "新馬" in pasted:
            class_default = 0
        elif pasted and ("G3" in pasted or "G2" in pasted or "G1" in pasted):
            class_default = 7

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
            r_loc = st.selectbox(f"場#{i+1}", locations, index=loc_default, key=f"loc_{i}")
            r_class = st.selectbox(f"級#{i+1}", classes, index=class_default, key=f"class_{i}")
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
            sim_df = sim_df.set_index('馬番')

            batch_results.append({
                '日付': rc['date'],
                'レース': rc['title'],
                '開催情報': rc['condition'],
                '結果df': sim_df
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
            # 行数に合わせて完全に収まる高さに自動調整（途中で切れないように設定）
            row_count = len(item['結果df'])
            calc_height = row_count * 35 + 38
            
            st.dataframe(item['結果df'], use_container_width=True, height=calc_height)
            
            if st.button(f"この結果を削除 (#{idx+1})", key=f"del_{idx}", use_container_width=True):
                st.session_state['history'].pop(idx)
                st.rerun()
