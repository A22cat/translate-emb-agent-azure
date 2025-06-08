## タスク

## バックエンドにCosmos DBを作成し、コレクションやスキーマ、ベクトル化するプロパティを特定してください

1. コードでの確認
    - コレクション (コンテナー) 名: 環境変数のAZURE_COSMOS_DB_CONTAINER_NAME (例: ImageTranslations) で定義され、src/services/database_services.py の get_cosmos_db_container 関数で使用。)

        - スキーマ: src/agents/image_processing_agent.py の _embed_and_save_step 関数内で item_to_save として定義されています。主なプロパティは以下の通りです。
        - id: ドキュメントの一意なID (UUID)。パーティションキーとしても使用。
        - originalImageName: アップロードされた元の画像ファイル名。
        - originalImageUrl: Blob Storageに保存された元画像のURL。
        - processedImageUrl: Blob Storageに保存された加工済み画像のURL。
        - originalText: OCRで抽出された原文。
        - translatedText: 翻訳されたテキスト。
        - embedding: ベクトル化されたプロパティ。
        - translatedText (日本語の翻訳文) から生成されたベクトルデータが格納されます。
        - originalLang: 原文の言語コード (例: "en")。
        - translatedLang: 翻訳文の言語コード (例: "ja")。
        - createdAt: データ作成日時 (ISOフォーマット)。
        - ベクトル化するプロパティ: 上記スキーマの embedding フィールドです。これは日本語の translatedText をAzure OpenAIのEmbeddingモデルでベクトル化したものです。


2. Azure Portalでの確認:
    - Azure Portalにサインインし、Cosmos DBアカウントに移動します。
    - 「データエクスプローラー」を開き、指定したデータベース（例: TranslateEmbAgentDB）とコンテナー（例: ImageTranslations）を選択します。
    - 「Items（項目）」タブで、アプリケーションで処理を実行した後に作成されたドキュメント（アイテム）を選択し、そのJSON構造を確認します。embedding プロパティに数値の配列（ベクトル）が格納されていることを確認します。
    - コンテナーの「設定」で、インデックスポリシーを確認し、/embedding パスに対してベクトルインデックスが設定されていることを確認します（例: {"vectorIndexes":[{"path":"/embedding","type":"quantizedFlat"}]}）。


## アプリケーションをコーディングし、CRUD操作の実装



## ベクトル検索機能（全文検索やハイブリッド検索)