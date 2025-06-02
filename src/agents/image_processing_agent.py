import uuid
from datetime import datetime, timezone
from langchain_core.runnables import RunnableLambda
from langchain_openai import AzureOpenAIEmbeddings
from azure.cosmos import ContainerProxy as CosmosContainer # ★ 修正: ContainerProxy をインポートし、エイリアスとして使用
from azure.storage.blob import BlobServiceClient

# servicesとutilsから必要な関数をインポート
from services.azure_ai_services import get_ocr_text, translate_text_azure
from services.database_services import save_translation_to_cosmos, upload_image_to_blob
from utils.image_utils import embed_text_on_image

# このファイルでは、3つの論理エージェントの役割を一つのチェーンとして実装します。
# 1. OCRエージェント (get_ocr_text)
# 2. 翻訳エージェント (translate_text_azure)
# 3. 埋込・保存エージェント (残りの処理)

def create_image_processing_chain(
    embeddings: AzureOpenAIEmbeddings,
    cosmos_container: CosmosContainer, # 型ヒントを修正後のものに
    blob_service_client: BlobServiceClient,
):
    """
    画像処理の一連の流れを実行するLangChainのチェーンを作成する。
    入力: {"image_bytes": bytes, "image_name": str}
    出力: 辞書。成功時は処理結果、失敗時はエラー情報を含む可能性。
    例: {"processed_image_bytes": bytes, "processed_image_url": str, "item_saved": dict}
    """
    
    # ステップ1: OCR処理 (入力: data_in -> 出力: data_with_ocr)
    def _ocr_step(data_in: dict) -> dict:
        print("Agent Step: OCR Processing...")
        extracted_text = get_ocr_text(data_in["image_bytes"])
        return {"extracted_text": extracted_text, **data_in}
    
    ocr_lambda = RunnableLambda(_ocr_step)

    # ステップ2: 翻訳処理 (入力: data_with_ocr -> 出力: data_with_translation)
    def _translate_step(data_with_ocr: dict) -> dict:
        print("Agent Step: Translation Processing...")
        if data_with_ocr["extracted_text"]:
            translated_text = translate_text_azure(data_with_ocr["extracted_text"], from_language_code="en", target_language_code="ja")
        else:
            translated_text = "" # 抽出テキストがなければ翻訳も空
        return {"translated_text": translated_text, **data_with_ocr}
        
    translation_lambda = RunnableLambda(_translate_step)

    # ステップ3: 画像埋込、ベクトル化、保存処理 (入力: data_with_translation -> 出力: final_result)
    def _embed_and_save_step(data_with_translation: dict) -> dict:
        print("Agent Step: Embedding Text on Image and Saving...")
        
        original_image_bytes = data_with_translation["image_bytes"]
        original_image_name = data_with_translation["image_name"]
        extracted_text = data_with_translation["extracted_text"]
        translated_text = data_with_translation["translated_text"]

        if not translated_text and not extracted_text: # 抽出も翻訳もされなかった場合
            print("No text extracted or translated. Skipping embed and save.")
            return {
                "processed_image_bytes": None, 
                "processed_image_url": None,
                "item_saved": None,
                "message": "テキストが検出されなかったため、埋込と保存はスキップされました。"
            }

        # 画像に翻訳を埋め込み (翻訳テキストがない場合は抽出テキストを試みるか、何もしない)
        text_to_embed_on_image = translated_text if translated_text else extracted_text
        if text_to_embed_on_image:
            processed_image_bytes = embed_text_on_image(original_image_bytes, text_to_embed_on_image)
        else:
            processed_image_bytes = None # 埋め込むテキストがない場合

        # ファイル名とIDを生成
        doc_id = str(uuid.uuid4()) # Cosmos DBのパーティションキーと一致させる
        timestamp_utc = datetime.now(timezone.utc)
        
        # Blob名にはサニタイズが必要な場合がある (例: スペースや特殊文字)
        safe_original_image_name = "".join(c if c.isalnum() or c in ['.', '-'] else '_' for c in original_image_name)
        original_image_blob_name = f"{timestamp_utc.strftime('%Y%m%d%H%M%S')}_{doc_id}_original_{safe_original_image_name}"
        
        processed_image_blob_name = None
        if processed_image_bytes:
            processed_image_blob_name = f"{timestamp_utc.strftime('%Y%m%d%H%M%S')}_{doc_id}_processed_{safe_original_image_name}"

        # Blob Storageにアップロード
        original_image_url = upload_image_to_blob(blob_service_client, original_image_bytes, original_image_blob_name)
        
        processed_image_url = None
        if processed_image_bytes and processed_image_blob_name:
            processed_image_url = upload_image_to_blob(blob_service_client, processed_image_bytes, processed_image_blob_name)
        
        # 翻訳テキストをベクトル化 (翻訳テキストがある場合のみ)
        translation_embedding = None
        if translated_text:
            try:
                translation_embedding = embeddings.embed_query(translated_text)
            except Exception as e:
                print(f"Error generating embedding for translated text: {e}")
                # Embedding生成エラーは許容し、ベクトルなしで保存を試みることもできる

        # Cosmos DBに保存するアイテムを作成
        item_to_save = {
            "id": doc_id, # パーティションキー
            "originalImageName": original_image_name,
            "originalImageUrl": original_image_url,
            "processedImageUrl": processed_image_url, # Noneの可能性あり
            "originalText": extracted_text,
            "translatedText": translated_text,
            "embedding": translation_embedding, # Noneの可能性あり
            "originalLang": "en", # 固定
            "translatedLang": "ja", # 固定
            "createdAt": timestamp_utc.isoformat()
        }
        
        # Cosmos DBに保存
        try:
            save_translation_to_cosmos(cosmos_container, item_to_save)
            print(f"Item '{doc_id}' successfully saved to Cosmos DB.")
        except Exception as e:
            print(f"Error saving item '{doc_id}' to Cosmos DB during agent step: {e}")
            # DB保存エラーの場合、部分的な成功として情報を返すか、全体をエラーとするか検討
            return {
                "processed_image_bytes": processed_image_bytes,
                "processed_image_url": processed_image_url,
                "item_saved": None, # 保存失敗
                "error": f"Cosmos DBへの保存中にエラー: {e}"
            }

        return {
            "processed_image_bytes": processed_image_bytes,
            "processed_image_url": processed_image_url,
            "item_saved": item_to_save,
            "message": "処理が正常に完了しました。"
        }
    
    embed_save_lambda = RunnableLambda(_embed_and_save_step)

    # 全てのチェーンを結合
    # 入力 -> OCR -> 翻訳 -> 埋込・保存 -> 出力
    full_chain = ocr_lambda | translation_lambda | embed_save_lambda
    
    print("Image processing chain created.")
    return full_chain
