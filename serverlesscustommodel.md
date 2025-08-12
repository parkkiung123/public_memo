はい、できます。
SageMaker Serverless Inference では **S3 の model.tar.gz を使わず**、
あらかじめモデルファイルを **Docker イメージにバンドル**して ECR にプッシュし、そのイメージを直接デプロイできます。

以下に、**Docker にモデル同梱 → ECR プッシュ → Serverless デプロイ**の流れをまとめます。

---

## 1. 推論用ディレクトリ構造

```
my-inference-container/
│
├── Dockerfile
├── inference.py        # 推論ロジック
└── model/              # モデルファイル（同梱する）
    └── my_model.pt
```

---

## 2. Dockerfile 例（PyTorch ベース）

```dockerfile
FROM python:3.10-slim

# 必要なライブラリをインストール
RUN pip install --no-cache-dir torch==2.1.0 transformers==4.39.0 sagemaker-inference

# モデルファイルと推論スクリプトをコピー
COPY model/ /opt/ml/model/
COPY inference.py /opt/ml/code/inference.py

# 推論用エントリポイント
ENV SAGEMAKER_PROGRAM inference.py
ENV SAGEMAKER_SUBMIT_DIRECTORY /opt/ml/code
ENV PYTHONUNBUFFERED=TRUE

WORKDIR /opt/ml/code
```

---

## 3. inference.py（最小例）

```python
import torch
import json

def model_fn(model_dir):
    # Docker イメージ内のモデルパスからロード
    model_path = f"{model_dir}/my_model.pt"
    model = torch.load(model_path, map_location="cpu")
    model.eval()
    return model

def predict_fn(input_data, model):
    # 例: 入力をテンソルに変換して推論
    inputs = torch.tensor(input_data["inputs"])
    with torch.no_grad():
        output = model(inputs)
    return output.tolist()

def input_fn(request_body, request_content_type):
    return json.loads(request_body)

def output_fn(prediction, content_type):
    return json.dumps({"result": prediction})
```

---

## 4. ECR にプッシュ

```bash
# ECR リポジトリ作成
aws ecr create-repository --repository-name my-serverless-model

# 認証
aws ecr get-login-password --region ap-northeast-1 \
| docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-northeast-1.amazonaws.com

# ビルド & プッシュ
docker build -t my-serverless-model .
docker tag my-serverless-model:latest <account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/my-serverless-model:latest
docker push <account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/my-serverless-model:latest
```

---

## 5. SageMaker Serverless エンドポイント作成（Python SDK）

```python
import sagemaker
from sagemaker.model import Model

sess = sagemaker.Session()
role = sagemaker.get_execution_role()

image_uri = "<account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/my-serverless-model:latest"

# S3 モデル URI は不要（Docker に同梱済みなので None）
model = Model(
    image_uri=image_uri,
    model_data=None,
    role=role,
    sagemaker_session=sess
)

serverless_config = {
    "memory_size_in_mb": 2048,
    "max_concurrency": 5
}

predictor = model.deploy(
    endpoint_name="serverless-docker-model",
    serverless_inference_config=serverless_config
)

# 推論呼び出し例
result = predictor.predict({"inputs": [1.0, 2.0, 3.0]})
print(result)
```

---

## ポイント

* `model_data=None` にすることで S3 の model.tar.gz を使わず、ECR イメージだけでデプロイできます。
* モデルは `/opt/ml/model/` に入れておけば `model_fn()` でロード可能。
* Serverless Inference でも Docker イメージを直接使えるため、コールドスタート時間はモデルサイズ＋依存パッケージ分だけになります（S3 ダウンロードが不要なので高速化）。

---

もし希望なら、
この例を **完全動作する最小 PyTorch モデル入り Docker** にして zip で渡せます。
そうすればそのままビルド→ECR→Serverless デプロイが可能になります。
