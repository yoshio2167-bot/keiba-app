from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide", initial_sidebar_state="collapsed")

st.title("競馬予想AIシミュレーター ＆ 精度検証ツール")

tab1, tab2, tab3 = st.tabs(["🚀 シミュレーション＆予想", "📊 結果照合・検証", "🛠️ テキスト整形ツール"])

with tab1:
  st.header("100回モンテカルロ・シミュレーション")
  st.write(
      "出馬表CSVを貼り付けると、100回の模擬レースを実行し、勝率・複勝率・回収率を算出してスプレッドシート用テキストで保存できます。"
  )

  pasted_data = st.text_area(
      "CSVデータ貼り付け欄",
      placeholder=(
          "開催地,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "阪神,5R 芝1800m(良) 2歳新馬,1,リスグロワール,2人気,3.9,,,,0-0-0-0,レーン,55.0"
      ),
      height=180,
  )

  df_input = None
  if pasted_data:
    try:
      lines = [line.strip() for line in pasted_data.strip().split("\n") if line.strip()]
      if len(lines) > 0:
        csv_io = StringIO("\n".join(lines))
        df_input = pd.read_csv(csv_io)

      if df_input is not None and not df_input.empty:
        # 不足している列があれば安全に空欄で追加
        expected_cols = [
            "開催地", "レース条件", "馬番", "馬名", "人気", "単勝オッズ",
            "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        for col in expected_cols:
          if col not in df_input.columns:
            df_input[col] = ""

        # レース条件から分解するための抽出用カラムを内部で用意
        r_num_list = []
        dist_list = []
        cond_list = []

        for idx, row in df_input.iterrows():
          raw_cond = str(row.get("レース条件", ""))
          r_num = "5R"
          dist = "芝1800m(良)"
          cond = "2歳新馬"
          
          m_r = re.search(r'(\d+R)', raw_cond)
          if m_r:
            r_num = m_r.group(1)
            raw_cond = raw_cond.replace(r_num, "").strip()
          
          parts = raw_cond.split()
          if len(parts) > 0:
            dist = parts[0]
          if len(parts) > 1:
            cond = " ".join(parts[1:])
          elif len(parts) == 1 and not m_r:
            cond = parts[0]

          r_num_list.append(r_num)
          dist_list.append(dist)
          cond_list.append(cond)

        df_input["_レース番号"] = r_num_list
        df_input["_距離馬場"] = dist_list
        df_input["_詳細条件"] = cond_list
        df_input["_日付"] = "2026/09/06"

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
        df_input["上がり3F_val"] = df_input["上がり3F"].apply(lambda x: extract_num(x, 35.5))
        df_input["speed_val"] = df_input["スピード指数"].apply(lambda x: extract_num(x, 0.0))

        st.success(f"データを正常に読み込みました（全 {len(df_input)} 頭登録中）")
        
        # プレビューは元の列並びのままスッキリ表示
        st.dataframe(df_input[expected_cols], use_container_width=True)

    except Exception as e:
      st.info("CSVデータを貼り付けるとここにプレビューが表示されます。")

  if st.button("🚀 100回シミュレーション＆予想実行", type="primary"):
    if df_input is not None and not df_input.empty:
      with st.spinner("100回の模擬レース（モンテカルロ法）を集計中..."):
        df_res = df_input.copy()

        def calc_speed_index(row):
          try:
            val = float(row["speed_val"])
            if val > 0:
              return val
          except:
            pass
          base_idx = 70.0
          up_time = float(row["上がり3F_val"])
          base_idx += (37.0 - up_time) * 4.0
          recent = str(row.get("近走5走成績", "0-0-0-0"))
          wins = recent.count("1")
          base_idx += wins * 3.0
          pop_bonus = max(0, (11 - float(row["人気_num"])) * 1.5)
          return round(max(50.0, min(100.0, base_idx + pop_bonus)), 1)

        df_res["スピード指数_calc"] = df_res.apply(calc_speed_index, axis=1)

        df_res["ベース評価"] = (
            df_res["スピード指数_calc"] * 0.7 + (37.0 - df_res["上がり3F_val"]) * 5.0
        )

        n_simulations = 100
        win_counts = np.zeros(len(df_res))
        place_counts = np.zeros(len(df_res))

        np.random.seed(42)
        for _ in range(n_simulations):
          noise = np.random.normal(
              0, df_res["ベース評価"].values * 0.1, size=len(df_res)
          )
          sim_scores = df_res["ベース評価"].values + noise
          top_indices = np.argsort(sim_scores)[::-1]
          winner_idx = top_indices[0]
          win_counts[winner_idx] += 1

          placers = top_indices[: min(3, len(df_res))]
          for p_idx in placers:
            place_counts[p_idx] += 1

        df_res["シミュ勝率_str"] = ((win_counts / n_simulations) * 100).round(1).astype(str) + "%"
        df_res["シミュ複勝率_str"] = ((place_counts / n_simulations) * 100).round(1).astype(str) + "%"
        
        raw_win_rate = (win_counts / n_simulations) * 100
        df_res["AI期待回収率_str"] = ((raw_win_rate / 100) * df_res["オッズ_num"] * 100).round(1).astype(str) + "%"
        
        df_res["_win_num"] = raw_win_rate
        df_ranked = df_res.sort_values(by="_win_num", ascending=False).reset_index(drop=True)

        st.subheader("📊 100回シミュレーション・ランキング結果")
        
        display_cols = [
            "開催地", "レース条件", "馬番", "馬名", "人気", "単勝オッズ",
            "シミュ勝率_str", "シミュ複勝率_str", "AI期待回収率_str", "騎手"
        ]
        available_cols = [c for c in display_cols if c in df_ranked.columns]
        df_display = df_ranked[available_cols]
        st.dataframe(df_display, use_container_width=True)

        kaisai_title = str(df_display["開催地"].iloc[0]) if not df_display["開催地"].empty else "阪神"
        r_num_title = str(df_ranked["_レース番号"].iloc[0]) if not df_ranked["_レース番号"].empty else "5R"
        file_prefix = f"{kaisai_title}{r_num_title}"

        # スプレッドシート用に出力する列を組み立て
        export_rows = []
        top_h_str = f"{df_ranked.iloc[0]['馬番']}番 {df_ranked.iloc[0]['馬名']}"

        for _, row in df_ranked.iterrows():
          export_rows.append({
              "日付": row["_日付"],
              "開催地": row["開催地"],
              "レース番号": row["_レース番号"],
              "距離・馬場": row["_距離馬場"],
              "レース条件": row["_詳細条件"],
              "AI本命予想": top_h_str if row.name == 0 else "",
              "シミュ勝率": row["シミュ勝率_str"],
              "シミュ複勝率": row["シミュ複勝_str"] if "シミュ複勝_str" in row else row["シミュ複勝率_str"],
              "AI期待回収率": row["AI期待回収率_str"],
              "実際の1着馬": "",
              "着差・判定メモ": "",
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
            file_name=f"{file_prefix}_sim100_result.csv",
            mime="text/csv",
        )

        tsv_buffer = StringIO()
        df_export_final.to_csv(tsv_buffer, sep="\t", index=False)
        sim_copy_text = tsv_buffer.getvalue()

        st.markdown(
            "### 📋 シミュレーション結果 スプレッドシート用コピー欄（ワンタップ選択）"
        )
        st.text_area(
            "シミュレーション結果コピー用ボックス",
            value=sim_copy_text,
            height=120,
        )

        st.subheader("🎯 おすすめAI買い目インフォ")
        top_horse = df_ranked.iloc[0]["馬名"]
        top_num = df_ranked.iloc[0]["馬番"]
        top_win = df_ranked.iloc[0]["シミュ勝率_str"]
        top_place = df_ranked.iloc[0]["シミュ複勝率_str"]

        df_roi_ranked = df_ranked.sort_values(by="_win_num", ascending=False)
        value_horse = df_roi_ranked.iloc[0]["馬名"]
        value_num = df_roi_ranked.iloc[0]["馬番"]
        value_roi = df_roi_ranked.iloc[0]["AI期待回収率_str"]

        st.info(
            f"◎ **本命推し**: {top_num}番 {top_horse} (勝率: {top_win} / 複勝率:"
            f" {top_place})\n\n★ **穴・妙味推奨**: {value_num}番"
            f" {value_horse} (期待回収率: {value_roi})"
        )
    else:
      st.warning("データが入力されていません。CSVデータを貼り付けてください。")

with tab2:
  st.header("実際のレース結果との照合・検証")
  st.write(
      "保存したシミュレーション結果（CSV）をアップロードし、実際の1〜3着馬を選択してAIの的中状況を検証します。"
  )

  uploaded_sim_file = st.file_uploader(
      "1. 保存したシミュレーション結果CSVをアップロード", type=["csv"]
  )

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.success("シミュレーション結果を読み込みました！")

    horse_options = [
        f"{row.get('馬番')}番 {row.get('馬名')} ({row.get('人気')}・単勝{row.get('単勝オッズ')}倍)"
        for _, row in df_saved.iterrows()
    ]

    date_val = str(df_saved["日付"].iloc[0]) if "日付" in df_saved.columns and not df_saved["日付"].empty else "2026/09/06"
    kaisai_val = str(df_saved["開催地"].iloc[0]) if "開催地" in df_saved.columns and not df_saved["開催地"].empty else "阪神"
    r_num_val = str(df_saved["レース番号"].iloc[0]) if "レース番号" in df_saved.columns and not df_saved["レース番号"].empty else "5R"
    dist_val = str(df_saved["距離・馬場"].iloc[0]) if "距離・馬場" in df_saved.columns and not df_saved["距離・馬場"].empty else ""
    cond_val = str(df_saved["レース条件"].iloc[0]) if "レース条件" in df_saved.columns and not df_saved["レース条件"].empty else ""

    st.subheader("2. 実際のレース結果を選択")
    col1, col2, col3 = st.columns(3)
    with col1:
      actual_1st = st.selectbox(
          "🥇 実際の1着馬",
          options=["選択してください"] + horse_options,
          index=0,
      )
    with col2:
      actual_2nd = st.selectbox(
          "🥈 実際の2着馬",
          options=["選択してください"] + horse_options,
          index=0,
      )
    with col3:
      actual_3rd = st.selectbox(
          "🥉 実際の3着馬",
          options=["選択してください"] + horse_options,
          index=0,
      )

    margin_option = st.selectbox(
        "AI本命馬の着差・状況",
        options=[
            "1着（的中）",
            "2着・3着（複勝圏内）",
            "4着以下（ハナ差・クビ差・惜しい）",
            "4着以下（完敗・見当違い）",
        ],
        index=0,
    )

    if st.button("🔍 予想結果を検証・判定する"):
      if actual_1st == "選択してください":
        st.warning("実際の1着馬を選択してください。")
      else:
        ai_top_row = df_saved.iloc[0]
        ai_top_num = str(ai_top_row.get("馬番"))
        ai_top_name = str(ai_top_row.get("馬名"))
        ai_top_str = f"{ai_top_num}番 {ai_top_name}"
        ai_win_rate = ai_top_row.get("シミュ勝率", "0%")
        ai_place_rate = ai_top_row.get("シミュ複勝率", "0%")
        ai_roi = ai_top_row.get("AI期待回収率", "0%")

        st.markdown("---")
        st.subheader("📝 検証結果レポート")

        col_a, col_b = st.columns(2)
        with col_a:
          st.info(f"**【AI本命予想】**\n\n◎ {ai_top_str}")
        with col_b:
          st.success(
              f"**【実際の着順】**\n\n1着: {actual_1st}\n2着:"
              f" {actual_2nd}\n3着: {actual_3rd}"
          )

        def check_hit(selected_str, target_num, target_name):
          if not selected_str or selected_str == "選択してください":
            return False
          match = re.match(r"^(\d+)番", selected_str.strip())
          if match:
            selected_num = match.group(1)
            if selected_num == str(target_num):
              return True
          if target_name in selected_str:
            return True
          return False

        is_win_hit = check_hit(actual_1st, ai_top_num, ai_top_name)
        is_place_hit = (
            is_win_hit
            or check_hit(actual_2nd, ai_top_num, ai_top_name)
            or check_hit(actual_3rd, ai_top_num, ai_top_name)
        )

        if is_win_hit:
          st.balloons()
          st.success("🎉 【判定】単勝的中！AIの本命が見事1着となりました！")
        elif is_place_hit:
          st.info(
              "👍 【判定】複勝圏内的中！AIの本命が3着以内に入りました。"
          )
        else:
          st.warning(
              f"❌ 【判定】不的中（{margin_option}）。次回のパラメータ調整に活かしましょう。"
          )

        sheet_row_text = (
            f"{date_val}\t{kaisai_val}\t{r_num_val}\t{dist_val}\t{cond_val}\t{ai_top_str}\t{ai_win_rate}\t{ai_place_rate}\t{ai_roi}\t{actual_1st}\t{margin_option}"
        )

        st.markdown("### 📋 検証結果 スプレッドシート用コピー欄（ワンタップ選択）")
        st.text_area(
            "検証結果コピー用ボックス",
            value=sheet_row_text,
            height=70,
        )

  else:
    st.info(
        "まずはTab1で保存したシミュレーション結果のCSVファイルをアップロードしてください。"
    )

with tab3:
  st.header("🛠️ テキスト整形ツール")
  st.write(
      "ネット競馬等の出馬表テキストをここに貼り付けると、AIシミュレーション用のCSV形式へ一瞬で変換します。"
  )

  raw_txt = st.text_area(
      "ここに生の出馬表テキストを貼り付け",
      placeholder="例:\n1 リスグロワール 牡2 55.0 川田将雅 3.9 2人気",
      height=150,
  )

  col_t1, col_t2 = st.columns(2)
  with col_t1:
    inp_date = st.text_input("日付", value="2026/09/06")
  with col_t2:
    inp_kaisai = st.text_input("開催地", value="阪神")

  inp_cond_full = st.text_input("レース条件全体（例: 5R 芝1800m(良) 2歳新馬）", value="5R 芝1800m(良) 2歳新馬")

  if st.button("✨ 指定フォーマットのCSVに変換する"):
    if raw_txt:
      lines = raw_txt.strip().split("\n")
      parsed_rows = []
      for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
          umaban = parts[0]
          ubana = parts[1]
          kishu = parts[2] if len(parts) > 2 else "レーン"
          parsed_rows.append({
              "開催地": inp_kaisai,
              "レース条件": inp_cond_full,
              "馬番": umaban,
              "馬名": ubana,
              "人気": "",
              "単勝オッズ": "",
              "脚質": "差し",
              "上がり3F": "",
              "スピード指数": "",
              "近走5走成績": "0-0-0-0",
              "騎手": kishu,
              "斤量": 55.0,
          })

      if parsed_rows:
        df_converted = pd.DataFrame(parsed_rows)
        cols_order = [
            "開催地", "レース条件", "馬番", "馬名", "人気", "単勝オッズ",
            "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        csv_text = df_converted[cols_order].to_csv(index=False)
        st.success("変換が完了しました！下のボックスをコピーしてTab1に貼り付けてください。")
        st.text_area("変換済みCSV出力", value=csv_text, height=150)
      else:
        st.warning("有効な行が見つかりませんでした。")
    else:
      st.warning("テキストが入力されていません。")
