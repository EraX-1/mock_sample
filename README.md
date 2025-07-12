# このリポジトリ

プレビュー用mock環境
* web検索ボタン
* GPT作成UI

## ローカル起動方法

1. 以下の環境変数を作成
https://www.notion.so/21954d8b9bc080b0932cd0d77df66319

2. 起動
```
make setup && make up
```

## ngrok起動方法

1. （持っていない場合のみ）
```
brew install ngrok
```
2. 
```
ngrok http 3000
```