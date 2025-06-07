import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions as cosmos_exceptions
from azure.storage.blob import BlobServiceClient
from langchain_openai import AzureOpenAIEmbeddings # AzureOpenAIEmbeddingsのインポートを確認

# --- Cosmos DB Functions ---

def init_cosmos_db_client() -> CosmosClient:
    """Cosmos DBクライアントを初期化する。"""
    endpoint = os.getenv("AZURE_COSMOS_DB_ENDPOINT")
    key = os.getenv("AZURE_COSMOS_DB_KEY")
    if not endpoint or not key:
        raise ValueError("Azure Cosmos DBの環境変数が設定されていません。")
    return CosmosClient(url=endpoint, credential=key)

def get_cosmos_db_container(client: CosmosClient):
    """Cosmos DBのデータベースとコンテナーを取得または作成する。"""
    database_name = os.getenv("AZURE_COSMOS_DB_DATABASE_NAME", "cwbh-app-db")
    container_name = os.getenv("AZURE_COSMOS_DB_CONTAINER_NAME", "ImageTranslations")
    
    try:
        database = client.create_database_if_not_exists(id=database_name)
        # パーティションキーはユースケースに合わせて変更可能。
        # シンプルな構成のため、各ドキュメントが一意のIDを持つことを前提に "/id" を使用。
        # 大量データや特定のクエリパターンがある場合は、より適切なパーティションキーを検討。
        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400 # 無料枠を意識した初期スループット (必要に応じて調整)
        )
        print(f"Cosmos DB container '{container_name}' in database '{database_name}' is ready.")
        return container
    except cosmos_exceptions.CosmosHttpResponseError as e:
        print(f"Error getting/creating Cosmos DB container: {e}")
        raise

def save_translation_to_cosmos(container, item: dict):
    """翻訳データをCosmos DBに保存する。"""
    try:
        container.upsert_item(body=item) # create_itemからupsert_itemに変更し、ID重複時の更新も可能に
        print(f"Item with id '{item.get('id')}' saved to Cosmos DB.")
    except cosmos_exceptions.CosmosHttpResponseError as e:
        print(f"Error saving item id '{item.get('id')}' to Cosmos DB: {e}")
        raise

# 検索関数
def search_histories_cosmos(
    container,
    embeddings_service: AzureOpenAIEmbeddings,
    query_text: str,
    search_mode: str = 'hybrid',
    top_k: int = 5
) -> list:
    """
    Cosmos DBで履歴を検索する。モードに応じてベクトル検索、全文検索、ハイブリッド検索を切り替える。
    Args:
        container: Cosmos DBのコンテナーオブジェクト。
        embeddings_service: Azure OpenAIの埋め込みサービス。
        query_text (str): ユーザーからの検索クエリ。
        search_mode (str): 'vector', 'fulltext', または 'hybrid'。
        top_k (int): 取得する最大件数。
    Returns:
        list: 検索結果のドキュメントリスト。
    """
    if not query_text: return []
    
    results = []
    
    # --- ベクトル検索の実行 ---
    if search_mode in ['vector', 'hybrid']:
        try:
            query_embedding = embeddings_service.embed_query(query_text)
            # VectorDistanceのORDER BY句から 'ASC' を削除
            # VectorDistanceはデフォルトで昇順（距離が近い順）にソートするため、ASC/DESCの指定は不要
            vector_query = (
                f"SELECT TOP @top_k c.id, c.originalImageName, c.originalImageUrl, c.processedImageUrl, "
                f"c.originalText, c.translatedText, c.createdAt, VectorDistance(c.embedding, @query_vector) AS similarityScore "
                f"FROM c "
                f"WHERE IS_DEFINED(c.embedding) AND IS_ARRAY(c.embedding) "
                f"ORDER BY VectorDistance(c.embedding, @query_vector)"
            )
            print(f"Executing Vector Search with top_k={top_k}...")
            vector_results = list(container.query_items(
                query=vector_query,
                parameters=[
                    {"name": "@query_vector", "value": query_embedding},
                    {"name": "@top_k", "value": top_k}
                ],
                enable_cross_partition_query=True
            ))
            results.extend(vector_results)
            print(f"Vector search found {len(vector_results)} results.")
        except Exception as e:
            print(f"Error during vector search: {e}")
            if search_mode == 'vector': raise # ベクトル検索のみの場合はエラーを再スロー

    # --- 全文検索の実行 ---
    if search_mode in ['fulltext', 'hybrid']:
        try:
            # 全文検索用のクエリ。CONTAINS関数で日本語テキストを検索。
            # 大文字小文字を区別しないようにLOWER関数を使うとより良い。
            fulltext_query = (
                f"SELECT TOP @top_k c.id, c.originalImageName, c.originalImageUrl, c.processedImageUrl, "
                f"c.originalText, c.translatedText, c.createdAt "
                f"FROM c "
                f"WHERE CONTAINS(c.translatedText, @query_text, true)" # 3番目の引数 true で大文字小文字を無視
            )
            print(f"Executing Full-text Search with query_text='{query_text}'...")
            fulltext_results = list(container.query_items(
                query=fulltext_query,
                parameters=[
                    {"name": "@query_text", "value": query_text},
                    {"name": "@top_k", "value": top_k}
                ],
                enable_cross_partition_query=True
            ))
            results.extend(fulltext_results)
            print(f"Full-text search found {len(fulltext_results)} results.")
        except Exception as e:
            print(f"Error during full-text search: {e}")
            if search_mode == 'fulltext': raise # 全文検索のみの場合はエラーを再スロー

    # --- 結果のマージと重複排除 (ハイブリッド検索の場合) ---
    if search_mode == 'hybrid':
        final_results = []
        seen_ids = set()
        for item in results:
            if item['id'] not in seen_ids:
                final_results.append(item)
                seen_ids.add(item['id'])
        # ハイブリッド検索では、ベクトル検索の結果が先にリストに追加されるため、意味的に近いものが優先される
        print(f"Hybrid search merged to {len(final_results)} unique results.")
        return final_results[:top_k] # 最終的にtop_k件に絞る

    return results

# --- Blob Storage Functions ---

def init_blob_service_client() -> BlobServiceClient:
    """Blob Storageクライアントを初期化する。"""
    connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("Azure Blob Storageの接続文字列が設定されていません。")
    return BlobServiceClient.from_connection_string(connection_string)

def upload_image_to_blob(blob_service_client: BlobServiceClient, image_bytes: bytes, blob_name: str) -> str:
    """画像をBlob Storageにアップロードし、URLを返す。"""
    try:
        container_name = os.getenv("AZURE_BLOB_STORAGE_CONTAINER_NAME", "transcompicimages")
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        blob_client.upload_blob(image_bytes, overwrite=True)
        print(f"Image '{blob_name}' uploaded to Blob Storage container '{container_name}'. URL: {blob_client.url}")
        return blob_client.url
    except Exception as e: # より具体的な例外をキャッチすることも検討 (e.g., ResourceExistsError)
        print(f"Error uploading image '{blob_name}' to Blob Storage: {e}")
        raise
