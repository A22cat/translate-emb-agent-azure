# TransEmbPic - 翻訳埋込エージェント

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33-ff69b4.svg)](https://streamlit.io/)
[![Azure](https://img.shields.io/badge/Azure-Services-blue.svg)](https://azure.microsoft.com/)

画像から外国語（英語）を抽出し、母国語（日本語）に翻訳・埋め込み・保存するWebアプリケーションです。
AzureのAIサービス（Azure AI Vision, Azure AI Translator, Azure OpenAI Embeddings, Azure Cosmos DB, Azure Blob Storageを使用し、Langchainを活用して処理を連携させています。

## ✨ 主な機能

- PNG/JPG画像のアップロード
- 画像の外国語テキスト（英語）を抽出し母国語（日本語）への自動翻訳
- 翻訳文を画像に埋め込み、加工済み画像を自動保存しダウンロード
- 過去の翻訳履歴検索（ベクトル検索、ベクトル検索(意味で探す)、全文検索(キーワード)の検索モード）


## 🚀 技術構成 [Tech Stack]
- Azure Computer Vision (OCR API)
- Azure Translator (Text API)
- Azure OpenAI (Embedding API)
- Azure Cosmos DB (JSONドキュメント + ベクトルインデックス)
- Azure Blob Storage
- Azure App Service
- LangChain
- Python
- Streamlit (UI)
- Pillow (Pythonライブラリ)


## 📂 フォルダ構成

フォルダ構成は `directory_structure.txt` を参照してください。


## 🛠️ セットアップに関する設定、ローカル環境での実行手順、および、Azure App Serviceへのデプロイ手順

詳細な手順は `doc/setup_guide.md` を参照してください。


## ▶️ デモ動画URL
デモ動画URL：
https://www.youtube.com/watch?v=WQckMI934N0

本動画は、翻訳埋込エージェントの4分間デモ動画でございます。
