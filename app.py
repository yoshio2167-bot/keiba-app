from io import StringIO
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ 精度検証ツール")

tab1, tab2 = st.tabs(["🚀 シミュレーション＆予想", "📊 結果照合・精度検証"])

with tab1:
  st.header("100回モンテカルロ・シミュレーション")
  st.write(
      "出馬表CSVを貼り付けると、100回の模擬レースを実行し、勝率・複勝率・回収率を算出してCSVやスプレッドシート用テキストで保存できます。"
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

        # レース情報の取得
        kaisai_str = ""
        cond_str = ""
        if "開催" in df_display.columns and not df_display["開催"].empty:
          kaisai_val = str(df_display["開催"].iloc[0]).strip()
          if kaisai_val and kaisai_val != "nan":
            kaisai_str = kaisai_val

        if "レース条件" in df_display.columns and not df_display["レース条件"].empty:
          cond_val = str(df_display["レース条件"].iloc[0]).strip()
          if cond_val and cond_val != "nan":
            cond_str = cond_val

        file_prefix = "keiba_montecarlo"
        if kaisai_str or cond_str:
          clean_cond = (
              cond_str.replace("/", "_")
              .replace("(", "_")
              .replace(")", "")
              .replace(" ", "")
          )
          file_prefix = f"{kaisai_str}_{clean_cond}"

        csv_download_data = df_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 シミュレーション結果をCSVで保存",
            data=csv_download_data,
            file_name=f"{file_prefix}_sim100_result.csv",
            mime="text/csv",
        )

        # Tab1用のスプレッドシート一発コピー用テキスト生成（レース情報を先頭に挿入）
        df_copy_prep = df_display.copy()
        race_full_title = f"{kaisai_str} {cond_str}".strip()
        if not race_full_title:
          race_full_title = "不明レース"
        df_copy_prep.insert(0, "レース名", race_full_title)

        tsv_buffer = StringIO()
        df_copy_prep.to_csv(tsv_buffer, sep="\t", index=False)
        sim_copy_text = tsv_buffer.getvalue()

        st.markdown(
            "### 📋 シミュレーション結果 スプレッドシート用コピー欄（ワンタップ選択）"
        )
        st.write(
            "先頭にレース名が入っています。下のボックス内を**1回タップ**すると全選択されるので、そのままコピーしてスプレッドシートに貼り付けてください。"
        )
        st.text_area(
            "シミュレーション結果コピー用ボックス",
            value=sim_copy_text,
            height=100,
            help="タップすると自動で全選択されます。",
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
      "保存したシミュレーション結果（CSV）をアップロードし、実際の1〜3着馬を選択してAIの的中状況を検証します。"
  )

  uploaded_sim_file = st.file_uploader(
      "1. 保存したシミュレーション結果CSVをアップロード", type=["csv"]
  )

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.success("シミュレーション結果を読み込みました！")

    horse_options = [
        f"{row.get('馬番')}番 {row.get('馬名')} ({row.get('人気')}人気・{row.get('単勝オッズ')}倍)"
        for _, row in df_saved.iterrows()
    ]

    race_info = "—"
    if "開催" in df_saved.columns and "レース条件" in df_saved.columns:
      kaisai = (
          str(df_saved["開催"].iloc[0])
          if not df_saved["開催"].empty
          else ""
      )
      cond = (
          str(df_saved["レース条件"].iloc[0])
          if not df_saved["レース条件"].empty
          else ""
      )
      race_info = f"{kaisai} {cond}".strip()

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
        ai_top_str = f"{ai_top_row.get('馬番')}番 {ai_top_row.get('馬名')}"
        ai_win_rate = ai_top_row.get("100回シミュ勝率(%)", 0)
        ai_place_rate = ai_top_row.get("100回シミュ複勝率(%)", 0)
        ai_roi = ai_top_row.get("AI期待回収率(%)", 0)

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

        is_win_hit = (
            str(ai_top_row.get("馬番")) in actual_1st
            or ai_top_row.get("馬名") in actual_1st
        )
        is_place_hit = (
            is_win_hit
            or str(ai_top_row.get("馬番")) in actual_2nd
            or ai_top_row.get("馬名") in actual_2nd
            or str(ai_top_row.get("馬番")) in actual_3rd
            or ai_top_row.get("馬名") in actual_3rd
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

        from datetime import datetime

        today_str = datetime.now().strftime("%Y/%m/%d")
        sheet_row_text = (
            f"{today_str}\t{race_info}\t{ai_top_str}\t{ai_win_rate}%\t{ai_place_rate}%\t{ai_roi}%\t{actual_1st}\t{margin_option}"
        )

        st.markdown("### 📋 検証結果 スプレッドシート用コピー欄（ワンタップ選択）")
        st.write(
            "先頭にレース名が入っています。下のボックス内を**1回タップ**すると全選択されるので、そのままコピーしてスプレッドシートのセルに貼り付けてください。"
        )
        st.text_area(
            "検証結果コピー用ボックス",
            value=sheet_row_text,
            height=70,
            help="タップすると自動で全選択されます。",
        )

  else:
    st.info(
        "まずはTab1で保存したシミュレーション結果のCSVファイルをアップロードしてください。"
    )
