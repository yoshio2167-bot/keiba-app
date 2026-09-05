from io import BytesIO, StringIO
import json
import os
import pandas as pd
from PIL import Image
import requests
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
      "スマホで撮影した出馬表のスクリーンショットをアップロードすると、AIが画像を読み取ってCSV形式に変換します。"
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
          api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get(
              "GOOGLE_API_KEY"
          )

          if not api_key:
            st.error(
                "エラー: APIキー（GOOGLE_API_KEY）が設定されていません。"
            )
          else:
            # 画像の軽量化とBase64エンコード準備
            image.thumbnail((800, 800))
            if image.mode in ("RGBA", "P"):
              image = image.convert("RGB")

            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format="JPEG", quality=80)
            import base64

            encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode(
                "utf-8"
            )

            prompt = (
                "添付された競馬の出馬表画像から、すべての馬について「馬番」「馬名」「単勝オッズ」を読み取ってください。"
                "出力は必ずPythonのpandas.read_csvで読み込めるCSV形式（ヘッダー: 馬番,馬名,単勝オッズ）のみを出力してください。"
                "余計な解説文やマークダウンのバッククォート（```csv など）は一切含めず、純粋なCSVテキストだけを返してください。"
            )

            # Gemini REST APIのエンドポイント
            url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=){api_key}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": encoded_image,
                                }
                            },
                            {"text": prompt},
                        ]
                    }
                ]
            }

            # 直接HTTPリクエスト（15秒でタイムアウト設定）
            response = requests.post(
                url, headers={"Content-Type": "application/json"}, json=payload, timeout=15
            )

            if response.status_code == 200:
              result_json = response.json()
              csv_text = (
                  result_json.get("candidates", [{}])[0]
                  .get("content", {})
                  .get("parts", [{}])[0]
                  .get("text", "")
                  .strip()
              )
              csv_text = (
                  csv_text.replace("```csv", "").replace("```", "").strip()
              )

              if csv_text:
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
                st.error("AIからの応答が空でした。")
            else:
              st.error(
                  f"APIエラー (ステータスコード: {response.status_code}): {response.text}"
              )

        except Exception as e:
          st.error(f"エラーが発生しました: {e}")
