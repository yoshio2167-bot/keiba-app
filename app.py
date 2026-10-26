from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st
from itertools import combinations

st.set_page_config(page_title="競馬予想AIシミュレーター ＆ 予想家比較ボード", layout="wide", initial_sidebar_state="collapsed")

st.title("競馬予想AIシミュレーター ＆ 予想家比較ボード")

tab1, tab2, tab3 = st.tabs(["🚀 シミュレーション", "📊 結果照合・判定", "📝 プロ予想家入力・連動"])

with tab1:
  st.header("モンテカルロ・シミュレーション ＆ 5頭ボックス")
  st.write("出馬表CSVを貼り付けてボタンを押すだけで、高速に展開予測と5頭ボックス買い目、即PAT用リストを算出します。")

  col_s1, col_s2, col_s3 = st.columns(3)
  with col_s1:
    threshold_roi = st.slider("🎯 勝負見送りライン（期待回収率 % 未満をパス）", min_value=100, max_value=200, value=120, step=10)
  with col_s2:
    sim_count_input = st.selectbox("🔄 シミュレーション回数", options=["1回（一発ガチ予想）", "100回", "300回", "500回"], index=1)
  with col_s3:
    total_budget = st.number_input("💰 投資予算 (円)", min_value=500, max_value=50000, value=2000, step=500)

  if "1回" in sim_count_input:
    sim_count = 1
  elif "100回" in sim_count_input:
    sim_count = 100
  elif "300回" in sim_count_input:
    sim_count = 300
  else:
    sim_count = 500

  if "pasted_csv" not in st.session_state:
    st.session_state.pasted_csv = ""

  col_btn1, col_btn2 = st.columns([0.8, 0.2])
  with col_btn2:
    if st.button("🗑️ 一括削除", type="secondary"):
      st.session_state.pasted_csv = ""
      st.rerun()

  pasted_data = st.text_area(
      "CSVデータ貼り付け欄",
      value=st.session_state.pasted_csv,
      placeholder=(
          "日付,開催地,レース番号,距離・馬場,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "2026/10/18,京都,12R,ダ1400m(良),3歳以上2勝クラス,1,ショウナンハルヒ,8人気,12.0,差,35.5,80,0-1-0-4,団野大,56.0"
      ),
      height=150,
  )
  st.session_state.pasted_csv = pasted_data

  df_input = None
  if pasted_data.strip():
    try:
      lines = [line.strip() for line in pasted_data.strip().split("\n") if line.strip()]
      if len(lines) > 0:
        first_line = lines[0]
        has_header = "馬番" in first_line or "馬名" in first_line or "日付" in first_line
        data_lines = lines[1:] if has_header else lines

        parsed_rows = []
        for l in data_lines:
          parts = [p.strip() for p in l.split(",")]
          if len(parts) >= 15:
            parsed_rows.append({
                "日付": parts[0],
                "開催地": parts[1],
                "レース番号": parts[2],
                "距離・馬場": parts[3],
                "レース条件": parts[4],
                "馬番": parts[5],
                "馬名": parts[6],
                "人気": parts[7],
                "単勝オッズ": parts[8],
                "脚質": parts[9],
                "上がり3F": parts[10],
                "スピード指数": parts[11],
                "近走5走成績": parts[12],
                "騎手": parts[13],
                "斤量": parts[14],
            })

        if parsed_rows:
          df_input = pd.DataFrame(parsed_rows)

      if df_input is not None and not df_input.empty:
        def extract_num(val, default=5.0):
          try:
            s = str(val)
            if s == "nan" or not s.strip():
              return default
            m = re.search(r'([\d\.]+)', s)
            if m:
              return float(m.group(1))
          except:
            pass
          return default

        df_input["人気_num"] = df_input["人気"].apply(lambda x: extract_num(x, 5.0))
        df_input["オッズ_num"] = df_input["単勝オッズ"].apply(lambda x: extract_num(x, 15.0))
        df_input["上がり3F_val"] = df_input["上がり3F"].apply(lambda x: extract_num(x, 0.0))
        df_input["speed_val"] = df_input["スピード指数"].apply(lambda x: extract_num(x, 0.0))

        st.success(f"データを正常に読み込みました（全 {len(df_input)} 頭登録中）")

    except Exception as e:
      st.info("CSVデータを貼り付けるとここにステータスが表示されます。")

  if st.button("🚀 高精度AI解析・予想を実行", type="primary"):
    if df_input is not None and not df_input.empty:
      with st.spinner("高速解析中..."):
        df_res = df_input.copy()

        nige_senko_count = 0
        for _, row in df_res.iterrows():
          kyaku = str(row["脚質"])
          if any(k in kyaku for k in ["逃", "先行"]):
            nige_senko_count += 1

        total_horses = len(df_res)
        if nige_senko_count <= max(1, total_horses * 0.2):
          auto_pace_name = "スローペース（前残・先行有利）"
        elif nige_senko_count >= total_horses * 0.5:
          auto_pace_name = "ハイ・タフペース（差し・追込有利）"
        else:
          auto_pace_name = "平均ペース（バランス型）"

        def calc_high_precision_score(row):
          try:
            odds = float(row["オッズ_num"])
            if odds <= 0: odds = 10.0
          except:
            odds = 10.0
          
          try:
            pop = float(row["人気_num"])
          except:
            pop = 5.0

          base_score = max(10.0, 150.0 / (np.log(odds + 1.0) + 0.6))
          
          try:
            s_val = float(row["speed_val"])
            if s_val > 0:
              base_score += s_val * 0.8
              if pop >= 6:
                base_score += 12.0
          except:
            pass

          try:
            f_val = float(row["上がり3F_val"])
            if 30.0 <= f_val <= 42.0:
              base_score += (42.0 - f_val) * 10.0
          except:
            pass

          kyaku = str(row["脚質"])
          if "スロー" in auto_pace_name:
            if any(k in kyaku for k in ["逃", "先行"]):
              base_score += 20.0
          elif "ハイ・タフ" in auto_pace_name:
            if any(k in kyaku for k in ["差", "追"]):
              base_score += 22.0

          try:
            rec = str(row["近走5走成績"])
            parts_rec = [p for p in rec.split("-") if p.isdigit()]
            if len(parts_rec) > 0:
              recent_rank = int(parts_rec[0])
              if recent_rank == 1:
                base_score += 15.0
              elif recent_rank <= 3:
                base_score += 8.0
              elif recent_rank >= 10:
                base_score -= 8.0
          except:
            pass

          return base_score

        df_res["ベース評価"] = df_res.apply(calc_high_precision_score, axis=1)

        win_counts = np.zeros(len(df_res))
        place_counts = np.zeros(len(df_res))

        np.random.seed(42)
        scores_arr = df_res["ベース評価"].values
        actual_sims = max(1, sim_count)
        noise_scale = 0.0 if actual_sims == 1 else np.mean(scores_arr) * 0.3

        for _ in range(actual_sims):
          noise = np.random.normal(0, noise_scale, size=len(df_res))
          sim_scores = scores_arr + noise
          top_indices = np.argsort(sim_scores)[::-1]
          
          winner_idx = top_indices[0]
          win_counts[winner_idx] += 1

          placers = top_indices[: min(3, len(df_res))]
          for p_idx in placers:
            place_counts[p_idx] += 1

        df_res["シミュ勝率_str"] = ((win_counts / actual_sims) * 100).round(1).astype(str) + "%"
        df_res["シミュ複勝率_str"] = ((place_counts / actual_sims) * 100).round(1).astype(str) + "%"
        
        raw_win_rate = (win_counts / actual_sims) * 100
        df_res["AI期待回収率_str"] = ((raw_win_rate / 100) * df_res["オッズ_num"] * 100).round(1).astype(str) + "%"
        
        df_res["_win_num"] = raw_win_rate
        df_ranked = df_res.sort_values(by="_win_num", ascending=False).reset_index(drop=True)

        st.session_state.df_ranked = df_ranked
        st.session_state.total_budget = total_budget

        st.info(f"🤖 **【AI自動判定された展開】: {auto_pace_name}** （逃げ先行馬: {nige_senko_count}頭 / 登録数: {total_horses}頭）")
        st.subheader("📊 高精度予想・ランキング結果（上位5頭）")
        
        display_cols = [
            "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ",
            "シミュ勝率_str", "シミュ複勝率_str", "AI期待回収率_str", "脚質", "上がり3F", "スピード指数", "騎手"
        ]
        available_cols = [c for c in display_cols if c in df_ranked.columns]
        df_display = df_ranked[available_cols]
        st.dataframe(df_display, use_container_width=True, height=220)

        kaisai_title = str(df_display["開催地"].iloc[0]) if not df_display["開催地"].empty else "京都"
        r_num_title = str(df_ranked["レース番号"].iloc[0]) if not df_ranked["レース番号"].empty else "12R"
        file_prefix = f"{kaisai_title}{r_num_title}"

        top1 = df_ranked.iloc[0] if len(df_ranked) > 0 else None
        top2 = df_ranked.iloc[1] if len(df_ranked) > 1 else None
        top3 = df_ranked.iloc[2] if len(df_ranked) > 2 else None

        top1_str = f"◎{top1['馬番']}番 {top1['馬名']}" if top1 is not None else ""
        top2_str = f"〇{top2['馬番']}番 {top2['馬名']}" if top2 is not None else ""
        top3_str = f"▲{top3['馬番']}番 {top3['馬名']}" if top3 is not None else ""
        
        wide_1 = f"◎{top1['馬番']} - 〇{top2['馬番']}" if top1 is not None and top2 is not None else ""
        wide_2 = f"◎{top1['馬番']} - ▲{top3['馬番']}" if top1 is not None and top3 is not None else ""
        strict_buy_focus = f"【推奨ワイド2点】 {wide_1} / {wide_2}"

        num_bets_5box = 10
        bet_amount_5box = max(100, int((total_budget / 100 / num_bets_5box) * 100))
        
        ai_top5_list_str = " / ".join([f"{df_ranked.iloc[i]['馬番']}番 {df_ranked.iloc[i]['馬名']}" for i in range(min(5, len(df_ranked)))])
        
        top5_df_rows = [df_ranked.iloc[i] for i in range(min(5, len(df_ranked)))]
        top5_nums_int = []
        for r in top5_df_rows:
          try:
            top5_nums_int.append(int(r["馬番"]))
          except:
            pass
        
        ipat_lines = []
        if len(top5_nums_int) >= 3:
          for combo in combinations(sorted(top5_nums_int), 3):
            ipat_lines.append(f"{combo[0]}-{combo[1]}-{combo[2]}  ({bet_amount_5box}円)")
        ipat_text_block = "\n".join(ipat_lines)

        three_renpuku_focus = (
            f"【推奨3連複 5頭ボックス（全10点）】\n"
            f"  対象馬: {ai_top5_list_str}\n"
            f"  💡 **資金配分**: 1点あたり **{bet_amount_5box}円** （合計投資: {bet_amount_5box * num_bets_5box}円）"
        )

        try:
          roi_val_num = float(str(top1["AI期待回収率_str"]).replace("%", ""))
        except:
          roi_val_num = 100.0

        export_rows = []
        for _, row in df_ranked.iterrows():
          export_rows.append({
              "日付": row["日付"],
              "開催地": row["開催地"],
              "レース番号": row["レース番号"],
              "距離・馬場": row["距離・馬場"],
              "レース条件": row["レース条件"],
              "AI上位5頭予想": ai_top5_list_str if row.name == 0 else "",
              "シミュ勝率": row["シミュ勝率_str"],
              "シミュ複勝率": row["シミュ複勝率_str"],
              "AI期待回収率": row["AI期待回収率_str"],
              "実際の1着馬": "",
              "実際の2着馬": "",
              "実際の3着馬": "",
              "自動判定メモ": "",
              "馬番": row["馬番"],
              "馬名": row["馬名"],
              "人気": row["人気"],
              "単勝オッズ": row["単勝オッズ"],
              "脚質": row["脚質"],
              "上がり3F": row["上がり3F"],
              "スピード指数": row["スピード指数"],
              "近走5走成績": row["近走5走成績"],
              "騎手": row["騎手"],
              "斤量": row["斤量"]
          })

        df_export_final = pd.DataFrame(export_rows)

        csv_download_data = df_export_final.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 シミュレーション結果をCSVで保存",
            data=csv_download_data,
            file_name=f"{file_prefix}_sim_result.csv",
            mime="text/csv",
        )

        st.markdown("### 📋 即PAT入力用買い目リスト（ワンクリックコピー）")
        st.code(ipat_text_block, language="text")

        st.markdown("### 📋 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）")
        st.code(StringIO(df_export_final.to_csv(sep="\t", index=False)).getvalue(), language="text")

        st.subheader("🎯 勝負判定 ＆ 5頭ボックス買い目インフォ")
        if roi_val_num >= threshold_roi:
          st.success(f"🔥 **【勝負レース推奨】**\n\n{strict_buy_focus}\n\n{three_renpuku_focus}")
        else:
          st.warning(f"⚠️ **【見送り推奨】**\n\n{strict_buy_focus}\n\n{three_renpuku_focus}")
    else:
      st.warning("データが入力されていません。CSVデータを貼り付けてください。")

with tab2:
  st.header("実際のレース結果との照合・自動判定（5頭ボックス基準）")
  st.write("保存したシミュレーション結果（CSV）をアップロードし、実際の1〜3着馬を選択すると、上位5頭の中に3頭すべてが入っているか判定します。")

  uploaded_sim_file = st.file_uploader("1. シミュレーション結果CSVをアップロード", type=["csv"])

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.success("ファイルを読み込みました！")

    horse_options = [
        f"{row.get('馬番')}番 {row.get('馬名')} ({row.get('人気')}・単勝{row.get('単勝オッズ')}倍)"
        for _, row in df_saved.iterrows()
    ]

    date_val = str(df_saved["日付"].iloc[0]) if "日付" in df_saved.columns and not df_saved["日付"].empty else "2026-10-18"
    kaisai_val = str(df_saved["開催地"].iloc[0]) if "開催地" in df_saved.columns and not df_saved["開催地"].empty else "京都"
    r_num_val = str(df_saved["レース番号"].iloc[0]) if "レース番号" in df_saved.columns and not df_saved["レース番号"].empty else "12R"
    dist_val = str(df_saved["距離・馬場"].iloc[0]) if "距離・馬場" in df_saved.columns and not df_saved["距離・馬場"].empty else "ダ1400m(良)"
    cond_val = str(df_saved["レース条件"].iloc[0]) if "レース条件" in df_saved.columns and not df_saved["レース条件"].empty else "3歳以上2勝クラス"

    top1_row = df_saved.iloc[0]
    win_rate_val = str(top1_row.get("シミュ勝率", top1_row.get("シミュ勝率_str", "0%")))
    place_rate_val = str(top1_row.get("シミュ複勝率", top1_row.get("シミュ複勝率_str", "0%")))
    roi_val = str(top1_row.get("AI期待回収率", top1_row.get("AI期待回収率_str", "0%")))

    ai_top5_list = []
    for i in range(min(5, len(df_saved))):
      h_num = str(df_saved.iloc[i].get("馬番"))
      h_name = str(df_saved.iloc[i].get("馬名"))
      ai_top5_list.append({"num": h_num, "name": h_name})

    top5_display_str = " / ".join([f"{item['num']}番 {item['name']}" for item in ai_top5_list])

    st.subheader("2. 実際のレース結果（1〜3着）を選択")
    
    select_options = ["選択してください"] + horse_options

    actual_1st = st.radio("🥇 実際の1着馬", options=select_options, key="rad_1st")
    st.markdown("---")
    actual_2nd = st.radio("🥈 実際の2着馬", options=select_options, key="rad_2nd")
    st.markdown("---")
    actual_3rd = st.radio("🥉 実際の3着馬", options=select_options, key="rad_3rd")

    st.markdown("---")
    if st.button("🔍 5頭ボックスの的中を自動判定する"):
      if actual_1st == "選択してください" or actual_2nd == "選択してください" or actual_3rd == "選択してください":
        st.warning("実際の1着〜3着馬すべてを選択してください。")
      else:
        def get_umaban(sel_str):
          m = re.match(r"^(\d+)番", sel_str.strip())
          return m.group(1) if m else ""

        actual_nums = [
            get_umaban(actual_1st),
            get_umaban(actual_2nd),
            get_umaban(actual_3rd)
        ]

        top5_nums = [item["num"] for item in ai_top5_list]
        matched_horses = [num for num in actual_nums if num in top5_nums]
        match_count = len(matched_horses)

        if match_count == 3:
          auto_memo = "3連複的中！（上位5頭に1〜3着がすべて網羅）"
          badge_type = "success"
        elif match_count == 2:
          auto_memo = "惜しい外れ（上位5頭に2頭が該当）"
          badge_type = "warning"
        else:
          auto_memo = "外れ（上位5頭に1頭以下）"
          badge_type = "warning"

        st.markdown("---")
        st.subheader("📝 判定結果レポート")

        col_a, col_b = st.columns(2)
        with col_a:
          st.info(f"**【AI上位5頭予想】**\n\n{top5_display_str}")
        with col_b:
          st.markdown(f"**【実際の3着まで】**\n\n🥇 1着: {actual_1st}\n\n🥈 2着: {actual_2nd}\n\n🥉 3着: {actual_3rd}")

        if badge_type == "success":
          st.balloons()
          st.success(f"🎉 **【自動判定】 {auto_memo}**")
        else:
          st.warning(f"❌ **【自動判定】 {auto_memo}**")

        sheet_row_text = (
            f"{date_val}\t{kaisai_val}\t{r_num_val}\t{dist_val}\t{cond_val}\t{top5_display_str}\t{win_rate_val}\t{place_rate_val}\t{roi_val}\t{actual_1st}\t{actual_2nd}\t{actual_3rd}\t{auto_memo}"
        )

        st.markdown("### 📋 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）")
        st.code(sheet_row_text, language="text")

  else:
    st.info("まずはTab1で保存したCSVファイルをアップロードしてください。")

# --- Tab 3: プロ予想家入力 ＆ 実際の結果との紐づけ判定（完全版） ---
with tab3:
  st.header("📝 プロ予想家・SNS予想 入力 ＆ 結果紐づけ判定")
  st.info("Tab1でシミュレーションを実行すると馬データが連動します。さらに実際の1〜3着馬を選択することで、プロ予想の買い目が的中していたかをその場で自動判定できます。")

  if "df_ranked" in st.session_state and not st.session_state.df_ranked.empty:
    df_r = st.session_state.df_ranked
    horse_candidates_real = [f"{row['馬番']}番 {row['馬名']}" for _, row in df_r.iterrows()]

    st.subheader("1. プロ予想家 上位6頭セレクト（プルダウン式）")
    
    col1, col2 = st.columns(2)
    with col1:
      p_1st = st.selectbox("◎ 本命 (1番手)", ["選択してください"] + horse_candidates_real, key="pro_1")
      p_2nd = st.selectbox("○ 対抗 (2番手)", ["選択してください"] + horse_candidates_real, key="pro_2")
      p_3rd = st.selectbox("▲ 単穴 (3番手)", ["選択してください"] + horse_candidates_real, key="pro_3")
    with col2:
      p_4th = st.selectbox("△ 連下1 (4番手)", ["選択してください"] + horse_candidates_real, key="pro_4")
      p_5th = st.selectbox("× 連下2 (5番手)", ["選択してください"] + horse_candidates_real, key="pro_5")
      p_6th = st.selectbox("☆ 注目 (6番手)", ["選択してください"] + horse_candidates_real, key="pro_6")
        
    pro_strategy = st.selectbox(
        "検証する買い方", 
        [
            "ワイド 5頭ボックス (10点)", 
            "ワイド 1番人気外し4頭ボックス (6点)", 
            "3連複 1頭軸5頭流し (10点)",
            "3連複 5頭ボックス (10点)"
        ], 
        key="pro_strat"
    )

    st.markdown("---")
    st.subheader("2. 実際のレース結果（1〜3着）を選択")
    res_options = ["選択してください"] + horse_candidates_real
    pro_act_1st = st.selectbox("🥇 実際の1着馬", options=res_options, key="pro_act_1")
    pro_act_2nd = st.selectbox("🥈 実際の2着馬", options=res_options, key="pro_act_2")
    pro_act_3rd = st.selectbox("🥉 実際の3着馬", options=res_options, key="pro_act_3")

    if st.button("🔄 プロ予想の買い目生成 ＆ 的中判定を実行", type="primary"):
      selected_picks_raw = [p for p in [p_1st, p_2nd, p_3rd, p_4th, p_5th, p_6th] if p != "選択してください"]
      
      if len(selected_picks_raw) < 3:
        st.error("最低3頭以上を選択してください。")
      else:
        selected_nums = []
        for p in selected_picks_raw:
          m = re.match(r"^(\d+)番", p)
          if m:
            selected_nums.append(int(m.group(1)))

        budget_val = st.session_state.get("total_budget", 2000)
        
        # 買い目の構成と組み合わせ抽出
        if "ワイド" in pro_strategy and "5頭" in pro_strategy:
          box_horses = selected_nums[:5]
          pts = 10
          combos = list(combinations(sorted(box_horses), 2))
          bet_type_flag = "wide"
        elif "ワイド" in pro_strategy and "1番人気外し" in pro_strategy:
          box_horses = selected_nums[:4]
          pts = 6
          combos = list(combinations(sorted(box_horses), 2))
          bet_type_flag = "wide"
        elif "3連複" in pro_strategy and "1頭軸" in pro_strategy:
          axis = selected_nums[0]
          opp = selected_nums[:6]
          if axis in opp:
            opp.remove(axis)
          opp = opp[:5]
          pts = 10
          combos = [(axis, c[0], c[1]) for c in combinations(sorted(opp), 2)]
          bet_type_flag = "sanrenpuku"
        else: # 3連複 5頭ボックス
          box_horses = selected_nums[:5]
          pts = 10
          combos = list(combinations(sorted(box_horses), 3))
          bet_type_flag = "sanrenpuku"

        bet_amt = max(100, int((budget_val / 100 / pts) * 100))
        total_inv = pts * bet_amt

        # 実際の着順馬番を取得
        def parse_num(sel):
          m = re.match(r"^(\d+)番", str(sel))
          return int(m.group(1)) if m else None

        a1 = parse_num(pro_act_1st)
        a2 = parse_num(pro_act_2nd)
        a3 = parse_num(pro_act_3rd)

        is_hit = False
        hit_combo_str = ""

        if a1 and a2 and a3:
          actual_top3_set = {a1, a2, a3}
          
          if bet_type_flag == "wide":
            for c in combos:
              if c[0] in actual_top3_set and c[1] in actual_top3_set:
                is_hit = True
                hit_combo_str = f"{c[0]}-{c[1]}"
                break
          else:
            for c in combos:
              if set(c) == actual_top3_set:
                is_hit = True
                hit_combo_str = f"{c[0]}-{c[1]}-{c[2]}"
                break

        st.markdown("---")
        st.subheader("📊 プロ予想家 連動判定結果")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("想定投資額", f"{total_inv:,} 円")
        col_b.metric("買い目点数", f"{pts} 点")
        
        if a1 and a2 and a3:
          if is_hit:
            col_c.metric("判定結果", "🎉 的中！", delta="Hit")
            st.success(f"🎉 おめでとうございます！ プロ予想の買い目（{hit_combo_str}）が的中しました！")
          else:
            col_c.metric("判定結果", "❌ 外れ", delta="-100%", delta_color="inverse")
            st.warning("❌ 残念ながら今回のプロ予想の買い目はハズレとなりました。")
        else:
          col_c.metric("判定結果", "判定待ち", delta="結果未入力")
          st.info("実際の1〜3着馬を選択すると、自動で的中判定が行われます。")

        ipat_list = []
        for c in combos:
          if len(c) == 2:
            ipat_list.append(f"{c[0]}-{c[1]}  ({bet_amt}円)")
          else:
            ipat_list.append(f"{c[0]}-{c[1]}-{c[2]}  ({bet_amt}円)")

        st.markdown("### 📋 即PAT入力用買い目リスト（プロ予想版）")
        st.code("\n".join(ipat_list), language="text")

  else:
    st.info("⚠️ まだTab1で「高精度AI解析・予想を実行」が行われていません。まずはTab1でシミュレーションを実行してください。")
