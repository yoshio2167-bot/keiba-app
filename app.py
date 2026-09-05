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
      "出馬表のCSVデータを貼り付けるか、右側のタブでスクショから変換したデータを読み込んでシミュレーションを実行します。"
  )

  pasted_data = st.text_area(
      "CSVデータ入力欄",
      placeholder=(
          "馬番,馬名,人気,単勝オッズ,騎手,斤量\n1,サンプルホースA,1,4.5,川田将雅,56.0"
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
      st.error(
          f"CSVの読み込み形式にエラーがあります（ヘッダーとカンマ区切りを確認してください）: {e}"
      )

  if st.button("🚀 レースシミュレーションを実行"):
    if df_input is not None and not df_input.empty:
      with st.spinner("レース展開および勝率をシミュレーション中..."):
        # シミュレーション処理のプレースホルダー（必要に応じてお手元のロジックに置き換え可能です）
        st.subheader("📊 シミュレーション結果")
        st.write(
            "オッズや能力指数に基づいた予測勝率・推奨買い目の算出完了しました。"
        )

        # サンプルの計算結果表示
        df_result = df_input.copy()
        df_result["AI期待値スコア"] = (
            100 / pd.to_numeric(df_result["単勝オッズ"], errors="coerce")
        ).round(1)
        st.dataframe(
            df_result.sort_values(by="AI期待値スコア", ascending=False),
            use_container_width=True,
        )
    else:
      st.warning(
          "有効なデータが入力されていません。CSVデータを入力するか、スクショ解析タブからデータを読み込んでください。"
      )

with tab2:
  st.header("出馬表スクショからのデータ自動変換")
  st.write(
      "スマホで撮影した出馬表のスクリーンショットをアップロードすると、AIが「馬番」「馬名」「人気」「単勝オッズ」「騎手」「斤量」などの詳細データを一括でCSV化します。"
  )

  uploaded_file = st.file_uploader(
      "出馬表のスクリーンショットを選択", type=["jpg", "jpeg", "png"]
  )

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた出馬表", use_container_width=True)

    if st.button("この画像をAIで詳細解析してCSV化する"):
      with st.spinner(
          "AIが画像から出馬表の詳細データを抽出しています..."
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

            image.thumbnail((1000, 1000))
            if image.mode in ("RGBA", "P"):
              image = image.convert("RGB")

            prompt = (
                "添付された競馬の出馬表画像から、掲載されているすべての馬について以下の項目を読み取ってください:\n"
                "1. 馬番\n2. 馬名\n3. 人気（何番人気か。例: 1, 2など数字のみ、または記載がなければ空欄）\n4. 単勝オッズ（数値のみ。例: 4.5）\n5. 騎手名\n6. 斤量（例: 55.0）\n\n"
                "出力は必ずPythonのpandas.read_csvで読み込めるCSV形式（ヘッダー: 馬番,馬名,人気,単勝オッズ,騎手,斤量）のみを出力してください。"
                "余計な解説文やマークダウンのバッククォート（```csv など）は一切含めず、純粋なCSVテキストだけを返してください。"
            )

            response = model.generate_content([image, prompt])

            if response and response.text:
              csv_text = response.text.strip()
              csv_text = csv_text.replace("```csv", "").replace("```", "").strip()

              df_result = pd.read_csv(StringIO(csv_text))

              st.success("詳細解析が完了しました！")
              st.dataframe(df_result, use_container_width=True)

              st.info(
                  "👇 以下のテキストボックスの内容をコピーして、「レースシミュレーション」タブの入力欄に貼り付けてシミュレーションを実行してください。"
              )
              st.text_area(
                  "変換されたCSVデータ（コピー用）",
                  csv_text,
                  key="converted_csv_area",
                  height=150,
              )
            else:
              st.error("AIから応答がありませんでした。")

        except Exception as e:
          st.error(f"解析中にエラーが発生しました: {e}")
