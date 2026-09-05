from io import StringIO
import os
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ スクショ解析ツール")

tab1, tab2 = st.tabs(["レースシミュレーション", "スクショからデータ化"])

with tab1:
  st.header("レースシミュレーション実行")
  st.write(
      "スクショから変換したCSVデータを貼り付けると、AIが能力・上がり3F・オッズを総合評価して推奨順位を算出します。"
  )

  pasted_data = st.text_area(
      "CSVデータ入力欄",
      placeholder=(
          "馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n1,サンプルホースA,1,4.5,先行,33.8,85,1-2-1-3,川田将雅,56.0"
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
      st.info(
          "CSVデータを貼り付けるとここにプレビューが表示されます。"
      )

  if st.button("🚀 推奨シミュレーションを実行"):
    if df_input is not None and not df_input.empty:
      with st.spinner("スピード指数と上がり3Fを元に総合評価を計算中..."):
        df_res = df_input.copy()

        # 数値データの型変換（欠損値や文字列混入対策）
        df_res["スピード指数_num"] = pd.to_numeric(
            df_res["スピード指数"], errors="coerce"
        ).fillna(50)
        df_res["上がり3F_num"] = pd.to_numeric(
            df_res["上がり3F"], errors="coerce"
        ).fillna(35.0)
        df_res["オッズ_num"] = pd.to_numeric(
            df_res["単勝オッズ"], errors="coerce"
        ).fillna(10.0)

        # おすすめ総合スコア計算式:
        # スピード指数が高く、かつ上がり3Fのタイムが若い（速い）ほど高得点
        # 上がり3Fは数値が小さいほど良いので、基準値（37.0）から引いた数値をプラス評価にする
        df_res["AI総合評価スコア"] = (
            df_res["スピード指数_num"] * 0.7
            + (37.0 - df_res["上がり3F_num"]) * 5.0
        ).round(1)

        # 期待値スコア（能力スコア ÷ オッズ で「オッズ妙味のある穴馬」を浮き上がらせる）
        df_res["AI妙味期待値"] = (
            df_res["AI総合評価スコア"] / df_res["オッズ_num"]
        ).round(1)

        # スコア順に並び替え
        df_ranked = df_res.sort_values(
            by="AI総合評価スコア", ascending=False
        ).reset_index(drop=True)

        st.subheader("📊 AIシミュレーション・総合評価ランキング")
        st.write(
            "※「AI総合評価スコア」が高いほど能力上位、「AI妙味期待値」が高いほどオッズ妙味がある（穴でおすすめ）馬です。"
        )

        # 表示する列を整理
        display_cols = [
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

        # 推奨買い目の自動提案
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
      "スマホで撮影した出馬表のスクリーンショットをアップロードすると、AIが「馬番」「馬名」「人気」「オッズ」「脚質」「上がり3F」「スピード指数」「近走5走成績」「騎手」「斤量」をすべて抽出します。"
  )

  uploaded_file = st.file_uploader(
      "出馬表のスクリーンショットを選択", type=["jpg", "jpeg", "png"]
  )

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた出馬表", use_container_width=True)

    if st.button("この画像をAIで詳細解析してCSV化する"):
      with st.spinner(
          "AIが画像から出馬表の詳細データ（脚質・上がり3F・5走分など）を抽出中..."
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
            model = genai.GenerativeModel("gemini-3.6-flash")

            image.thumbnail((1200, 1200))
            if image.mode in ("RGBA", "P"):
              image = image.convert("RGB")

            prompt = (
                "添付された競馬の出馬表画像から、掲載されているすべての馬について以下の項目を漏れなく読み取ってください:\n"
                "1. 馬番\n"
                "2. 馬名\n"
                "3. 人気（何番人気か。数字のみ）\n"
                "4. 単勝オッズ（数値のみ）\n"
                "5. 脚質（逃げ、先行、差し、追込など）\n"
                "6. 上がり3F（直近または平均の上がり3ハロンのタイム。例: 34.5など）\n"
                "7. スピード指数（記載があれば数値。なければ空欄または推定値）\n"
                "8. 近走5走成績（直近5走の着順や着差などの戦績データ。例: 1-2-1-3-5 など）\n"
                "9. 騎手名\n"
                "10. 斤量\n\n"
                "出力は必ずPythonのpandas.read_csvで読み込めるCSV形式（ヘッダー: 馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量）のみを出力してください。"
                "余計な解説文やマークダウンのバッククォート（```csv など）は一切含めず、純粋なCSVテキストだけを返してください。"
            )

            response = model.generate_content([image, prompt])

            if response and response.text:
              csv_text = response.text.strip()
              csv_text = csv_text.replace("```csv", "").replace("```", "").strip()

              df_result = pd.read_csv(StringIO(csv_text))

              st.success("詳細解析が完了しました！")
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
          st.error(f"解析中にエラーが発生しました: {e}")
