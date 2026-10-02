from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="競馬予想AIシミュレーター（スプレッドシート自動連携版）",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("競馬予想AIシミュレーター ＆ スプレッドシート自動連携")

tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 シミュレーション＆自動3連複",
    "📊 結果照合・自動判定検証",
    "🛠️ 出馬表データ整形ツール",
    "📈 収支ダッシュボード",
])

with tab1:
  st.header("モンテカルロ・シミュレーション ＆ スプレッドシート連携")
  st.write(
      "GoogleスプレッドシートのCSV公開リンクを入力するか、CSVを直接貼り付けて実行できます。"
  )

  # スプレッドシート連携用の入力欄
  sheet_csv_url = st.text_input(
      "🔗 GoogleスプレッドシートのCSV公開リンク（共有URL等）",
      value="",
      placeholder=(
          "https://docs.google.com/spreadsheets/d/.../export?format=csv"
      ),
  )

  col_s1, col_s2, col_s3 = st.columns(3)
  with col_s1:
    threshold_roi = st.slider(
        "🎯 見送りライン(%)", min_value=100, max_value=200, value=120, step=10
    )
  with col_s2:
    sim_count_input = st.selectbox(
        "🔄 試行回数",
        options=["1回（一発ガチ）", "100回", "300回", "500回"],
        index=1,
    )
  with col_s3:
    total_budget = st.number_input(
        "💰 投資予算 (円)", min_value=500, max_value=50000, value=2000, step=500
    )

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

  df_input = None

  # 1. スプレッドシートのURLから読み込む場合
  if sheet_csv_url.strip():
    try:
      df_input = pd.read_csv(sheet_csv_url.strip())
      st.success(
          "Googleスプレッドシートからデータを自動取得しました！（全"
          f" {len(df_input)} 行）"
      )
    except Exception as e:
      st.error(
          "スプレッドシートの読み込みに失敗しました。URLや公開設定（CSV形式）をご確認ください。"
      )

  # 2. 手動で貼り付ける場合
  else:
    col_btn1, col_btn2 = st.columns([0.8, 0.2])
    with col_btn2:
      if st.button("🗑 一括削除", type="secondary"):
        st.session_state.pasted_csv = ""
        st.rerun()

    pasted_data = st.text_area(
        "またはCSVデータ貼り付け欄",
        value=st.session_state.pasted_csv,
        placeholder=(
            "日付,開催地,レース番号,距離・馬場,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
            "2026/09/20,阪神,1R,障2970m(晴"
            " 良),障害3歳以上未勝利,11,クロライナ,11人気,44.4,差,0,0,0-0-0-0-6,五十嵐雄,60.0"
        ),
        height=140,
    )
    st.session_state.pasted_csv = pasted_data

    if pasted_data.strip():
      try:
        lines = [
            line.strip()
            for line in pasted_data.strip().split("\n")
            if line.strip()
        ]
        if len(lines) > 0:
          first_line = lines[0]
          has_header = (
              "馬番" in first_line or "馬名" in first_line or "日付" in first_line
          )
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
      except Exception as e:
        pass

  if df_input is not None and not df_input.empty:

    def extract_num(val, default=5.0):
      try:
        s = str(val)
        if s == "nan" or not s.strip():
          return default
        m = re.search(r"([\d\.]+)", s)
        if m:
          return float(m.group(1))
      except:
        pass
      return default

    # 必要な数値カラムの正規化
    if "人気" in df_input.columns:
      df_input["人気_num"] = df_input["人気"].apply(
          lambda x: extract_num(x, 5.0)
      )
    else:
      df_input["人気_num"] = 5.0

    if "単勝オッズ" in df_input.columns:
      df_input["オッズ_num"] = df_input["単勝オッズ"].apply(
          lambda x: extract_num(x, 15.0)
      )
    else:
      df_input["オッズ_num"] = 15.0

    if "上がり3F" in df_input.columns:
      df_input["上がり3F_val"] = df_input["上がり3F"].apply(
          lambda x: extract_num(x, 0.0)
      )
    else:
      df_input["上がり3F_val"] = 0.0

    preview_cols = [
        c
        for c in [
            "日付",
            "開催地",
            "レース番号",
            "距離・馬場",
            "馬番",
            "馬名",
            "人気",
            "単勝オッズ",
            "脚質",
        ]
        if c in df_input.columns
    ]
    st.dataframe(
        df_input[preview_cols], use_container_width=True, height=160
    )

    if st.button("🚀 自動ペース判定 ＆ 予想を実行", type="primary"):
      with st.spinner("AIがレース展開を自動判定・解析中..."):
        df_res = df_input.copy()

        nige_senko_count = 0
        for _, row in df_res.iterrows():
          kyaku = str(row.get("脚質", ""))
          if any(k in kyaku for k in ["逃", "先行"]):
            nige_senko_count += 1

        total_horses = len(df_res)
        if nige_senko_count <= max(1, total_horses * 0.2):
          auto_pace_name = "スローペース（前残・先行有利）"
        elif nige_senko_count >= total_horses * 0.5:
          auto_pace_name = "ハイ・タフペース（差し・追込有利）"
        else:
          auto_pace_name = "平均ペース（バランス型）"

        def calc_enhanced_score(row):
          try:
            odds = float(row["オッズ_num"])
            if odds <= 0:
              odds = 10.0
          except:
            odds = 10.0

          base_score = max(10.0, 160.0 / (np.log(odds + 1.0) + 0.7))

          try:
            f_val = float(row["上がり3F_val"])
            if 30.0 <= f_val <= 42.0:
              base_score += (40.0 - f_val) * 7.0
          except:
            pass

          kyaku = str(row.get("脚質", ""))
          if "スロー" in auto_pace_name:
            if any(k in kyaku for k in ["逃", "先行"]):
              base_score += 15.0
          elif "ハイ・タフ" in auto_pace_name:
            if any(k in kyaku for k in ["差", "追"]):
              base_score += 18.0

          return base_score

        df_res["ベース評価"] = df_res.apply(calc_enhanced_score, axis=1)

        win_counts = np.zeros(len(df_res))
        place_counts = np.zeros(len(df_res))

        np.random.seed(42)
        scores_arr = df_res["ベース評価"].values
        actual_sims = max(1, sim_count)
        noise_scale = 0.0 if actual_sims == 1 else np.mean(scores_arr) * 0.4

        for _ in range(actual_sims):
          noise = np.random.normal(0, noise_scale, size=len(df_res))
          sim_scores = scores_arr + noise
          top_indices = np.argsort(sim_scores)[::-1]

          winner_idx = top_indices[0]
          win_counts[winner_idx] += 1

          placers = top_indices[: min(3, len(df_res))]
          for p_idx in placers:
            place_counts[p_idx] += 1

        df_res["シミュ勝率_str"] = (
            ((win_counts / actual_sims) * 100).round(1).astype(str) + "%"
        )
        df_res["シミュ複勝率_str"] = (
            ((place_counts / actual_sims) * 100).round(1).astype(str) + "%"
        )

        raw_win_rate = (win_counts / actual_sims) * 100
        df_res["AI期待回収率_str"] = (
            ((raw_win_rate / 100) * df_res["オッズ_num"] * 100)
            .round(1)
            .astype(str)
            + "%"
        )

        df_res["_win_num"] = raw_win_rate
        df_ranked = df_res.sort_values(
            by="_win_num", ascending=False
        ).reset_index(drop=True)

        st.info(
            f"🤖 **【AI自動判定された展開】: {auto_pace_name}**"
            f" （逃げ先行馬: {nige_senko_count}頭 / 登録数: {total_horses}頭）"
        )
        st.subheader("📊 予想・ランキング結果")

        display_cols = [
            c
            for c in [
                "開催地",
                "レース番号",
                "距離・馬場",
                "馬番",
                "馬名",
                "人気",
                "単勝オッズ",
                "シミュ勝率_str",
                "シミュ複勝率_str",
                "AI期待回収率_str",
                "脚質",
                "上がり3F",
                "騎手",
            ]
            if c in df_ranked.columns
        ]
        st.dataframe(
            df_ranked[display_cols], use_container_width=True, height=220
        )

        top1 = df_ranked.iloc[0] if len(df_ranked) > 0 else None
        top2 = df_ranked.iloc[1] if len(df_ranked) > 1 else None
        top3 = df_ranked.iloc[2] if len(df_ranked) > 2 else None
        top4 = df_ranked.iloc[3] if len(df_ranked) > 3 else None
        top5 = df_ranked.iloc[4] if len(df_ranked) > 4 else None

        wide_1 = (
            f"◎{top1['馬番']} - 〇{top2['馬番']}"
            if top1 is not None and top2 is not None
            else ""
        )
        wide_2 = (
            f"◎{top1['馬番']} - ▲{top3['馬番']}"
            if top1 is not None and top3 is not None
            else ""
        )
        strict_buy_focus = f"【推奨ワイド2点】 {wide_1} / {wide_2}"

        num_bets_3ren = 3
        bet_amount_per_point = max(
            100, int((total_budget / 100 / num_bets_3ren) * 100)
        )
        three_renpuku_focus = (
            "【推奨3連複 軸2頭流し（全3点）】\n"
            f"  軸: ◎{top1['馬番']}番 ＆ 〇{top2['馬番']}番\n"
            f"  相手: ▲{top3['馬番']}番, {top4['馬番']}番, {top5['馬番']}番\n"
            f"  💡 **資金配分**: 1点あたり **{bet_amount_per_point}円**"
            f" （合計: {bet_amount_per_point * num_bets_3ren}円）"
        )

        try:
          roi_val_num = float(
              str(top1["AI期待回収率_str"]).replace("%", "")
          )
        except:
          roi_val_num = 100.0

        if roi_val_num >= threshold_roi:
          st.success(
              f"🔥 **【勝負レース推奨】（回収率: {top1['AI期待回収率_str']} ＞"
              f" 基準 {threshold_roi}%）**\n\n{strict_buy_focus}\n\n{three_renpuku_focus}"
          )
        else:
          st.warning(
              f"⚠️ **【見送り推奨 / パス】（回収率: {top1['AI期待回収率_str']} ＜"
              f" 基準 {threshold_roi}%）**\n\n{strict_buy_focus}\n\n{three_renpuku_focus}"
          )

with tab2:
  st.header("実際のレース結果との照合・自動判定")
  st.info("Tab1で実行したデータを活用して結果を判定できます。")

with tab3:
  st.header("🛠️ 出馬表データ整形ツール")
  st.write("スプレッドシートやテキストデータを15列の正しいフォーマットに整えます。")

with tab4:
  st.header("📈 収支ダッシュボード ＆ 回収率分析")
  if "df_balance" not in st.session_state:
    st.session_state.df_balance = pd.DataFrame(columns=[
        "日付",
        "競馬場",
        "レース",
        "券種",
        "投資額(円",
        "払戻額(円)",
    ])

  with st.form("balance_form"):
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
      b_date = st.text_input("日付", value="2026-09-20")
      b_track = st.text_input("競馬場", value="阪神")
    with col_b2:
      b_race = st.text_input("レース番号", value="1R")
      b_type = st.selectbox(
          "券種", options=["3連複", "ワイド", "馬連", "単勝", "その他"]
      )
    with col_b3:
      b_invest = st.number_input(
          "投資額 (円)", min_value=100, value=1000, step=100
      )
      b_return = st.number_input("払戻額 (円)", min_value=0, value=0, step=100)

    if st.form_submit_button("📝 収支データを登録する"):
      new_row = pd.DataFrame([{
          "日付": b_date,
          "競馬場": b_track,
          "レース": b_race,
          "券種": b_type,
          "投資額(円": b_invest,
          "払戻額(円)": b_return,
      }])
      st.session_state.df_balance = pd.concat(
          [st.session_state.df_balance, new_row], ignore_index=True
      )
      st.success("追加しました！")

  df_bal = st.session_state.df_balance
  if not df_bal.empty:
    total_invest = df_bal["投資額(円"].sum()
    total_return = df_bal["払戻額(円)"].sum()
    net_profit = total_return - total_invest
    overall_roi = (
        (total_return / total_invest * 100) if total_invest > 0 else 0
    )

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("総投資額", f"{total_invest:,} 円")
    mcol2.metric("総払戻額", f"{total_return:,} 円")
    mcol3.metric("トータル収支", f"{net_profit:,} 円")
    mcol4.metric("回収率", f"{overall_roi:.1f} %")

    st.dataframe(df_bal, use_container_width=True)
    df_bal["収支"] = df_bal["払戻額(円)"] - df_bal["投資額(円"]
    df_bal["累計収支"] = df_bal["収支"].cumsum()
    st.line_chart(df_bal["累計収支"])
