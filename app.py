from io import StringIO
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ 精度検証ツール")

# タブの作成
tab1, tab2 = st.tabs(["🚀 シミュレーション＆予想", "📊 結果照合・精度検証"])

with tab1:
  st.header("100回モンテカルロ・シミュレーション")
  st.write(
      "出馬表CSVを貼り付けると、100回の模擬レースを実行し、勝率・複勝率・回収率を算出してCSVで保存できます。"
  )

  pasted_data = st.text_area(
      "CSVデータ貼り付け欄",
      placeholder=(
          "開催,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "中山11R,芝1600m(良),1,サンプルホースA,1,4.5,先行,33.8,,1-2-1-3,川田将雅,56.0"
      ),
      height=180,
  )

  df_input = None
  if pasted_data:
    try:
      df_input = pd.read_csv(StringIO(pasted_data))
      st.success(f"データを正常に読み込みました（全 {len(df_input)} 頭登録中）")
      st.dataframe(df_input, use_container_width=True)
    except Exception as e:
      st.info(
          "CSVデータを貼り付けるとここにプレビューが表示されます。（カンマ区切りとヘッダーを確認してください）"
      )

  if st.button("🚀 100回シミュレーション＆予想実行"):
    if df_input is not None and not df_input.empty:
      with st.spinner(
          "100回の模擬レース（モンテカルロ法）の勝率・複勝率を集計中..."
      ):
        df_res = df_input.copy()

        df_res["上がり3F_num"] = pd.to_numeric(
            df_res["上がり3F"], errors="coerce"
        ).fillna(35.0)
        df_res["オッズ_num"] = pd.to_numeric(
            df_res["単勝オッズ"], errors="coerce"
        ).fillna(10.0)


        def calc_speed_index(row):
          try:
            val = float(row["スピード指数"])
            if val > 0:
              return val
          except:
            pass
          base_idx = 70.0
          up_time = row["上がり3F_num"]
          base_idx += (37.0 - up_time) * 4.0
          recent = str(row["近走5走成績"])
          wins = recent.count("1")
          base_idx += wins * 3.0
          return round(max(50.0, min(100.0, base_idx)), 1)


        if "スピード指数" not in df_res.columns:
          df_res["スピード指数"] = 0.0
        df_res["スピード指数"] = df_res.apply(calc_speed_index, axis=1)

        df_res["ベース評価"] = (
            df_res["スピード指数"] * 0.7 + (37.0 - df_res["上がり3F_num"]) * 5.0
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

        df_res["100回シミュ勝率(%)"] = (
            (win_counts / n_simulations) * 100
        ).round(1)
        df_res["100回シミュ複勝率(%)"] = (
            (place_counts / n_simulations) * 100
        ).round(1)
        df_res["AI期待回収率(%)"] = (
            (df_res["100回シミュ勝率(%)"] / 100) * df_res["オッズ_num"] * 100
        ).round(1)
        df_res["AI総合評価スコア"] = df_res["ベース評価"].round(1)

        df_ranked = df_res.sort_values(
            by="100回シミュ勝率(%)", ascending=False
        ).reset_index(drop=True)

        st.subheader("📊 100回シミュレーション・勝率＆複勝率ランキング")
        display_cols = [
            "開催",
            "レース条件",
            "馬番",
            "馬名",
            "人気",
            "単勝オッズ",
            "100回シミュ勝率(%)",
            "100回シミュ複勝率(%)",
            "AI期待回収率(%)",
            "AI総合評価スコア",
            "スピード指数",
            "上がり3F",
            "騎手",
        ]
        available_cols = [c for c in display_cols if c in df_ranked.columns]
        df_display = df_ranked[available_cols]
        st.dataframe(df_display, use_container_width=True)

        file_prefix = "keiba_montecarlo"
        if "開催" in df_display.columns and not df_display["開催"].empty:
          kaisai_val = str(df_display["開催"].iloc[0]).strip()
          if kaisai_val and kaisai_val != "nan":
            file_prefix = kaisai_val

        if "レース条件" in df_display.columns and not df_display["レース条件"].empty:
          cond_val = str(df_display["レース条件"].iloc[0]).strip()
          if cond_val and cond_val != "nan":
            cond_val = (
                cond_val.replace("/", "_")
                .replace("(", "_")
                .replace(")", "")
                .replace(" ", "")
            )
            file_prefix = f"{file_prefix}_{cond_val}"

        csv_download_data = df_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 シミュレーション結果をCSVで保存",
            data=csv_download_data,
            file_name=f"{file_prefix}_sim100_result.csv",
            mime="text/csv",
        )

        st.subheader("🎯 おすすめAI買い目インフォ")
        top_horse = df_ranked.iloc[0]["馬名"]
        top_num = df_ranked.iloc[0]["馬番"]
        top_win = df_ranked.iloc[0]["100回シミュ勝率(%)"]
        top_place = df_ranked.iloc[0]["100回シミュ複勝率(%)"]

        df_roi_ranked = df_ranked.sort_values(
            by="AI期待回収率(%)", ascending=False
        )
        value_horse = df_roi_ranked.iloc[0]["馬名"]
        value_num = df_roi_ranked.iloc[0]["馬番"]
        value_roi = df_roi_ranked.iloc[0]["AI期待回収率(%)"]

        st.info(
            f"◎ **本命推し**: {top_num}番 {top_horse} (勝率: {top_win}% / 複勝率:"
            f" {top_place}%)\n\n★ **穴・妙味推奨**: {value_num}番"
            f" {value_horse} (期待回収率: {value_roi}%)"
        )
    else:
      st.warning("データが入力されていません。CSVデータを貼り付けてください。")

with tab2:
  st.header("実際のレース結果との照合・検証")
  st.write(
      "過去に保存したシミュレーション結果（CSV）と、実際のレース結果（着順データ）を突き合わせて的中状況を検証します。"
  )

  uploaded_sim_file = st.file_uploader(
      "1. 保存したシミュレーション結果CSVをアップロード", type=["csv"]
  )

  actual_result_text = st.text_area(
      "2. 実際のレース結果（上位馬の馬番または馬名）を入力",
      placeholder=(
          "例:\n"
          "1着: 4\n"
          "2着: 1\n"
          "3着: 7\n"
          "（または馬名でも可。上から順に1着、2着、3着を入力してください）"
      ),
      height=120,
  )

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.subheader("📋 読み込んだシミュレーション結果プレビュー")
    st.dataframe(df_saved, use_container_width=True)

    if st.button("🔍 実際の着と比較して検証する"):
      if not actual_result_text:
        st.warning("実際のレース結果を入力してください。")
      else:
        st.success("検証処理を実行しました。")
        # 本命（ランキング1行目）の取得
        top_pick_row = df_saved.iloc[0]
        top_num = str(top_pick_row.get("馬番"))
        top_name = str(top_pick_row.get("馬名"))
        top_odds = float(top_pick_row.get("単勝オッズ", 0))

        st.info(
            f"**【AIの本命】** 枠番/馬番: {top_num}番 ({top_name}) / 単勝オッズ:"
            f" {top_odds}倍"
        )
        st.write(
            "※ 入力された実際の着順テキストと照らし合わせ、的中していたかを確認してください。"
        )
        st.text(f"【入力された実際の結果】\n{actual_result_text}")
  else:
    st.info(
        "まずはTab1で保存したシミュレーション結果のCSVファイルをアップロードしてください。"
    )
