# TransEmbPic - 翻訳埋込エージェント

画像から外国語（英語）を抽出し、母国語（日本語）に翻訳・埋め込み・保存するWebアプリケーションです。
AzureのAIサービス（Azure AI Vision, Azure AI Translator, Azure OpenAI Embeddings, Azure Cosmos DB, Azure Blob Storageを使用し、Langchainを活用して処理を連携させています。


## 概要

本アプリは、画像内の英語テキストをOCRで抽出し、日本語に翻訳します。そして、翻訳文を元画像に埋め込み、加工済み画像として保存・ダウンロードできます。過去の翻訳履歴はベクトル検索により、意味的に類似した内容を効率的に検索可能です。

**主な機能:**

1.  PNG/JPG画像のアップロード
2.  画像の外国語テキスト（英語）を抽出し母国語（日本語）への自動翻訳
3.  翻訳文を画像に埋め込み、加工済み画像を自動保存しダウンロード
4.  過去の翻訳履歴検索（ベクトル検索、ベクトル検索(意味で探す)、全文検索(キーワード)の検索モード）

## 技術スタック

* **UI**: Streamlit
* **開発言語**: Python
* **エージェント/チェーン連携**: Langchain
* **OCR**: Azure AI Vision
* **翻訳**: Azure AI Translator
* **Embedding生成**: Azure OpenAI Service (Embeddingモデル)
* **データベース (メタデータ + ベクトルストア)**: Azure Cosmos DB for NoSQL
* **画像保存**: Azure Blob Storage
* **画像合成**: Pillow (Pythonライブラリ)
* **実行環境**: Azure App Service

## セットアップと実行

詳細は `doc/setup_guide.md` を参照してください。

1.  リポジトリをクローンします。
2.  必要なAzureサービスをAzure Portalで作成・設定します。
3.  `.env` ファイルに必要な環境変数を設定します。
4.  Pythonの依存関係をインストールします: `pip install -r requirements.txt`
5.  Streamlitアプリを実行します: `streamlit run src/main_trans_azure.py`

## フォルダ構成

フォルダ構成は `directory_structure.txt` を参照してください。
