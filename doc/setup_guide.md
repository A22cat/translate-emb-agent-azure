# 翻訳埋込エージェント： セットアップ手順 (デプロイ手順含む)

翻訳埋込エージェントのセットアップに関する設定、ローカル環境での実行手順、および、Azure App Serviceへのデプロイ手順の概要を説明します。

## 1. 前提条件

- [Azureアカウント](https://azure.microsoft.com/ja-jp/free/)
- [Python 3.10 以降](https://www.python.org/downloads/)
- [Visual Studio Code](https://code.visualstudio.com/)
  - [Azure App Service 拡張機能](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureappservice)
  - [Python 拡張機能](https://marketplace.visualstudio.com/items?itemName=ms-python.python)


## 2. Azureリソースの準備

Azureポータルにログインし、以下のリソースを作成します。リソース名は任意ですが、後で環境変数に設定するため控えておいてください。

### a. Azure OpenAI Service

1.  Azureポータルで「Azure OpenAI」を検索し、「作成」を選択します。
2.  サブスクリプション、リソースグループ、リージョン、一意の名前を入力します。
3.  価格レベルは「Standard S0」を選択します。
4.  作成後、リソースに移動し、「モデルのデプロイ」メニューから以下のモデルをデプロイします。
    -   **Embeddingモデル**: `text-embedding-ada-002`または `text-embedding-3-small`など
    -   **開発環境では、コストを考慮すると `text-embedding-3-small` の選択肢を検討することができます。
5.  「キーとエンドポイント」から**エンドポイント**と**キー1**をコピーします。

### b. Azure Cosmos DB（Azure Cosmos DB for NoSQL）

1.  Azureポータルで「Azure Cosmos DB」を検索し、「作成」を選択します。
2.  「Azure Cosmos DB for NoSQL」の「create(作成)」を選択します。
3.  リソースグループ、アカウント名、場所などを設定します。
4.  作成後、リソースに移動し、「データエクスプローラー」から新しいデータベースとコンテナを作成します。
    「データエクスプローラー」 > 「新しいデータベース作成」(=「+New Database」)
    -   データベース名:例 `TranslateEmbAgentDB`
5.  作成済みのデータベースの「…」ボタンを選択>「+ New Container」(=「新しいコンテナー」)を選択します。
	以下の情報を入力して「OK」で作成します。
    -   パーティションキー：例 ` /userId`
    -   Database id：Use existing：`TranslateEmbAgentDB`(=データベース ID	作成したデータベースを選択（例：`TranslateEmbAgentDB`）)
    -   コンテナーID：`ImageTranslations`	コンテナ名。
    -   Indexing Mode：Automatic
    -   (途中で変更不可)パーティション キー：例 `/userId`	IDまたは高頻度アクセスのキーにするのが一般的。 ユーザーごとのデータを考慮する場合。シンプルな構成なら /id などでも可)
    -   Dedicated Throughput(=Provision dedicated throughput for this container)：OFF（チェックしない）  
        スループットのチェック不要、すでに データベース共有スループットで作成済みのため、このチェックは外す（データベース側に任せる）
    -   ユニークキー：任意(今回はなし)
    -   Enable analytical store capability to perform near real-time analytics on your operational data, without impacting the performance of transactional workloads. 
        分析ストア機能を有効にして、トランザクション ワークロードのパフォーマンスに影響を与えることなく、運用データに対してほぼリアルタイムの分析を実行します。
    →「分析ストア機能（Analytical Store）を有効にするかどうか」の設定について、現状および目的を踏まえたおすすめは**「OFF（無効）」**です。理由：無料枠の維持・分析用途が現時点でないため。
6.  「キー」メニューから**URI**と**プライマリキー**を控えます。
    ```
    ●作成するコンテナ一覧
    - コンテナ ID：`ImageTranslations`、用途：質問履歴やチャット履歴、パーティションキー(名称は任意)：`/userId`
    ```
    #### 注意点
    - **パーティションキーは後から変更できません。最初に慎重に設計してください。**
    - **Database Throughput**  
      スループット設定画面にて「**スループットをこのコンテナーにプロビジョニングする**」のチェックは **外してください**。  
      ※チェックを入れると、そのコンテナーに対して専用スループットが割り当てられ、**個別課金の対象**になります。


### c. Azure Computer Vision
1.  「Computer Vision」を検索し、「作成」を選択します。
2.  リソースグループ、リージョン、名前（例: translate-emb-agent-vision）、価格レベル（Free F0 または Standard S1）を選択します。
3.  作成後、リソースに移動し、「キーとエンドポイント」からキー1とエンドポイントURLを控えます


### d. Azure AI Translator
1.  (必須)「リソースの作成」ボタンをクリックします。(=「+リソースの作成」ボタン)
2.  (必須)検索ボックスに「Translator」と入力し、「作成」をクリックします。次に「Translator」の下の「作成」ドロップダウンをクリックし、「Translator」をクリックします。
3.  「基本」タブでリソースグループ、リージョン(例:japanwest/japaneast)、名前（例:translate-emb-agent-translator01）を入力する。
4.  作成後、リソースに移動し、「キーとエンドポイント」からキー1、場所/地域を控えます。
5.  次のサービス名とリソースタイプが作成されています。
    - サービス名：「Cognitive Services」
    - リソースタイプ：Microsoft.CognitiveServices/accounts
この場合、エンドポイントは以下のように構成されます：
```
https://<your-resource-name>.cognitiveservices.azure.com/
```
このURLを自分で手動で組み立てます。


具体例：  
- 名前＝リソース名：translate-emb-agent-translator01
- リソースの種類：Microsoft.CognitiveServices/accounts

この場合、エンドポイントは以下で構成されます：
```
https://translate-emb-agent-translator01.cognitiveservices.azure.com/
```

※注意：Microsoft Azureの青色の検索欄で「Translator」を検索し、Marketplaceの「Translator」の作成とは異なります。


### e. Azure Blob Storage
1. 「ストレージアカウント」(transcompicimages01)を検索し、「作成」。
2. リソースグループ、ストレージアカウント名（例: transcompicstorage01、グローバルに一意である必要あり）、リージョン、プライマリサービス(Azure Blob StorageまたはAzure Data Lake Storage Gen2)パフォーマンス（Standard）、冗長性（LRS）を選択。
3. 作成後、「リソースに移動」。
4. 「コンテナー」を選択し、「+ コンテナー」で新しいコンテナーを作成。
   ・名前: transcompicimages← この値がAZURE_BLOB_STORAGE_CONTAINER_NAME=の値となる。
   ・パブリックアクセスレベル: 「プライベート（匿名アクセスなし）」または必要に応じて「BLOB」
5. 「アクセスキー」から"接続文字列"を控えます。


### f. Azure App Service

1.  Azureポータルで「App Service」を検索し、「作成」>「Webアプリ」を選択します。
2.  サブスクリプション、リソースグループを選択します。
3.  インスタンスの詳細：
    -   名前: グローバルに一意な名前 (例: `trans-emb-pic-app`)
    -   発行: `コード`
    -   ランタイム スタック: `Python 3.11` [Python(準備のセクションでインストールしたものと同じバージョンまたは一番近いバージョン)] を選択します。
    -   オペレーティング システム: `Linux` (Pythonは2025/06現在[Linux]のみサポート)
    -   地域: 地域を選択
4.  「App Service プラン」を選択または新規作成します。
5.  作成後、リソースに移動します。この時点ではデプロイは不要です。


## 3. ローカル環境での実行
1. GitHub.com からローカルコンピューターにリポジトリをクローンします。
2. プロジェクトのルートディレクトリで、ターミナルを開きます。
3. .env.example をコピーして `.env` という名前のファイルを作成します。
Azureリソースの作成時に控えた各サービスのキーとエンドポイントをすべて設定します。
必要なPythonパッケージをインストールします。

Bash
```
pip install -r requirements.txt
```

Streamlitアプリを起動します。

Bash
```
streamlit run src/main_trans_azure.py
```
ブラウザで http://localhost:8501 が開き、アプリケーションが表示されます。


## 4. VSCodeを使用したAzure App Serviceへのデプロイ
VSCodeのAzure拡張機能を使って、アプリケーションをデプロイします。

1.  Azure ポータルでApp Service を開き、左側のメニューから 「設定」 >「環境変数」を選択し、[+追加]からアプリケーション設定にenvファイルの内容を一つずつ環境変数として追加します。
    - 名前：環境変数のキー（例：AZURE_OPENAI_ENDPOINT）
    - 値：環境変数の値 (例：https://your-resource.openai.azure.com/)
2.  左側のメニューから 「構成」(Configration) > 全般設定 を選択し、「スタートアップコマンド」に以下を設定して保存します。

```
python -m streamlit run src/main_trans_azure.py --server.port 8000 --server.address 0.0.0.0
```

3. 次にVSCodeで「ファイル」>「フォルダーを開く...」でプロジェクトフォルダ（`translate-emb-agent-azure`）を選択し、開きます。
4. 左のアクティビティバーからAzureアイコンを選択し、Azureアカウントにサインインします。
5. Azure拡張機能パネルに戻り、リソースの一覧からデプロイ先のApp Serviceを探します。
対象のApp ServiceはStoppedではなく通常は起動したままデプロイします。
6. 対象のApp Serviceを右クリックし、「Deploy to Web App...」を選択します。
7. 「Would you like to update your workspace configuration to run build commands on the target server?This should improve deployment performance.」の確認メッセージが表示されたら、「Yes」を選択します。「Yes」を選ぶと、今後同じワークスペースからデプロイする際に、ビルドコマンド（依存パッケージのインストールなど）がAzure側で実行されるように設定され、デプロイが効率化されます。この設定は .vscode/settings.json に保存され、プロジェクト単位で適用されます。後から変更したい場合も、ワークスペース設定で編集できます。
8. 「Are you sure you want to deploy to "<App Service名>"? This will overwrite any previous deplyment and cannot be undone.」の確認メッセージが表示されたら、「Deploy」を選択します。現在のWebアプリに新しいコードを上書いてデプロイします。
8. デプロイが完了すると通知が表示されます。その後、App ServiceのURLにアクセスして、アプリケーションが正しく動作することを確認します。