from io import StringIO
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ 記録管理ツール")
st.write(
    "出馬表のスクショは別のチャットでCSV化し、以下の入力欄に貼り付けるだけで、スピード指数計算・総合ランキング・買い目提案・結果保存までを一括で行えます。"
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

if st.button("🚀 スピード指数算出 ＆ シミュレーション実行"):
  if df_input is not None and not df_input.empty:
    with st.spinner("スピード指数の自動算出および総合評価を計算中..."):
      df_res = df_input.copy()

      # 1. 各項目の数値化
      df_res["上がり3F_num"] = pd.to_numeric(
          df_res["上がり3F"], errors="coerce"
      ).fillna(35.0)
      df_res["オッズ_num"] = pd.to_numeric(
          df_res["単勝オッズ"], errors="coerce"
      ).fillna(10.0)


      # 2. スピード指数の自動計算ロジック
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

      # 3. 総合評価スコア・妙味期待値の計算
      df_res["AI総合評価スコア"] = (
          df_res["スピード指数"] * 0.7 + (37.0 - df_res["上がり3F_num"]) * 5.0
      ).round(1)

      df_res["AI妙味期待値"] = (
          df_res["AI総合評価スコア"] / df_res["オッズ_num"]
      ).round(1)

      df_ranked = df_res.sort_values(
          by="AI総合評価スコア", ascending=False
      ).reset_index(drop=True)

      st.subheader("📊 AIシミュレーション・総合評価ランキング")
      display_cols = [
          "開催",
          "レース条件",
          "馬番",
          "馬名",
          "人気",
          "単勝オッズ",
          "脚質",
          "スピード指数",
          "AI総合評価スコア",
          "AI妙味期待値",
          "上がり3F",
          "近走5走成績",
          "騎手",
      ]
      available_cols = [c for c in display_cols if c in df_ranked.columns]

      df_display = df_ranked[available_cols]
      st.dataframe(df_display, use_container_width=True)

      # 📥 わかりやすいファイル名（開催・レース条件を反映）を動的に作成
      file_prefix = "keiba_result"
      if "開催" in df_display.columns and not df_display["開催"].empty:
        kaisai_val = str(df_display["開催"].iloc[0]).strip()
        if kaisai_val and kaisai_val != "nan":
          file_prefix = kaisai_val

      if "レース条件" in df_display.columns and not df_display["レース条件"].empty:
        cond_val = str(df_display["レース条件"].iloc[0]).strip()
        if cond_val and cond_val != "nan":
          # ファイル名に使えない記号などを安全に置換
          cond_val = (
              cond_val.replace("/", "_")
              .replace("(", "_")
              .replace(")", "")
              .replace(" ", "")
          )
          file_prefix = f"{file_prefix}_{cond_val}"

      download_file_name = f"{file_prefix}_simulation.csv"

      # 📥 記録用CSVダウンロードボタン
      csv_download_data = df_display.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          label="📥 このシミュレーション結果をCSVで保存（記録する）",
          data=csv_download_data,
          file_name=download_file_name,
          mime="text/csv",
      )

      st.subheader("🎯 おすすめAI買い目インフォ")
      top_horse = df_ranked.iloc[0]["馬名"]
      top_num = df_ranked.iloc[0]["馬番"]
      value_horse = (
          df_ranked.sort_values(by="AI妙味期待値", ascending=False)
          .iloc[0]["馬名"]
      )
      value_num = (
          df_ranked.sort_values(by="AI妙味期待値", ascending=False)
          .iloc[0]["馬番"]
      )

      st.info(
          f"◎ **本命推し (能力最上位)**: {top_num}番 {top_horse}\n\n"
          f"★ **穴推奨 (妙味期待値高)**: {value_num}番 {value_horse}"
      )
  else:
    st.warning("データが入力されていません。CSVデータを貼り付けてください。")
