## 無料枠での注意点
トレーニングは不要（JumpStartの事前学習モデルを使うため）

推論エンドポイント（ml.t2.medium）は 125時間/月 無料 → 使い終わったら必ず削除

Studio アプリ（ml.t3.medium）は 250時間/月 無料 → 使い終わったら「停止」必須

EFS と S3 の無料枠（各5GB/月）を超えるとストレージ課金が発生


`ml.t3.medium` は CPUインスタンスなので **GPU不要の軽量モデル** を使うのに向いています。画像以外でもテキストや構造化データの軽い推論・トレーニングに最適です。

---

## ml.t3.mediumで無料枠内に軽く使えるおすすめモデル例

### 1. テキスト分類や感情分析（NLP系）

* **Amazon Comprehendの軽量版モデル（SageMaker JumpStartなど）**

  * 例えばシンプルなテキスト分類や感情分析モデル（BERTの小型版やDistilBERTなど）
  * 小規模データや簡単な用途ならCPUで十分動く
  * ニュース記事やレビューのポジネガ判定など

### 2. 構造化データの回帰・分類モデル

* **XGBoostやLightGBMのCPU版**

  * カスタムデータの回帰・分類タスクに使いやすい
  * SageMaker JumpStartにある「回帰モデル」や「分類モデル」の軽量版が該当
  * 例：売上予測、顧客離脱予測など

### 3. 軽量な自然言語生成（NLG）

* **小型Transformerモデル（GPT-2 Smallなど）**

  * 推論のみならCPUで使えるが処理は遅め
  * 簡単な文章生成や要約などに限定

---

## JumpStartで試しやすい例

| モデル名                             | 用途     | 備考                 |
| -------------------------------- | ------ | ------------------ |
| Text Classification - DistilBERT | テキスト分類 | 軽量版BERTで高速CPU推論可能  |
| XGBoost Regressor                | 数値回帰   | CPUで高速、構造化データ向き    |
| Text Summarization - Small GPT2  | テキスト要約 | 小型GPT2モデル、CPUでも試せる |

---

## まとめ

| 項目     | ポイント                   |
| ------ | ---------------------- |
| インスタンス | ml.t3.medium (CPU 2コア) |
| 無料枠対応  | SageMaker無料枠対象         |
| モデル    | 軽量テキスト分類・回帰モデルなど       |
| 適した用途  | テキスト分析、構造化データ分析、軽量NLG  |
| GPU不要  | CPUインスタンスで十分動作         |

---

必要なら、`ml.t3.medium` で使えるSageMaker JumpStartの軽量テキスト分類モデルのノートブックサンプルも作成します！

了解です！
`ml.t3.medium` のCPUインスタンス上で使える、SageMaker JumpStartの「Text Summarization（文章要約）」モデルを使った簡単なノートブックサンプル例を作ります。

---

# SageMaker StudioでText Summarizationモデルを動かす簡単サンプル (JumpStartモデルをCPUインスタンスにデプロイするサンプル)

```python
import sagemaker
from sagemaker.jumpstart import JumpStartModel

sess = sagemaker.Session()
role = sagemaker.get_execution_role()

model_id = "huggingface-t5-small"
model_version = "*"

model = JumpStartModel(
    model_id=model_id,
    model_version=model_version,
    role=role,
    sagemaker_session=sess,
)

# 無料枠対象のml.t2.mediumを指定してデプロイ
predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.t2.medium",
)

print(f"Endpoint name: {predictor.endpoint_name}")
```

---

# 推論実行例

```python
# 要約したいテキスト
text = """
Amazon SageMaker JumpStart は、事前にトレーニングされたモデルやソリューションテンプレートを簡単に利用できる機能です。
これにより、機械学習の初心者でもすぐにモデルをデプロイして推論が行えます。
本サービスは画像認識、自然言語処理、異常検知など幅広い用途に対応しています。
"""

# 推論リクエスト送信
response = predictor.predict({"inputs": text})

print("要約結果:")
print(response)
```

---

# 推論終了後のクリーンアップ

```python
# エンドポイント削除
predictor.delete_endpoint()
```

---

## ポイント

* `JumpStartModel`クラスでモデルを指定し、CPUインスタンス（`ml.t3.medium`）を明示的に指定できる
* この方法なら無料枠範囲内での利用も可能（条件による）
* 物体検出モデルなどGPU必須のモデルはこの方法でもCPU指定できないことが多いので注意

---

もしほかに知りたいモデルの例や応用があれば教えてください！
