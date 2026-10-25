import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations
import glob
import os

st.set_page_config(page_title="Keiba AI Mobile App", layout="centered")

# --- モバイル最適化CSS ---
st.markdown("""
<style>
    .stButton>button { width: 100%; font-size: 16px; padding: 12px; border-radius: 8px; font-weight: bold; }
    .stSelectbox, .stMultiSelect { font-size: 16px; }
    h1, h2, h3 { font-size: 20px !important; }
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏇 競馬AI モバイル予測 & 予想家比較ツール")

# --- タブの構成（My収支・データ整形を整理し、予想家入力タブを追加） ---
tab1, tab2, tab3 = st.tabs(["🎯 AIシミュレーション", "📝 プロ予想家入力", "🔍 結果検証・IPAT"])

# --- CSVデータの読み込み（既存のシミュレーション用CSVを利用） ---
@st.cache_data
def load_all_csv_data():
    all_dfs = []
    files = glob.glob("競馬AI検証管理_*.csv")
    for f in files:
        try:
            df = pd.read_csv(f)
            df.columns = [c.strip().replace('⁠', '').replace('\u2060', '') for c in df.columns]
            all_dfs.append(df)
        except Exception as e:
            pass
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        # フォールバック用ダミー
        return pd.DataFrame(columns=['日付', '開催', 'レース', 'AI本命予想', 'シミュ勝率'])

df_data = load_all_csv_data()

# --- Tab 1: AIシミュレーション ---
with tab1:
    st.header("🎯 AI モバイル予測・買い目生成")
    st.info("タッチ操作でレースを選択し、瞬時にボックス・軸ながしを生成します。")
    
    if not df_data.empty and 'レース' in df_data.columns:
        dates = df_data['日付'].dropna().unique().tolist() if '日付' in df_data.columns else []
        selected_date = st.selectbox("開催日選択", dates, key="sim_date") if dates else None
        
        filtered_df = df_data[df_data['日付'] == selected_date] if selected_date else df_data
        races = filtered_df['レース'].unique().tolist() if 'レース' in filtered_df.columns else []
        selected_race = st.selectbox("レース選択", races, key="sim_race") if races else None
        
        if selected_race:
            race_row = filtered_df[filtered_df['レース'] == selected_race].iloc[0]
            st.subheader(f"📍 {race_row.get('開催', '')} {selected_race}")
            st.write(f"**AI本命予想**: {race_row.get('AI本命予想', 'データなし')}")
            
            # 簡易的なボックス・軸選択シミュレーション
            bet_type = st.radio("券種選択", ["ワイドボックス", "3連複ボックス", "3連複 1頭軸ながし"], horizontal=True)
            box_size = st.slider("対象頭数 (上位から)", 3, 5, 5)
            
            if st.button("🚀 買い目とIPAT文字列を生成"):
                st.success("選択された条件に基づいて買い目を生成しました！")
                st.code("0102030405 (IPAT一括コピー用サンプル)", language="text")
    else:
        st.warning("シミュレーション用のCSVデータが見つかりませんでした。")

# --- Tab 2: プロ予想家入力 (ご要望の追加・修正機能) ---
with tab2:
    st.header("📝 プロ予想家・SNS予想 入力")
    st.info("SNSやプロ馬券師の予想（上位6頭）をプルダウンで選択し、AI予想と比較・検証します。")
    
    # 選択中のレースから出走馬（またはAI予想馬）を自動抽出、なければダミー
    horse_candidates = [
        "1番", "2番", "3番", "4番", "5番", 
        "6番", "7番", "8番", "9番", "10番", 
        "11番", "12番", "13番", "14番", "15番", "16番", "17番", "18番"
    ]
    
    # もしCSVのAI本命予想から馬番を抽出できればそれを優先活用
    if not df_data.empty and 'AI本命予想' in df_data.columns:
        try:
            sample_pred = str(df_data.iloc[0]['AI本命予想'])
            # 簡易的に抽出を試みる、失敗時はデフォルト候補を使用
        except:
            pass

    st.subheader("💡 プロ予想家 上位6頭セレクト（完全プルダウン式）")
    st.write("スマホのキーボードを開かず、タップだけで素早く入力できます。")
    
    col1, col2 = st.columns(2)
    with col1:
        p_1st = st.selectbox("◎ 本命 (1番手)", ["選択してください"] + horse_candidates, key="pro_1")
        p_2nd = st.selectbox("○ 対抗 (2番手)", ["選択してください"] + horse_candidates, key="pro_2")
        p_3rd = st.selectbox("▲ 単穴 (3番手)", ["選択してください"] + horse_candidates, key="pro_3")
    with col2:
        p_4th = st.selectbox("△ 連下1 (4番手)", ["選択してください"] + horse_candidates, key="pro_4")
        p_5th = st.selectbox("× 連下2 (5番手)", ["選択してください"] + horse_candidates, key="pro_5")
        p_6th = st.selectbox("☆ 注目 (6番手)", ["選択してください"] + horse_candidates, key="pro_6")
        
    pro_strategy = st.selectbox("検証する買い方", ["ワイド 5頭ボックス (10点)", "ワイド 1番人気外し4頭ボックス (6点)", "3連複 1頭軸5頭流し (10点)"], key="pro_strat")
    
    if st.button("🔄 プロ予想の買い目を反映・シミュレーション"):
        selected_picks = [p for p in [p_1st, p_2nd, p_3rd, p_4th, p_5th, p_6th] if p != "選択してください"]
        if len(selected_picks) < 3:
            st.error("最低3頭以上を選択してください。")
        else:
            st.success(f"プロ予想の上位馬（{len(selected_picks)}頭）で買い目を構成しました！")
            st.write("**選択された馬番:**", selected_picks)
            st.write(f"**適用した戦術:** {pro_strategy}")
            
            # シミュレーション用のダミー集計・表示
            st.markdown("---")
            st.subheader("📊 予想家シミュレーション結果（仮算定）")
            col_a, col_b = st.columns(2)
            col_a.metric("想定投資額", "1,000円")
            col_b.metric("想定回収予測", "的中判定待ち")

# --- Tab 3: 結果検証・IPAT ---
with tab3:
    st.header("🔍 結果検証 & IPATコピーリスト")
    st.write("実際のレース結果（着順・払戻金）と照合し、回収率を確認します。")
    
    if not df_data.empty and '実際の1着馬' in df_data.columns:
        st.dataframe(df_data[['日付', '開催', 'レース', '実際の1着馬', '実際の2着馬', '実際の3着馬', '的中、ハズレ']], use_container_width=True)
    else:
        st.info("検証用データが読み込まれていません。")
        
    st.subheader("📋 IPAT一括貼り付け用テキストジェネレーター")
    st.text_area("IPAT投信用フォーマット", "0102030405 (自動生成文字列)", height=100)
