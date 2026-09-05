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
  pasted_data = st.text_area(
      "ペースト #1 (CSVデータを貼り付け)",
      placeholder="馬番,馬名,単勝オッズ...\n1,サンプルホースA,4.5",
  )
  if pasted_data:
    try:
      df_input = pd.read_csv(StringIO(pasted_data))
      st.success("データを正常に読み込みました！")
      st.dataframe(df_input)
    except Exception:
      pass

with tab2:
  st.header("出馬表スクショからのデータ自動変換")
  st.write(
      "スマホで撮影した出馬表のスクリーンショットをアップロードすると、AIが画像を読み取って実際の馬名やオッズをCSV形式に変換します。"
  )

  uploaded_file = st.file_uploader(
      "出馬表のスクリーンショットを選択", type=["jpg", "jpeg", "png"]
  )

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた出馬表", use_container_width=True)

    if st.button("この画像をAIで解析してCSV化する"):
      with st.spinner("AIが画像から出馬表を解析しています..."):
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
            # 新しいAPIキーに対応している最新モデルを指定
            model = genai.GenerativeModel("gemini-3.6-flash")

            image.thumbnail((800, 800))
            if image.mode in ("RGBA", "P"):
              image = image.convert("RGB")

            prompt = (
                "添付された競馬の出馬表画像から、すべての馬について「馬番」「馬名」「単勝オッズ」を読み取ってください。"
                "出力は必ずPythonのpandas.read_csvで読み込めるCSV形式（ヘッダー: 馬番,馬名,単勝オッズ）のみを出力してください。"
                "余計な解説文やマークダウンのバッククォート（```csv など）は一切含めず、純粋なCSVテキストだけを返してください。"
            )

            response = model.generate_content([image, prompt])

            if response and response.text:
              csv_text = response.text.strip()
              csv_text = csv_text.replace("```csv", "").replace("```", "").strip()

              df_result = pd.read_csv(StringIO(csv_text))

              st.success("解析が完了しました！")
              st.dataframe(df_result)

              st.write(
                  "👇 以下のテキストをコピーして「レースシミュレーション」タブの入力欄に貼り付けてください"
              )
              st.text_area(
                  "変換されたCSVデータ", csv_text, key="converted_csv_area"
              )
            else:
              st.error("AIから応答がありませんでした。")

        except Exception as e:
          st.error(f"エラーが発生しました: {e}")
