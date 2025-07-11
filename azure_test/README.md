# Azure Functions タイムスケジュールと関数名の設定方法

Azure FunctionsでTimer Triggerを使い、関数名やスケジュールを指定する具体的なコード例を示します。

---

## 1. 関数名の指定

関数名は`@app.function_name`デコレーターで指定します。  
この名前がAzure Functions上での関数の識別子になります。

```python
import azure.functions as func
import logging

app = func.FunctionApp()

@app.function_name(name="MyTimerFunction")
@app.schedule(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=True, use_monitor=True)
def my_timer_function(mytimer: func.TimerRequest) -> None:
    logging.info("MyTimerFunction executed.")
```

---

## 2. タイムスケジュールの指定

`schedule`パラメータにはCRON形式の文字列を指定します。  
Azure FunctionsのTimer Triggerは6フィールドのCRONを使います。

| フィールド | 意味               | 例                   |
|------------|--------------------|----------------------|
| 秒         | 0-59               | 0                    |
| 分         | 0-59               | */5 （5分ごと）       |
| 時         | 0-23               | * （毎時）            |
| 日         | 1-31               | * （毎日）            |
| 月         | 1-12               | * （毎月）            |
| 曜日       | 0-6 (日曜=0)       | * （毎週）            |

### 例

- 毎5分実行  
  `"0 */5 * * * *"`

- 毎日午前3時に実行  
  `"0 0 3 * * *"`

- 毎週月曜午前9時に実行  
  `"0 0 9 * * 1"`

---

## 3. 完全なコード例

```python
import azure.functions as func
import logging

app = func.FunctionApp()

@app.function_name(name="MyTimerFunction")
@app.schedule(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=True, use_monitor=True)
def my_timer_function(mytimer: func.TimerRequest) -> None:
    logging.info("MyTimerFunction executed.")
    print("Hello from MyTimerFunction!")
```

---

## 4. 注意点

- `run_on_startup=True`を指定すると、関数アプリ起動時に即時実行されます。  
- `use_monitor=True`はスケジュールの状態を監視し、複数インスタンスでの重複実行を防ぎます。  
- 関数名はAzureポータルやログで表示される名前になるため、わかりやすい名前を付けましょう。

---

この方法で関数名とタイムスケジュールを設定し、Azure FunctionsのTimer Triggerを管理できます。