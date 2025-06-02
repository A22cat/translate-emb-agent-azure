import os
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError # Azure SDKのHTTPエラーをインポート
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.translation.text import TextTranslationClient

def get_ocr_text(image_bytes: bytes) -> str:
    """
    Azure AI Visionを使用して画像からテキストを抽出する。

    Args:
        image_bytes (bytes): 画像のバイトデータ。

    Returns:
        str: 抽出されたテキスト。抽出できなかった場合は空文字。
    """
    try:
        # 環境変数が正しく設定されているか確認
        endpoint = os.getenv("AZURE_COMPUTER_VISION_ENDPOINT")
        key = os.getenv("AZURE_COMPUTER_VISION_KEY")
        if not endpoint or not key:
            raise ValueError("Azure Computer Visionの環境変数が設定されていません。")

        client = ImageAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        # 画像分析の実行
        result = client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.READ] # READ機能でテキスト抽出
        )
        
        extracted_text = ""
        if result.read is not None and result.read.blocks:
            extracted_text = " ".join([line.text for block in result.read.blocks for line in block.lines])
        
        print(f"OCR Result: '{extracted_text}'") # デバッグ用に抽出結果をログ出力
        return extracted_text
            
    except Exception as e:
        print(f"Error during OCR: {e}")
        # エラー発生時は空文字を返すか、エラーを再raiseするかは要件による
        # ここではエラーをログに出力し、空文字を返す
        return ""


def translate_text_azure(text: str, from_language_code: str = "en", target_language_code: str = "ja") -> str:
    """
    Azure AI Translatorを使用してテキストを翻訳する。

    Args:
        text (str): 翻訳するテキスト。
        from_language_code (str): 元の言語コード (例: "en")。
        target_language_code (str): 翻訳先の言語コード (例: "ja")。

    Returns:
        str: 翻訳されたテキスト。翻訳できなかった場合は空文字。
    """
    if not text: # 入力テキストが空の場合は翻訳処理をスキップ
        print("Translation skipped: input text is empty.")
        return ""
        
    try:
        # 環境変数が正しく設定されているか確認
        translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
        # translator_region = os.getenv("AZURE_TRANSLATOR_REGION") # TextTranslationClientでは通常リージョンはエンドポイントに含まれるか、キーの認証情報で解決される
        translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")

        if not translator_key or not translator_endpoint:
            raise ValueError("Azure Translatorのキーまたはエンドポイントの環境変数が設定されていません。")

        # TextTranslationClient の初期化には AzureKeyCredential を使用
        credential = AzureKeyCredential(translator_key)
        #credential = TranslatorCredential(translator_key, translator_region)
        text_translator_client = TextTranslationClient(
            endpoint=translator_endpoint,
            credential=credential
        )
        
        print(f"Attempting translation from '{from_language_code}' to '{target_language_code}' for text: '{text[:100]}...'")

        # 翻訳の実行
        # body パラメータはリスト形式で、各要素は辞書 {"text": "翻訳したいテキスト"}
        # to_language パラメータは翻訳先言語コードのリスト
        # from_language パラメータは翻訳元言語コード (オプション)
        
        # ★ 修正点: エラーメッセージに基づき、引数名を to_language と from_language に修正
        response = text_translator_client.translate(
            body=[{"text": text}],
            to_language=[target_language_code], # 必須キーワード引数として指定(#Azure Translator Text APIのPython SDKでは、ソース言語指定の引数名はto_language。toという引数名は存在しません。)
            from_language=from_language_code    # 翻訳元言語
            # from_parameter を指定しなければ自動検出
        )
        
        translated_text = ""
        print(f"Raw API Response object type: {type(response)}") # ★ 生のレスポンスオブジェクトの型をプリント
        if hasattr(response, '__dict__'):
             print(f"Raw API Response attributes: {response.__dict__}") # オブジェクトの属性を表示（可能な場合）
        else:
             print(f"Raw API Response (list or other): {response}")


        # レスポンスの構造を確認し、正しく翻訳結果を取得
        if response and isinstance(response, list) and len(response) > 0:
            translation_entry = response[0]
            print(f"First entry in response object type: {type(translation_entry)}") # ★ レスポンスの最初の要素の型をプリント
            if hasattr(translation_entry, '__dict__'):
                print(f"First entry in response attributes: {translation_entry.__dict__}") # オブジェクトの属性を表示
            else:
                print(f"First entry in response: {translation_entry}")


            if hasattr(translation_entry, 'detected_language') and translation_entry.detected_language:
                detected_lang_info = translation_entry.detected_language
                print(f"Detected language: {getattr(detected_lang_info, 'language', 'N/A')} with score {getattr(detected_lang_info, 'score', 'N/A')}")

            if hasattr(translation_entry, 'translations') and \
               translation_entry.translations and \
               isinstance(translation_entry.translations, list) and \
               len(translation_entry.translations) > 0:
                
                first_translation_obj = translation_entry.translations[0]
                print(f"First translation object type: {type(first_translation_obj)}") # ★ 最初の翻訳オブジェクトの型をプリント
                if hasattr(first_translation_obj, '__dict__'):
                     print(f"First translation object attributes: {first_translation_obj.__dict__}")
                else:
                    print(f"First translation object: {first_translation_obj}")


                if hasattr(first_translation_obj, 'text'):
                    translated_text = first_translation_obj.text
                else:
                    print("Translation object (first_translation_obj) does not have 'text' attribute.")
            else:
                print("Response 'translations' attribute is missing, empty, not a list, or has no elements.")
        else:
            print("Translation response is empty, not a list, or has no elements.")
        
        print(f"Translation Input: '{text[:100]}...'") # デバッグ用に翻訳結果をログ出力
        print(f"Translation Output: '{translated_text}'") # デバッグ用に翻訳結果をログ出力
        return translated_text

    except HttpResponseError as e: # Azure SDKのHTTPエラーを具体的にキャッチ
        print(f"Azure HTTP Error during translation: {e.status_code} - {e.reason}")
        if e.response and hasattr(e.response, 'text'):
            print(f"Error response body: {e.response.text}")
        elif e.message:
             print(f"Error message: {e.message}")
        return ""
    except Exception as e:
        import traceback
        print(f"Generic error during translation: {e}")
        print(traceback.format_exc()) # スタックトレースも出力
        # エラー発生時は空文字を返すか、エラーを再raiseするかは要件による
        # ここではエラーをログに出力し、空文字を返す
        return ""
