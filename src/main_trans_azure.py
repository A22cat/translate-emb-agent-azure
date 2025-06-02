import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime
# import io # ioモジュールは直接使用していないためコメントアウト

# LangchainとAzure SDK関連のインポート
from langchain_openai import AzureOpenAIEmbeddings
from services.database_services import (
    init_cosmos_db_client,
    get_cosmos_db_container,
    vector_search_cosmos,
    init_blob_service_client
)
from agents.image_processing_agent import create_image_processing_chain

# --- アプリケーション設定と初期化 ---
st.set_page_config(page_title="TransEmbPic - 翻訳埋込エージェント", layout="wide", page_icon="⚛️")
load_dotenv() # .envファイルから環境変数を読み込む

# --- セッションステートの管理 ---
# エラーメッセージや処理結果をセッションまたいで保持するために使用
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "clients_initialized_successfully" not in st.session_state:
    st.session_state.clients_initialized_successfully = False
if "search_history_results" not in st.session_state:
    st.session_state.search_history_results = []
if "last_processed_result" not in st.session_state:
    st.session_state.last_processed_result = None


# --- Azureサービスクライアントの初期化 (Streamlitのキャッシュ機能を利用) ---
@st.cache_resource # リソースをキャッシュして再初期化を防ぐ
def initialize_all_clients():
    """
    必要なAzureサービスクライアントとLangChainエージェントを初期化する。
    Returns:
        dict: 初期化されたクライアントとチェーンを含む辞書。初期化失敗時はNone。
    """
    try:
        print("Initializing Azure services and LangChain agent...")
        # Azure OpenAI Embeddingsクライアント
        embeddings_service = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"), # .envで指定したバージョン
            # azure_endpointとapi_keyは環境変数から自動で読み込まれる想定 (SDKの挙動による)
            # 明示的に指定する場合は以下のようにする
            # azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        
        # Azure Cosmos DBクライアントとコンテナー
        cosmos_db_client = init_cosmos_db_client()
        cosmos_db_container = get_cosmos_db_container(cosmos_db_client)
        
        # Azure Blob Storageクライアント
        blob_storage_client = init_blob_service_client()
        
        # 画像処理チェーン (エージェント)
        image_processing_chain = create_image_processing_chain(
            embeddings_service, cosmos_db_container, blob_storage_client
        )
        
        print("All clients and agent initialized successfully.")
        st.session_state.clients_initialized_successfully = True
        return {
            "embeddings": embeddings_service,
            "cosmos_container": cosmos_db_container,
            "blob_client": blob_storage_client, # 将来的に使うかもしれないので保持
            "processing_chain": image_processing_chain
        }
    except Exception as e:
        st.session_state.error_message = f"サービスの初期化中に重大なエラーが発生しました: {e}"
        st.session_state.clients_initialized_successfully = False
        print(st.session_state.error_message) # ログにも出力
        return None

# アプリケーション開始時にクライアントを初期化
initialized_clients = initialize_all_clients()

if not st.session_state.clients_initialized_successfully:
    st.error(f"アプリケーションの起動に必要なサービスの初期化に失敗しました。詳細はログを確認してください。エラー: {st.session_state.error_message}")
    st.stop() # 初期化失敗時はアプリを停止

# --- Streamlit UIレイアウト ---
st.title("🌐 TransEmbPic - 翻訳埋込エージェント")
st.caption("画像から外国語を抽出し、母国語に翻訳・埋め込み・保存するWebアプリ (Azure AI活用)")

# --- メイン処理セクション (画像アップロードと処理実行) ---
main_processing_col1, main_processing_col2 = st.columns(2)

with main_processing_col1:
    st.header("1. 画像をアップロード")
    uploaded_image_file = st.file_uploader(
        "翻訳したい画像 (PNG, JPG, JPEG) を選択してください:",
        type=["png", "jpg", "jpeg"],
        disabled=not st.session_state.clients_initialized_successfully # 初期化失敗時は無効化
    )

    if uploaded_image_file is not None:
        uploaded_image_bytes = uploaded_image_file.getvalue()
        uploaded_image_name = uploaded_image_file.name
        st.image(uploaded_image_bytes, caption=f"アップロードされた画像: {uploaded_image_name}", use_container_width=True)

        if st.button("🤖 AIエージェントで処理実行", disabled=not st.session_state.clients_initialized_successfully, type="primary"):
            with st.spinner("AIエージェントが画像処理を実行中です... (OCR → 翻訳 → 埋込 → 保存)"):
                try:
                    chain_input_data = {"image_bytes": uploaded_image_bytes, "image_name": uploaded_image_name}
                    # LangChainエージェント (処理チェーン) を呼び出し
                    processing_result = initialized_clients["processing_chain"].invoke(chain_input_data)
                    
                    st.session_state.last_processed_result = processing_result # 最新の処理結果を保存
                    
                    if processing_result.get("error"):
                        st.error(f"処理中にエラーが発生しました: {processing_result['error']}")
                    elif processing_result.get("message"):
                        st.success(processing_result["message"])
                    else:
                        st.info("処理は実行されましたが、予期しない結果となりました。")
                
                except Exception as e:
                    st.session_state.last_processed_result = None
                    st.error(f"画像処理の実行中に予期せぬエラーが発生しました: {e}")

with main_processing_col2:
    st.header("2. 最新の処理結果")
    if st.session_state.last_processed_result:
        result_data = st.session_state.last_processed_result
        saved_item_info = result_data.get("item_saved") # 保存されたアイテム情報
        
        if saved_item_info:
            st.subheader("抽出＆翻訳テキスト")
            st.text_area("抽出されたテキスト (原文)", saved_item_info.get("originalText", "N/A"), height=100, disabled=True)
            st.text_area("翻訳されたテキスト (訳文)", saved_item_info.get("translatedText", "N/A"), height=100, disabled=True)
            
            st.subheader("加工済み画像")
            processed_image_display_bytes = result_data.get("processed_image_bytes")
            if processed_image_display_bytes:
                st.image(processed_image_display_bytes, caption="翻訳が埋め込まれた画像", use_container_width=True)
                st.download_button(
                    label="加工済み画像をダウンロード",
                    data=processed_image_display_bytes,
                    file_name=f"processed_{saved_item_info.get('originalImageName', 'image.png')}",
                    mime="image/png"
                )
            elif saved_item_info.get("processedImageUrl"): # Blob URLがある場合 (バイトデータがない場合)
                st.image(saved_item_info.get("processedImageUrl"), caption="加工済み画像 (ストレージより)", use_container_width=True)
            else:
                st.info("加工済み画像は生成されませんでした (または、埋め込むテキストがありませんでした)。")
        elif result_data.get("message"):
             st.info(result_data.get("message")) # エージェントからのメッセージ表示
        else:
            st.info("まだ画像処理が実行されていません。")
    else:
        st.info("画像をアップロードして「処理実行」ボタンを押してください。")

st.divider() # セクション区切り

# --- 翻訳履歴検索セクション ---
st.header("3. 翻訳履歴検索 (ベクトル検索)")
search_query_text = st.text_input(
    "検索キーワード (日本語の翻訳文から意味的に類似した履歴を検索します):",
    disabled=not st.session_state.clients_initialized_successfully
)

if st.button("🔍 履歴を検索", disabled=not st.session_state.clients_initialized_successfully):
    if search_query_text:
        with st.spinner("過去の翻訳履歴をベクトル検索中..."):
            try:
                # データベース検索サービスを呼び出し
                st.session_state.search_history_results = vector_search_cosmos(
                    initialized_clients["cosmos_container"],
                    initialized_clients["embeddings"],
                    search_query_text,
                    top_k=5 # 表示する検索結果の最大数
                )
                if not st.session_state.search_history_results:
                    st.info("検索キーワードに一致する翻訳履歴は見つかりませんでした。")
            except Exception as e:
                st.error(f"履歴検索中にエラーが発生しました: {e}")
                st.session_state.search_history_results = []
    else:
        st.warning("検索キーワードを入力してください。")

# 検索結果の表示
if st.session_state.search_history_results:
    st.subheader(f"検索結果: {len(st.session_state.search_history_results)} 件")
    for db_item in st.session_state.search_history_results:
        # 日付フォーマットを調整 (例: '2023-10-27T10:30:00.123456Z' -> '2023-10-27 10:30')
        # 類似度スコアの表示準備 (Unknown format code 'f' for object of type 'str'のエラー修正箇所)
        created_at_display = db_item.get('createdAt', 'N/A')
        if created_at_display != 'N/A' and created_at_display is not None:
            try:
                # 'Z'を'+00:00'に置換してISOフォーマット文字列をパース可能にする
                # datetime.fromisoformat はマイクロ秒も扱える
                dt_obj = datetime.fromisoformat(created_at_display.replace('Z', '+00:00'))
                created_at_display = dt_obj.strftime('%Y-%m-%d %H:%M')
            except ValueError as e_date:
                # パース失敗時は元の文字列を使用。デバッグ用にエラー内容をコンソールに出力しても良い
                # print(f"DEBUG: Failed to parse date string '{db_item.get('createdAt')}': {e_date}")
                pass 

        # 類似度スコアの表示準備 (Unknown format code 'f' for object of type 'str'のエラー修正箇所)
        similarity_score_value = db_item.get('similarityScore')
        if isinstance(similarity_score_value, (float, int)):
            similarity_score_display = f"{similarity_score_value:.4f}"
        elif similarity_score_value is None:
            similarity_score_display = 'N/A' # None の場合は 'N/A' と表示
        else:
            # 文字列型で 'N/A' が入っている場合や、予期せぬ型の場合はそのまま文字列として表示
            similarity_score_display = str(similarity_score_value)

        expander_title = (
            f"翻訳日: {created_at_display} - "
            f"元ファイル: {db_item.get('originalImageName', 'N/A')} "
            f"(類似度スコア: {similarity_score_display})" # 事前に処理したスコア表示(類似度スコア表示)
        )
        with st.expander(expander_title):
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.markdown(f"**翻訳文 (日本語):**")
                st.info(f"{db_item.get('translatedText', '翻訳文なし')}")
                st.markdown(f"**抽出文 (英語):** \n {db_item.get('originalText', '原文なし')}")
                #print(f"Debug: Original Image URL from Cosmos DB: {db_item.get('originalImageUrl')}") # デバッグ用に追加
                #print(f"Debug: Processed Image URL from Cosmos DB: {db_item.get('processedImageUrl')}") # デバッグ用に追加
                if db_item.get('originalImageUrl'):
                    st.image(db_item['originalImageUrl'], caption="元画像 (ストレージより)", use_container_width=True)

            with res_col2:
                if db_item.get('processedImageUrl'):
                    st.image(db_item['processedImageUrl'], caption="加工済み画像 (ストレージより)", use_container_width=True)
                else:
                    st.write("この履歴には加工済み画像はありません。")
