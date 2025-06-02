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

def vector_search_cosmos(container, embeddings_service: AzureOpenAIEmbeddings, query_text_for_embedding: str, top_k: int = 3) -> list:
    #デフォルト値 3,呼び出し側でtop_k が指定されなかったら 3 を使う。
    #関数を呼び出す際にその引数に値を渡すと、デフォルト値ではなく渡された値が使用される(main_trans_azure.pyでの呼び出し側のtop_k)
    """Cosmos DBでベクトル検索を実行する。"""
    if not query_text_for_embedding:
        return []
        
    try:
        query_embedding = embeddings_service.embed_query(query_text_for_embedding)
        
        # VectorDistance関数の利用には、Cosmos DBアカウントでベクトル検索機能が有効になっている必要がある。
        # また、コンテナのインデックスポリシーにベクトルインデックスが正しく定義されている必要がある。
        # 例: {"vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}]}
        # (dimensionsは使用するEmbeddingモデルに合わせる。例: text-embedding-ada-002なら1536)
        
        # TOP @top_k をクエリに追加
        query = (
            f"SELECT TOP @top_k c.id, c.originalImageName, c.originalImageUrl, c.processedImageUrl, "
            f"c.originalText, c.translatedText, c.createdAt, VectorDistance(c.embedding, @query_vector) AS similarityScore "
            f"FROM c "
            f"ORDER BY VectorDistance(c.embedding, @query_vector) " # 昇順 (距離が小さいほど類似)
        )

        results = list(container.query_items(
            query=query,
            parameters=[
                {"name": "@query_vector", "value": query_embedding},
                {"name": "@top_k", "value": top_k} # top_kをパラメータとして渡すことを追加して、実際の件数を指定
            ],
            enable_cross_partition_query=True # パーティションキーが "/id" の場合は実質不要だが念のため
        ))
        
        # Cosmos DBのクエリでTOP句が有効な場合、クライアント側でのソートやスライスは不要になることが多い。
        # ORDER BYで既にソートされているため、そのまま返す。
        print(f"Vector search found {len(results)} results for query (TOP {top_k}).")
        return results

    except Exception as e:
        # CosmosHttpResponseErrorだけでなく、一般的な例外もキャッチ
        print(f"Error during vector search in Cosmos DB: {e}")
        # エラー時は空リストを返す
        return []

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
