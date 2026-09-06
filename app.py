from io import StringIO
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ モンテカルロ分析ツール")
st.write(
    "出馬表CSVを貼り付けると、100回の模擬レース（モンテカルロ法）を実行し、勝率や回収率を算出してCSVで保存できます。"
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
        "100回の模擬レース（モンテカルロ法）を実行・集計中..."
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

      np.random.seed(42)
      for _ in range(n_simulations):
        noise = np.random.normal(
            0, df_res["ベース評価"].values * 0.1, size=len(df_res)
        )
        sim_scores = df_res["ベース評価"].values + noise
        winner_idx = np.argmax(sim_scores)
        win_counts[winner_idx] += 1

      df_res["100回シミュ勝率(%)"] = (
          (win_counts / n_simulations) * 100
      ).round(1)
      df_res["AI期待回収率(%)"] = (
          (df_res["100回シミュ勝率(%)"] / 100) * df_res["オッズ_num"] * 100
      ).round(1)
      df_res["AI総合評価スコア"] = df_res["ベース評価"].round(1)

      df_ranked = df_res.sort_values(
          by="100回シミュ勝率(%)", ascending=False
      ).reset_index(drop=True)

      st.subheader("📊 100回シミュレーション・勝率＆回収率ランキング")
      display_cols = [
          "開催",
          "レース条件",
          "馬番",
          "馬名",
          "人気",
          "単勝オッズ",
          "100回シミュ勝率(%)",
          "AI期待回収率(%)",
          "AI総合評価スコア",
          "スピード指数",
          "上がり3F",
          "騎手",
      ]
      available_cols = [c for c in display_cols if c in df_ranked.columns]
      df_display = df_ranked[available_cols]
      st.dataframe(df_display, use_container_width=True)

      # ファイル名のプレフィックス自動生成
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

      # 📥 CSV保存ボタン
      csv_download_data = df_display.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          label="📥 シミュレーション結果をCSVで保存",
          data=csv_download_data,
          file_name=f"{file_prefix}_sim100_result.csv",
          mime="text/csv",
      )

      st.info(
          "💡 PDFとして保存したい場合は、ブラウザのメニューから「共有」または「印刷」を選び、PDFとして保存してください。"
      )

      st.subheader("🎯 おすすめAI買い目インフォ")
      top_horse = df_ranked.iloc[0]["馬名"]
      top_num = df_ranked.iloc[0]["馬番"]
      top_win = df_ranked.iloc[0]["100回シミュ勝率(%)"]

      df_roi_ranked = df_ranked.sort_values(
          by="AI期待回収率(%)", ascending=False
      )
      value_horse = df_roi_ranked.iloc[0]["馬名"]
      value_num = df_roi_ranked.iloc[0]["馬番"]
      value_roi = df_roi_ranked.iloc[0]["AI期待回収率(%)"]

      st.info(
          f"◎ **本命推し (シミュレーション勝率最高 {top_win}%)**: {top_num}番"
          f" {top_horse}\n\n★ **穴・妙味推奨 (期待回収率 {value_roi}%)**: {value_num}番"
          f" {value_horse}"
      )
  else:
    st.warning("データが入力されていません。CSVデータを貼り付けてください。")
