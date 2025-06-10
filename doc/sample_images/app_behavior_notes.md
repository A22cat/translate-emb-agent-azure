# **ハイブリッド検索、ベクトル検索、全文検索の結果比較について**

## **サンプル画像の英語テキストと日本語への翻訳結果**

* The dog eats bananas. \-\> 犬はバナナを食べます。  
* Monkeys like bananas. \-\> サルはバナナが好きです。  
* The cat eats fishes. \-\> 猫は魚を食べます。  
* My rabbit eats carrots. \-\> 私のウサギはニンジンを食べます。  
* Go Away, Wolf\! \-\> 行け、オオカミ\!  
* The dog is running now. \-\> 犬は今走っています。  
* Birds are flying in the sky. \-\> 鳥が空を飛んでいます。  
* A fox runs very fast. \-\> キツネはとても速く走ります。  
* The cat runs very slowly. \-\> 猫はとてもゆっくり走ります。  
* The horse jumps high. \-\> 馬は高くジャンプします。  
* The cat is sleeping now. \-\> 猫は今寝ています。  
* Dogs love to play fetch. \-\> 犬は取ってこい遊びが大好きです。  
* Fish swim in the pond. \-\> 魚が池で泳いでいます。  
* The lion roars loudly. \-\> ライオンは大きな声で吠えます。  
* Owls hoot at night. \-\> フクロウは夜に鳴きます。  
* The dog eats dog food. \-\> その犬はドッグフードを食べます。  
* Catfish swim in the pond. \-\> ナマズが池で泳ぐ。

## **検索シナリオ（例）**

以下の表は、検索キーワードの入力例と、それぞれの検索モードでどう振る舞うかを示します。

| 検索キーワード | 検索モード | ヒットする例 | 解説 |
| :---- | :---- | :---- | :---- |
| バナナ | 全文検索 | 「The dog eats bananas」「Monkeys like bananas」 | キーワード「バナナ」が翻訳文に完全に含まれているため両方ヒットします。 |
| banana | ベクトル検索 | 上記2件＋その他果物系（意味的に類似） | 翻訳文に"banana"とは書かれていなくても、意味的に近い文（例: fruit/eat）もヒットする可能性があります。 |
| 果物 | ハイブリッド検索 | 上記＋"My rabbit eats carrots." など | ベクトル検索と全文検索の結果を合わせるため、意味的に近い文も補完されて表示されます。 |

## **全文検索(キーワード)でしかヒットしない例**

| 検索キーワード | 想定ヒット | 説明 |
| :---- | :---- | :---- |
| 行け、オオカミ | Go Away, Wolf\! | 完全にこの文字列を含む翻訳文がある場合のみヒットします。 |
| ニンジン | My rabbit eats carrots | 翻訳文に「ニンジン」という単語が含まれているためヒットします。 |

## **ベクトル検索で強みを発揮する検索キーワード例**

| 検索キーワード | 想定ヒット | 説明 |
| :---- | :---- | :---- |
| 動物が走る | The dog is running now / A fox runs very fast / The cat runs very slowly | 「走る」という行動の意味が近い文が、類似度の高い順にヒットします（ベクトル埋め込みベース）。 |
| ウサギが食べる | My rabbit eats carrots | キーワードが部分的にしか一致しなくても、「rabbit」と「eat」の意味的な関連性でヒットします。 |
| 魚 | The cat eats fishes / Catfish swim in the pond | 翻訳文に「魚」という単語がなくても、原文の"Fish"や"Catfish"から生成されたベクトルが類似しているためヒットする可能性があります。 |

## **シナリオの手順**

1. まだアップロードしていないサンプル画像からいくつかを選び、アプリケーションで処理してCosmos DBに登録する。  
2. 以下の検索キーワードを、それぞれの検索モードで試してみる。

| 検索キーワード | 備考 |
| :---- | :---- |
| バナナ | 全文検索とベクトル検索の違いが出やすいキーワードです。 |
| 犬が走る | 「The dog is running now」 vs 「A fox runs very fast」などでベクトルの効果を確認できます。 |
| 猫 | 「The cat is sleeping now」「The cat runs very slowly」など、猫に関連する文がどこまで拾われるかで各モードの差が見えます。 |
| 走る | 意味検索では「fox」「dog」「cat」の文がヒットしますが、全文検索ではヒットしにくい例です。 |

