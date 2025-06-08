# セットアップ手順 (デプロイ手順含む)

このガイドでは、「TranslateEmbAgent」アプリケーションのローカルでのセットアップと、Azure App ServiceへのVSCodeを利用したデプロイ手順について説明します。

## 1. 前提条件

* Python 3.9 以上 (3.11推奨)
* Azureアカウントとアクティブなサブスクリプション
* Visual Studio Code (VSCode)
    * 拡張機能:
        * Azure Account (Microsoft製)
        * Azure App Service (Microsoft製)
        * Python (Microsoft製)

## 2. Azureリソースの準備

以下のAzureサービスをAzure Portalで作成し、必要な情報（エンドポイント、APIキー、接続文字列など）を控えておきます。これらの情報は後で `.env` ファイルまたはApp Serviceのアプリケーション設定で使用します。

* **リソースグループ**: 全てのリソースをまとめるグループ (例: `TranslateEmbAgent-RG`)
* **Azure OpenAI Service**:
    * Embeddingモデルをデプロイ (例: `text-embedding-ada-002`)
    * 控える情報: APIキー, エンドポイントURL, Embeddingモデルのデプロイ名
* **Azure AI Vision (Computer Vision)**:
    * 控える情報: APIキー, エンドポイントURL
* **Azure AI Translator**:
    * 控える情報: APIキー, エンドポイントURL, リソースのリージョン
* **Azure Cosmos DB for NoSQL**:
    * データベースを作成 (例: `TranslateEmbAgentDB`)
    * コンテナーを作成 (例: `ImageTranslations`、パーティションキー: `/id`)
        * **重要**: コンテナー作成後、「設定」>「ベクトルインデックスポリシー」で、Embeddingベクトルを保存するプロパティ（例: `/embedding`）に対してベクトルインデックスを設定します。Embeddingモデルの次元数に合わせて設定してください (例: `text-embedding-ada-002` の場合、1536次元)。
    * 控える情報: アカウントのエンドポイントURL, プライマリキー
* **Azure Blob Storage (ストレージアカウント)**:
    * コンテナーを作成 (例: `transcompicimages`、アクセスレベル: プライベート推奨)
    * 控える情報: 接続文字列

## 3. ローカル環境でのセットアップと実行

1.  GitHub.com からローカルコンピューターにリポジトリをクローンします。
    **リポジトリのクローン**:
    ```bash
    git clone <リポジトリのURL>
    cd translate-emb-agent-azure
    ```
2. プロジェクトのルートディレクトリで、ターミナルを開きます。
3. .env.example をコピーして `.env` という名前のファイルを作成します。Azureリソースの作成時に控えた各サービスのキーとエンドポイントをすべて設定します。
必要なPythonパッケージをインストールします。

Bash
```
pip install -r requirements.txt
```

Streamlitアプリを起動します。

Bash
```
streamlit run src/main_db_chat_ai.py
```
ブラウザで http://localhost:8501 が開き、アプリケーションが表示されます。

## 5. VSCodeを使用したAzure App Serviceへのデプロイ
VSCodeのAzure拡張機能を使って、アプリケーションをデプロイします。

1. Azure ポータルでApp Service を開き、左側のメニューから 「設定」 >「環境変数」を選択し、[+追加]からアプリケーション設定にenvファイルの内容を一つずつ環境変数として追加します。
    - 名前：環境変数のキー（例：AZURE_OPENAI_ENDPOINT）
    - 値：環境変数の値 (例：https://your-resource.openai.azure.com/)
2. 左側のメニューから 「構成」(Configration) > 全般設定 を選択し、「スタートアップコマンド」に以下を設定して保存します。
```
python -m streamlit run src/main_db_chat_ai.py --server.port 8000 --server.address 0.0.0.0
```

3. 次にVSCodeで「ファイル」>「フォルダーを開く...」でプロジェクトフォルダ（query-chatdb-azure）を選択し、開きます。
4. 左のアクティビティバーからAzureアイコンを選択し、Azureアカウントにサインインします。
5. Azure拡張機能パネルに戻り、リソースの一覧からデプロイ先のApp Serviceを探します。
対象のApp ServiceはStoppedではなく通常は起動したままデプロイします。
6. 対象のApp Serviceを右クリックし、「Deploy to Web App...」を選択します。

7. 「Would you like to update your workspace configuration to run build commands on the target server?This should improve deployment performance.」の確認メッセージが表示されたら、「Yes」を選択します。「Yes」を選ぶと、今後同じワークスペースからデプロイする際に、ビルドコマンド（依存パッケージのインストールなど）がAzure側で実行されるように設定され、デプロイが効率化されます。この設定は .vscode/settings.json に保存され、プロジェクト単位で適用されます。後から変更したい場合も、ワークスペース設定で編集できます。
8. 「Are you sure you want to deploy to "<App Service名>"? This will overwrite any previous deplyment and cannot be undone.」の確認メッセージが表示されたら、「Deploy」を選択します。現在のWebアプリに新しいコードを上書いてデプロイします。
8. デプロイが完了すると通知が表示されます。その後、App ServiceのURLにアクセスして、アプリケーションが正しく動作することを確認します。



