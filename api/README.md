## 開発環境構築

### Docker コンテナの立ち上げ

以下のコマンドで API サーバー用のコンテナと MongoDB 用のコンテナが立ち上がる。

```
make
```

`http://localhost:8080`を叩いて、`{"message":"Hello, World!"}`を表示されれば OK

### MongoDB 用の GUI

https://www.mongodb.com/try/download/compass にて、MongoDB Compass をダウンロード。<br>
接続文字列は、`mongodb://root:password@localhost:27017/`

## ジョブ

ジョブ用のコンテナを立ち上げる。

```
make exec-job
```

ジョブ用のコンテナに入った状態で、./src/job 配下の python ファイルを実行する。

例えば、`index_blob.py`を実行するには、以下のコマンドを実行する。

```
python ./job/index_blob.py
```

## DB マイグレーション

本アプリケーションはマイグレーション機能を装備している。
以下の機能をサポートする。

- マイグレーションファイルの作成
  - DB 実体からの差分作成
  - スナップショット（後述）からの差分作成
- マイグレーションの実行
  - 未実行のマイグレーションファイル実行
  - 過去のマイグレーションファイル実行
- ~~データバックアップ~~
- ~~バックアップからデータリストア~~

スナップショットとは、マイグレーション初期化時とマイグレーション実行後に自動で作成される JSON 形式のモデルを状態を記録したファイルである。

マイグレーションに係るファイルは、
`src`配下の`migrations`ディレクトリに格納される。
`migrations`ディレクトリには、

- `backup`ディレクトリ
  - バックアップファイル
- `migration_scripts`ディレクトリ
- `snapshot`ディレクトリ
  がある。

### 使いかた

これからマイグレーションシステムを使用する場合は、初回のみ初期化コマンドを実行すること。

```
python ./job/migration.py init
```

#### 基本

```
python ./job/migration.py <<実行コマンド>> <<コマンドライン引数>>
```

#### マイグレーションファイル作成

##### スナップショットから

```
python ./job/migration.py makemigrations
```

デフォルトではスナップショットとの差分を作成する。コマンドライン引数`--from snapshot`と同様の処理をする。

##### DB 実体から

```
python ./job/migration.py makemigrations --source entity
```

コマンドライン引数で`entity`を指定すると、DB の実体との差分を作成する。

どちらも実行すると、マイグレーションの名前を聞かれるので、わかりやすい名前を設定する。（省略可）

```
python ./job/migration.py makemigrations --source snapshot
***
差分サマリ
***
マイグレーション名（省略可）:
```

処理が終わると`20241124135706_migrate_chat_messages.py`のようなファイルが`migrate_scripts`配下に作成される。
タイムスタンプ+マイグレーション名となる。

#### マイグレーション実行

```
python ./job/migration.py migrate
```

未実行のマイグレーションが実行される。コマンドライン引数`--source snapshot`と同様の処理をする。

##### 過去の DB の状態に戻す

マイグレーションファイル名をコマンドライン引数に渡すことによって、そのマイグレーションが完了した DB のスキーマにする。

例

```
python ./job/migration.py migrate --target 20241124135706_migrate_chat_messages
```

#### dryrun

`makemigations`コマンドと`migrate`コマンドには`--dryrun`オプションが使用できる。これを使用すると実際に処理はされず、処理内容を確認することができる。

## RAG の評価方法

[src/evaluation/methods.py](https://github.com/Raiku-Setoyama/jmu-rag-chatbot/blob/main/api/src/evaluation/methods.py)に RAG を評価するための関数を定義されている。それを使うための例が、[src/evaluation/example.py](https://github.com/Raiku-Setoyama/jmu-rag-chatbot/blob/main/api/src/evaluation/example.py)においてある。想定されるデータ形式は、[src/evaluation/evaluation_data.schema.json](https://github.com/Raiku-Setoyama/jmu-rag-chatbot/blob/main/api/src/evaluation/evaluation_data.schema.json)に記載されている。さらに、想定されるデータ形式の例は、[src/evaluation/sample\_{1,2,3}.json](https://github.com/Raiku-Setoyama/jmu-rag-chatbot/blob/main/api/src/evaluation/sample_1.json)に記載されている。すべての評価を実行するには、`run_evaluation()`を適切なデータを引数として渡して実行する。

### RAG の評価メトリクス

現在採用している RAG の評価メトリクスを以下に示す。

- Precision@k
  - 上位 K 件に検索されたドキュメントの中で、関連性のあるドキュメントがどれだけ含まれているかを表す。
  - この指標が高いほど、生成部分に対してより有用な情報が提供されることになる。
- Recall@k
  - 上位 K 件に検索されたドキュメントの中で、どれだけ取りこぼしなく検索されているかを表す。
  - この指標が高いほど、モデルが必要な情報を見逃すことが少なくなり、生成される応答がより正確で完全なものになる。
- Mean Reciprocal Rank (MRR)
  - 関連するドキュメントがどれだけ早くリストに表示されるかを測定する値。
  - RAG では、上位に表示されたドキュメントが生成部分に強く影響を与え、関連するドキュメントがリストの上位にあるほど、MRR が高くなる。

### RAG の評価手法の追加方針

1. `src/evaluation/methods.py`に新しく関数を定義して、必要な処理を書く。
2. `run_evaluation()`で、新しく作成した関数を実行し、標準出力に出力する。
