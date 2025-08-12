SageMaker **Serverless Inference** のコールドスタート時間は、AWS の公式情報と実測報告を合わせると、だいたい以下の傾向です。

---

### **1. コールドスタートが発生する条件**

* 直近 **数分〜数時間** リクエストが無かった場合
* 新しいバージョンのエンドポイントをデプロイした直後
* モデルが初めてロードされるとき

---

### **2. 所要時間の目安**

* **軽量モデル（数MB〜数百MB）**
  → 約 **300〜1000ms**（0.3〜1秒）
* **中〜大型モデル（1〜2GB程度）**
  → 約 **2〜5秒**
* **非常に大きいモデル（>5GB）**
  → 10秒以上かかるケースあり

※ モデルサイズと依存ライブラリの初期化処理時間に大きく依存します。
※ 推論コンテナのビルド・初期化が含まれるため、同じモデルでも初回アクセス時が最も遅いです。

---

### **3. ウォームスタート時**

* 直前にアクセスがあれば、
  → **100〜300ms 程度**でレスポンスされることが多いです。

---

### **4. コールドスタート対策**

* 定期的にダミーリクエストを送ってウォーム状態を維持（CloudWatch Events / Lambda などで可能）
* モデルサイズを小さくする（不要なファイル削除、FP16 変換など）
* 起動時の初期化処理を最小限にする（不要なロードを削る）

---

もし希望があれば、この**Serverless Inference の Python デプロイ例**と、
**コールドスタートを最小化する設定サンプル**をまとめて作れます。

では、**SageMaker Serverless Inference** を使ったデプロイ例と、
**コールドスタートを最小化するための工夫**をセットでまとめます。

---

## 1. Python デプロイ例（Serverless Inference）

```python
import sagemaker
from sagemaker.model import Model

# SageMaker セッションとロール
sess = sagemaker.Session()
role = sagemaker.get_execution_role()

# S3 にアップロード済みのモデルファイル
model_artifact = "s3://your-bucket-name/path/to/model.tar.gz"

# 推論用 Docker イメージ URI（例：PyTorch）
image_uri = sagemaker.image_uris.retrieve(
    framework="pytorch",
    region=sess.boto_region_name,
    version="1.13",     # 適切なバージョン
    image_scope="inference"
)

# モデルオブジェクト作成
model = Model(
    image_uri=image_uri,
    model_data=model_artifact,
    role=role,
    sagemaker_session=sess
)

# サーバーレス設定
serverless_config = {
    "memory_size_in_mb": 2048,  # 1024, 2048, 4096 のみ
    "max_concurrency": 5        # 同時リクエスト数の上限
}

# Serverless エンドポイントとしてデプロイ
predictor = model.deploy(
    endpoint_name="my-serverless-endpoint",
    serverless_inference_config=serverless_config
)

# 推論リクエスト送信例
response = predictor.predict({"inputs": "Hello, SageMaker!"})
print(response)
```

---

## 2. コールドスタート最小化の工夫

| 対策               | 内容                                       |
| ---------------- | ---------------------------------------- |
| **モデルサイズ削減**     | モデル圧縮（FP16変換、不要ファイル削除）でロード時間を短縮          |
| **依存軽量化**        | 推論に不要なライブラリや初期化コードを削除                    |
| **ウォームアップリクエスト** | CloudWatch Event + Lambda で数分ごとにダミー推論    |
| **メモリ割当増加**      | `memory_size_in_mb` を大きくするとロードが高速化する場合あり |
| **初期化コード最適化**    | 推論関数外で不要な処理を実行しない（lazy load）             |

---

## 3. Lambda でウォームアップする例（擬似コード）

```python
import boto3
import json

runtime = boto3.client("sagemaker-runtime")

def lambda_handler(event, context):
    response = runtime.invoke_endpoint(
        EndpointName="my-serverless-endpoint",
        ContentType="application/json",
        Body=json.dumps({"inputs": "warmup"})
    )
    return {"statusCode": 200, "body": "Warmup request sent"}
```

* この Lambda を **5分おき** に CloudWatch Event で実行すれば、
  ほぼウォーム状態を維持でき、コールドスタート時間を回避できます。

---

これ、実際に**サーバーレス**でやると、
オンデマンド料金で**アクセスが少ない場合はコストが激減**しますが、
コールドスタートを避けたい場合は結局ウォームアップの運用コストが増える、というトレードオフがあります。

---

## SageMaker Serverless InferenceにリクエストがなくOFFになるまでかかる時間

SageMaker Serverless Inference のエンドポイントは、
最後のリクエストからしばらく経つと自動的にコンテナを停止して **OFF（スケールダウン）** します。

AWS は公式に「正確な時間は保証しない」としていますが、実測と AWS エンジニアの回答をまとめるとこんな感じです。

---

### **アイドル状態から OFF になるまでの目安**

* **だいたい 5〜15分** リクエストが無いとスケールダウン
* その間はウォーム状態が維持されるため、再アクセス時はコールドスタートなし
* 時間はモデルサイズや AWS 内部のリソース状況によって変動

---

### **コールドスタートのトリガー**

1. **アイドル時間が一定以上（5〜15分）経過**
2. **新しいエンドポイントをデプロイ**
3. **別リージョンや別アベイラビリティゾーンに移動**

---

### **参考**

* 小〜中サイズモデル（<500MB）：ほぼ 5〜10分で停止
* 大型モデル（>2GB）：15分くらい持つことが多い（内部キャッシュ戦略の影響）

---

もし望めば、この「5分おきウォームアップ」スケジューラーを CloudWatch + Lambda で構築するコードも作れます。
そうするとほぼコールドスタート無しで運用できます。
