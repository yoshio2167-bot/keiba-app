from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター（高精度版）", layout="wide", initial_sidebar_state="collapsed")

st.title("競馬予想AIシミュレーター ＆ 高精度回収率フィルター")

tab1, tab2, tab3 = st.tabs(["🚀 100回シミュレーション＆厳選予想", "📊 結果照合・自動判定検証", "🛠️ 出馬表データ整形ツール"])

with tab1:
  st.header("モンテカルロ・シミュレーション ＆ 期待回収率フィルター")
  st.write(
      "出馬表CSVを貼り付けると、オッズ・上がり3F・近走実績を多角的に解析し、ヤキトリを防ぐための『勝負レース判定』と『厳選ワイド買い目』を自動算出します。"
  )

  # サイドバーまたは設定エリアでフィルタースレッショルドを調整可能に
  col_s1, col_s2 = st.columns(2)
  with col_s1:
    threshold_roi = st.slider("🎯 勝負見送りライン（期待回収率 % 未満をパス）", min_value=100, max_value=200, value=120, step=10)
  with col_s2:
    sim_count = st.selectbox("🔄 モンテカルロ試行回数", options=[100, 300, 500], index=0)

  pasted_data = st.text_area(
      "CSVデータ貼り付け欄",
      placeholder=(
          "日付,開催地,レース番号,距離・馬場,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "2026/09/06,阪神,11R,芝1200m(良),セントウルS G2,1,ママコチャ,5人気,10.8,先,0,0,7-5-3-10,武豊,56.0"
      ),
      height=180,
  )

  df_input = None
  if pasted_data:
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
            row_dict = {
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
            }
            parsed_rows.append(row_dict)

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
        
        preview_cols = [
            "日付", "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ", "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        available_preview = [c for c in preview_cols if c in df_input.columns]
        st.dataframe(df_input[available_preview], use_container_width=True)

    except Exception as e:
      st.info("CSVデータを貼り付けるとここにプレビューが表示されます。")

  if st.button("🚀 高精度シミュレーション＆予想を実行", type="primary"):
    if df_input is not None and not df_input.empty:
      with st.spinner(f"{sim_count}回の模擬レース（モンテカルロ法）を高精度解析中..."):
        df_res = df_input.copy()

        def calc_enhanced_score(row):
          try:
            odds = float(row["オッズ_num"])
            if odds <= 0: odds = 10.0
          except:
            odds = 10.0
          
          # オッズの歪みを補正しつつ、実力・人気バランスを最適化
          base_score = max(10.0, 160.0 / (np.log(odds + 1.0) + 0.7))
          
          # 上がり3Fのスピード評価を反映
          try:
            f_val = float(row["上がり3F_val"])
            if 30.0 <= f_val <= 42.0:
              base_score += (40.0 - f_val) * 7.0
          except:
            pass

          # 近走成績の好走度（最初の一桁の数字が小さいほど良い等）の簡易ボーナス
          try:
            rec = str(row["近走5走成績"])
            first_num = int(rec.split("-")[0]) if "-" in rec and rec.split("-")[0].isdigit() else 5
            if first_num <= 3:
              base_score += (4 - first_num) * 3.0
          except:
            pass

          return base_score

        df_res["ベース評価"] = df_res.apply(calc_enhanced_score, axis=1)

        win_counts = np.zeros(len(df_res))
        place_counts = np.zeros(len(df_res))

        np.random.seed(42)
        scores_arr = df_res["ベース評価"].values
        for _ in range(sim_count):
          noise = np.random.normal(0, np.mean(scores_arr) * 0.4, size=len(df_res))
          sim_scores = scores_arr + noise
          top_indices = np.argsort(sim_scores)[::-1]
          
          winner_idx = top_indices[0]
          win_counts[winner_idx] += 1

          placers = top_indices[: min(3, len(df_res))]
          for p_idx in placers:
            place_counts[p_idx] += 1

        df_res["シミュ勝率_str"] = ((win_counts / sim_count) * 100).round(1).astype(str) + "%"
        df_res["シミュ複勝率_str"] = ((place_counts / sim_count) * 100).round(1).astype(str) + "%"
        
        raw_win_rate = (win_counts / sim_count) * 100
        df_res["AI期待回収率_str"] = ((raw_win_rate / 100) * df_res["オッズ_num"] * 100).round(1).astype(str) + "%"
        
        df_res["_win_num"] = raw_win_rate
        df_ranked = df_res.sort_values(by="_win_num", ascending=False).reset_index(drop=True)

        st.subheader("📊 シミュレーション・ランキング結果（高精度版）")
        
        display_cols = [
            "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ",
            "シミュ勝率_str", "シミュ複勝率_str", "AI期待回収率_str", "脚質", "上がり3F", "騎手"
        ]
        available_cols = [c for c in display_cols if c in df_ranked.columns]
        df_display = df_ranked[available_cols]
        st.dataframe(df_display, use_container_width=True)

        kaisai_title = str(df_display["開催地"].iloc[0]) if not df_display["開催地"].empty else "阪神"
        r_num_title = str(df_ranked["レース番号"].iloc[0]) if not df_ranked["レース番号"].empty else "11R"
        file_prefix = f"{kaisai_title}{r_num_title}"

        top1 = df_ranked.iloc[0] if len(df_ranked) > 0 else None
        top2 = df_ranked.iloc[1] if len(df_ranked) > 1 else None
        top3 = df_ranked.iloc[2] if len(df_ranked) > 2 else None

        top1_str = f"◎{top1['馬番']}番 {top1['馬名']}" if top1 is not None else ""
        top2_str = f"〇{top2['馬番']}番 {top2['馬名']}" if top2 is not None else ""
        top3_str = f"▲{top3['馬番']}番 {top3['馬名']}" if top3 is not None else ""
        ai_top3_combined = f"{top1_str} / {top2_str} / {top3_str}"

        wide_1 = f"◎{top1['馬番']} - 〇{top2['馬番']}" if top1 is not None and top2 is not None else ""
        wide_2 = f"◎{top1['馬番']} - ▲{top3['馬番']}" if top1 is not None and top3 is not None else ""
        strict_buy_focus = f"【推奨ワイド2点】 {wide_1} / {wide_2}"

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
              "AI上位3頭予想": ai_top3_combined if row.name == 0 else "",
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
            file_name=f"{file_prefix}_sim_highacc.csv",
            mime="text/csv",
        )

        tsv_buffer = StringIO()
        df_export_final.to_csv(tsv_buffer, sep="\t", index=False)
        sim_copy_text = tsv_buffer.getvalue()

        st.markdown(
            "### 📋 シミュレーション結果 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）"
        )
        st.code(sim_copy_text, language="text")

        st.subheader("🎯 勝負判定 ＆ 推奨買い目インフォ")
        if roi_val_num >= threshold_roi:
          st.success(f"🔥 **【勝負レース推奨】（期待回収率: {top1['AI期待回収率_str']} ＞ 設定基準 {threshold_roi}%）**\n\n{strict_buy_focus}\n\n※期待値が高いため、ワイド2点勝負で高回収を狙えます。")
        else:
          st.warning(f"⚠️ **【見送り推奨 / パス】（期待回収率: {top1['AI期待回収率_str']} ＜ 設定基準 {threshold_roi}%）**\n\n{strict_buy_focus}\n\n※期待回収率が基準未満です。無駄な投資を避けるため、このレースは見送り（パス）が賢明です。")
    else:
      st.warning("データが入力されていません。CSVデータを貼り付けてください。")

with tab2:
  st.header("実際のレース結果との照合・自動判定")
  st.write("保存したシミュレーション結果（CSV）をアップロードし、実際の1〜3着馬を選択すると、的中状況を自動判定します。")

  uploaded_sim_file = st.file_uploader("1. シミュレーション結果CSVをアップโหลด", type=["csv"])

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.success("ファイルを読み込みました！")

    horse_options = [
        f"{row.get('馬番')}番 {row.get('馬名')} ({row.get('人気')}・単勝{row.get('単勝オッズ')}倍)"
        for _, row in df_saved.iterrows()
    ]

    date_val = str(df_saved["日付"].iloc[0]) if "日付" in df_saved.columns and not df_saved["日付"].empty else "2026/09/06"
    kaisai_val = str(df_saved["開催地"].iloc[0]) if "開催地" in df_saved.columns and not df_saved["開催地"].empty else "阪神"
    r_num_val = str(df_saved["レース番号"].iloc[0]) if "レース番号" in df_saved.columns and not df_saved["レース番号"].empty else "11R"
    dist_val = str(df_saved["距離・馬場"].iloc[0]) if "距離・馬場" in df_saved.columns and not df_saved["距離・馬場"].empty else "芝1200m(良)"
    cond_val = str(df_saved["レース条件"].iloc[0]) if "レース条件" in df_saved.columns and not df_saved["レース条件"].empty else "セントウルS G2"

    top1_row = df_saved.iloc[0]
    win_rate_val = str(top1_row.get("シミュ勝率", top1_row.get("シミュ勝率_str", "0%")))
    place_rate_val = str(top1_row.get("シミュ複勝率", top1_row.get("シミュ複勝率_str", "0%")))
    roi_val = str(top1_row.get("AI期待回収率", top1_row.get("AI期待回収率_str", "0%")))

    ai_top3_list = []
    for i in range(min(3, len(df_saved))):
      h_num = str(df_saved.iloc[i].get("馬番"))
      h_name = str(df_saved.iloc[i].get("馬名"))
      ai_top3_list.append({"num": h_num, "name": h_name})

    t1 = f"◎{ai_top3_list[0]['num']}番 {ai_top3_list[0]['name']}" if len(ai_top3_list) > 0 else ""
    t2 = f"〇{ai_top3_list[1]['num']}番 {ai_top3_list[1]['name']}" if len(ai_top3_list) > 1 else ""
    t3 = f"▲{ai_top3_list[2]['num']}番 {ai_top3_list[2]['name']}" if len(ai_top3_list) > 2 else ""
    ai_top3_str = f"{t1} / {t2} / {t3}"

    st.subheader("2. 実際のレース結果（1〜3着）を選択")
    col1, col2, col3 = st.columns(3)
    with col1:
      actual_1st = st.selectbox("🥇 実際の1着馬", options=["選択してください"] + horse_options, index=0)
    with col2:
      actual_2nd = st.selectbox("🥈 実際の2着馬", options=["選択してください"] + horse_options, index=0)
    with col3:
      actual_3rd = st.selectbox("🥉 実際の3着馬", options=["選択してください"] + horse_options, index=0)

    if st.button("🔍 検証結果を自動判定する"):
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

        hit_horses = []
        for item in ai_top3_list:
          if item["num"] in actual_nums:
            hit_horses.append(f"{item['num']}番 {item['name']}")

        hit_count = len(hit_horses)

        if hit_count >= 2:
          auto_memo = f"的中（上位3頭から {hit_count}頭が馬券内絡み・ワイド的中圏内）"
          badge_type = "success"
        elif hit_count == 1:
          auto_memo = f"的中（上位3頭から {hit_count}頭が馬券内絡み）"
          badge_type = "success"
        else:
          auto_memo = "不格外れ（上位3頭がすべて馬券外）"
          badge_type = "warning"

        st.markdown("---")
        st.subheader("📝 判定結果レポート")

        col_a, col_b = st.columns(2)
        with col_a:
          st.info(f"**【AI上位3頭予想】**\n\n{ai_top3_str}")
        with col_b:
          st.markdown(f"**【実際の3着まで】**\n\n🥇 1着: {actual_1st}\n\n🥈 2着: {actual_2nd}\n\n🥉 3着: {actual_3rd}")

        if badge_type == "success":
          st.balloons()
          st.success(f"🎉 **【自動判定】 {auto_memo}**")
        else:
          st.warning(f"❌ **【自動判定】 {auto_memo}**")

        sheet_row_text = (
            f"{date_val}\t{kaisai_val}\t{r_num_val}\t{dist_val}\t{cond_val}\t{ai_top3_str}\t{win_rate_val}\t{place_rate_val}\t{roi_val}\t{actual_1st}\t{actual_2nd}\t{actual_3rd}\t{auto_memo}"
        )

        st.markdown("### 📋 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）")
        st.code(sheet_row_text, language="text")

  else:
    st.info("まずはTab1で保存したCSVファイルをアップロードしてください。")

with tab3:
  st.header("🛠️ 出馬表テキスト・CSV整形ツール")
  st.write("カンマ区切りの出馬表データをここに貼り付けると、15列の正しいフォーマットに完璧に整えます。")

  raw_txt = st.text_area(
      "ここにカンマ区切りの出馬表データを貼り付け",
      placeholder="2026/09/06,阪神,11R,芝1200m(良),セントウルS G2,1,ママコチャ...",
      height=150,
  )

  if st.button("✨ 完璧なCSVに変換する"):
    if raw_txt:
      lines = [l.strip() for l in raw_txt.strip().split("\n") if l.strip()]
      parsed_rows = []
      for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
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
        df_converted = pd.DataFrame(parsed_rows)
        cols_order = [
            "日付", "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ",
            "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        csv_text = df_converted[cols_order].to_csv(index=False)
        st.success("変換が完了しました！下のボックスをコピーしてTab1に貼り付けてください。")
        st.text_area("整形済みCSV出力（ワンタップ選択）", value=csv_text, height=150)
      else:
        st.warning("有効な行が見つかりませんでした。データ形式を確認してください。")
    else:
      st.warning("テキストが入力されていません。")
