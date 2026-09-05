from io import StringIO
import os
import time
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ スクショ解析ツール")

tab1, tab2 = st.tabs(["レースシミュレーション", "スクショからデータ化"])

with tab1:
  st.header("レースシミュレーション実行")
  st.write(
      "出馬表のCSVデータを貼り付けるか、右側のタブでスクショから変換したデータを読み込んでシミュレーションを実行します。"
  )

  pasted_data = st.text_area(
      "CSVデータ入力欄",
      placeholder=(
          "開催,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "中山11R,芝1600m(良),1,サンプルホースA,1,4.5,先行,33.8,85,1-2-1-3,川田将雅,56.0"
      ),
      height=150,
  )

  df_input = None
  if pasted_data:
    try:
      df_input = pd.read_csv(StringIO(pasted_data))
      st.success(
          f"データを正常に読み込みました（全 {len(df_input)} 頭登録中）"
      )
      st.dataframe(df_input, use_container_width=True)
    except Exception as e:
      st.info("CSVデータを貼り付けるとここにプレビューが表示されます。")

  if st.button("🚀 推奨シミュレーションを実行"):
    if df_input is not None and not df_input.empty:
      with st.spinner("条件とデータを元に総合評価を計算中..."):
        df_res = df_input.copy()

        df_res["スピード指数_num"] = pd.to_numeric(
            df_res["スピード指数"], errors="coerce"
        ).fillna(50)
        df_res["上がり3F_num"] = pd.to_numeric(
            df_res["上がり3F"], errors="coerce"
        ).fillna(35.0)
        df_res["オッズ_num"] = pd.to_numeric(
            df_res["単勝オッズ"], errors="coerce"
        ).fillna(10.0)

        df_res["AI総合評価スコア"] = (
            df_res["スピード指数_num"] * 0.7
            + (37.0 - df_res["上がり3F_num"]) * 5.0
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
            "AI総合評価スコア",
            "AI妙味期待値",
            "上がり3F",
            "スピード指数",
            "騎手",
        ]
        available_cols = [
            c for c in display_cols if c in df_ranked.columns
        ]

        st.dataframe(df_ranked[available_cols], use_container_width=True)

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
      st.warning(
          "データが入力されていません。CSVを貼り付けるか、スクショ解析からデータを読み込んでください。"
      )

with tab2:
  st.header("出馬表スクショからのデータ自動変換")
  st.write(
      "スマホで撮影した出馬表のスクリーンショット（複数可）をアップロードすると、AIが「競馬場・距離・馬場・天候・クラス」などのレース条件と、各馬の詳細データを一括抽出します。"
  )

  uploaded_files = st.file_uploader(
      "出馬表のスクリーンショットを選択（複数選択可）",
      type=["jpg", "jpeg", "png"],
      accept_multiple_files=True,
  )

  if uploaded_files:
    cols = st.columns(min(len(uploaded_files), 3))
    for idx, file in enumerate(uploaded_files):
      with cols[idx % len(cols)]:
        img_preview = Image.open(file)
        st.image(img_preview, caption=f"画像 {idx+1}", use_container_width=True)

    if st.button("選択した画像をAIで詳細解析（レース条件＋全馬データ）"):
      with st.spinner(
          "AIがレース条件と出馬表データを同時に解析・抽出中..."
      ):
        try:
          import google.generativeai as genai

          api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get(
              "GOOGLE_API_KEY"
          )

          if not api_key:
            st.error(
                "エラー: APIキー（GOOGLE_API_KEY）がSecretsに設定されていません。"
            )
          else:
            genai.configure(api_key=api_key)
            # 制限にひっかかりにくい安定モデル gemini-1.5-flash を使用
            model = genai.GenerativeModel("gemini-1.5-flash")

            pil_images = []
            for file in uploaded_files:
              img = Image.open(file)
              img.thumbnail((1200, 1200))
              if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
              pil_images.append(img)

            prompt = (
                "添付された競馬の出馬表画像から、以下のレース全体条件および各馬の詳細データを読み取ってください:\n\n"
                "【レース条件項目】\n"
                "- 開催（例: 東京、中山、阪神など競馬場名）\n"
                "- レース条件（例: 芝1600m, ダ1200m, 良, 稍重, 晴, 雨, 3歳未勝利, 2勝クラス などをまとめたテキスト）\n\n"
                "【各馬の項目】\n"
                "1. 馬番\n"
                "2. 馬名\n"
                "3. 人気（数字のみ）\n"
                "4. 単勝オッズ（数値のみ）\n"
                "5. 脚質（逃げ、先行、差し、追込など）\n"
                "6. 上がり3F（直近または平均の上がりタイム）\n"
                "7. スピード指数（記載があれば数値）\n"
                "8. 近走5走成績（例: 1-2-1-3-5）\n"
                "9. 騎手名\n"
                "10. 斤量\n\n"
                "※CSV形式にする際、すべての行の「開催」と「レース条件」の列には、そのレースの共通データを自動入力してください。\n"
                "出力は必ずPythonのpandas.read_csvで読み込めるCSV形式（ヘッダー: 開催,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量）のみを出力してください。"
                "余計な解説文やマークダウンのバッククォート（```csv など）は一切含めず、純粋なCSVテキストだけを返してください。"
            )

            content_list = pil_images + [prompt]

            response = None
            max_retries = 3
            for attempt in range(max_retries):
              try:
                response = model.generate_content(content_list)
                break
              except Exception as err:
                if "429" in str(err) and attempt < max_retries - 1:
                  time.sleep(20)
                  continue
                else:
                  raise err

            if response and response.text:
              csv_text = response.text.strip()
              csv_text = csv_text.replace("```csv", "").replace("```", "").strip()

              df_result = pd.read_csv(StringIO(csv_text))

              st.success("レース条件を含む詳細解析・統合が完了しました！")
              st.dataframe(df_result, use_container_width=True)

              st.subheader("📋 変換されたCSVデータ")
              st.text_area(
                  "コピー用エリア",
                  csv_text,
                  key="converted_csv_area",
                  height=150,
              )

              st.code(csv_text, language="csv")
              st.caption(
                  "↑ 上記のコードブロック右上にあるコピーアイコン（📋）をクリックすると、ワンクリックでクリップボードにコピーできます！"
              )

            else:
              st.error("AIから応答がありませんでした。")

        except Exception as e:
          st.error(
              f"解析中にエラーが発生しました（無料枠の上限を超えた場合は少し時間を置いてください）: {e}"
          )
