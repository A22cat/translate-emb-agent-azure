# Azure AIエージェント、Azure OpenAI、Azure Cosmos DBを活用したエージェンティックアプリの構築

## 1. アプリ概要

- **タイトル**：TranslateEmbAgent（翻訳埋込エージェント）
- **プロダクト名**：TransEmbPic（トランスエンブピック）  
  → Translate + Embed + Picture の造語。

**概要**  
画像から外国語を抽出し、母国語に翻訳・埋め込み・保存するWebアプリ。  
翻訳とベクトル埋め込みを組み合わせた新しい知識活用体験を提供するエージェント型アプリです。本アプリは、画像から外国語（英語）テキストを抽出し、母国語（日本語）に翻訳します。そして、画像に翻訳文（日本語訳）を挿入し保存まで自動で実施するWebアプリです。AzureのAIサービスを活用することで、高精度かつ実用的な画像検索と翻訳体験を提供します。

---

## 2. 解決する課題と利用シーン

語学学習や多言語業務の現場では、教材や案内文が外国語のみで提供されることが多く、内容の理解が難しくなることで、学習や業務の効率が低下することがあります。また、絵本や漫画の翻訳業務では、専門的な語彙や独特の表現、文化的なニュアンスを正確に把握し適切に伝える必要があるため、翻訳作業が難航することがあります。

**TranslateEmbAgent（翻訳埋込エージェント）は、こうした言葉の壁を解消し、次のようなシーンで役立ちます。**

- 教育関係者：語学学習教材の母国語補助表示
- 多言語業務現場：外国語案内文の理解や情報共有
- 翻訳業務：絵本や漫画といったクリエイティブコンテンツの翻訳支援

---

## 3. 主な機能

1. PNG/JPG画像のアップロード
2. 画像の外国語テキスト（英語）を抽出（OCR）し母国語（日本語）への自動翻訳
3. 翻訳文を画像に埋め込み、加工済み画像を自動保存しダウンロード
4. 過去の翻訳履歴検索（ベクトル検索、ベクトル検索(意味で探す)、全文検索(キーワード)の検索モード）

---

## 4. 技術構成（Tech Stack）

- LangChain
- Azure Computer Vision (OCR API)
- Azure Translator (Text API)
- Azure OpenAI (Embeddingモデル)
- Azure Cosmos DB (JSONドキュメント + ベクトルインデックス)
- Azure Blob Storage (元画像と加工済み画像保存)
- Azure App Service
- Python
- Streamlit (UI)
- Pillow (Pythonライブラリ)

---

## 5. エージェント構成（Langchain）

エージェント構成と役割

    | エージェント名         | 役割                                                                                                                                          |
    |------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
    | OCRエージェント        | 画像から英語テキストを抽出（Azure Computer Vision OCR API）                                                                                 |
    | 翻訳エージェント       | 抽出された英語を日本語に翻訳（Azure Translator Text API）                                                                                   |
    | 埋込・保存エージェント | ・翻訳結果を画像に合成（Pillow）し、Azure Blob Storageに保存  
                             ・翻訳文とメタ情報をCosmos DBへ保存  
                             ・埋込用ベクトルを生成し、類似検索に対応（Azure OpenAI Embedding + Cosmos DB ベクトルインデックス） |


---

## 6. 拡張構想

- Semantic KernelのPlannerで「どのエージェントを呼ぶか」をLLMに判断させる（高度なルーティング・状態保持が必要な場合）：Semantic KernelをLangChainと併用活用
- 多言語対応（ドイツ語など）：Azure Translatorのパラメータ設定により拡張可能
- 音声読み上げ（TTS）：Azure Speech (Text to Speech)を活用
- ユーザー別の履歴・翻訳傾向管理：ユーザー認証＋Cosmos DBにユーザーID単位で履歴を保存・分析（認証には Azure AD B2C または Firebase Auth などが候補）
- 音声認識による入力（STT）：マイク入力UI＋Azure Speech to Textの組み込み
- 音声関連機能は Azure Speech Services で統一的に実装可能（TTSとSTTを両立）
- 会話型UI：Chat風インターフェース導入（Streamlit Chat UI等）

---

## 7. GitHubリポジトリのURL

- メインリポジトリ：  
  https://github.com/A22cat

- 本課題実装のリポジトリ：  
  https://github.com/A22cat/translate-emb-agent-azure
