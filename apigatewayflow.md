了解です。では、ご提示の内容をMarkdown形式で整理して見やすくまとめ直しました。

---

# WebSocket × Lambda × SageMakerによるリアルタイム画像処理フロー

## 全体構成図

```
クライアント（ブラウザ）
    ── JPEG画像フレーム(10fps) ──▶ API Gateway WebSocket API（Route: sendFrame）
                                     └─▶ Lambda（受信処理）
                                          └─▶ SageMaker エンドポイントへ推論依頼（InvokeEndpoint API）
                                                └─▶ 推論結果（画像など）をLambdaで受信
                                                      └─▶ API Gateway WebSocket経由でクライアントへ返送
```

---

## 1. クライアント側の概要

* `MediaRecorder` や `canvas.toBlob` を用いて 10fps でJPEG画像フレームを生成
* WebSocketでフレームデータ（Base64 またはバイナリ）を送信
* 推論結果（加工済み画像など）を受信し、`<canvas>` または `<img>` に描画

---

## 2. Lambda側サンプルコード（Node.js）

```javascript
const AWS = require("aws-sdk");
const sagemakerRuntime = new AWS.SageMakerRuntime();

exports.handler = async (event) => {
  const routeKey = event.requestContext.routeKey;
  const connectionId = event.requestContext.connectionId;

  if (routeKey === "sendFrame") {
    // クライアントからの画像フレーム受信
    let frameData;
    if (event.isBase64Encoded) {
      frameData = Buffer.from(event.body, "base64");
    } else {
      frameData = Buffer.from(event.body, "utf8"); // テキストの場合
    }

    const params = {
      EndpointName: "YOUR_SAGEMAKER_ENDPOINT_NAME",
      ContentType: "image/jpeg",
      Body: frameData,
    };

    try {
      // SageMakerへ推論依頼
      const response = await sagemakerRuntime.invokeEndpoint(params).promise();
      const resultBuffer = response.Body;

      // クライアントへ返送
      const apiGateway = new AWS.ApiGatewayManagementApi({
        endpoint: `${event.requestContext.domainName}/${event.requestContext.stage}`,
      });

      await apiGateway.postToConnection({
        ConnectionId: connectionId,
        Data: resultBuffer,
      }).promise();

      return { statusCode: 200 };

    } catch (err) {
      console.error("Error in SageMaker or WebSocket send:", err);
      return { statusCode: 500, body: "Internal Server Error" };
    }
  }

  if (routeKey === "$connect" || routeKey === "$disconnect") {
    return { statusCode: 200 };
  }

  return { statusCode: 400, body: "Invalid route" };
};
```

---

## 3. 実装ポイント

* **ルーティング**
  `sendFrame` ルートでクライアントからのJPEGフレームを受け取り処理する
* **データ形式**
  JPEGフレームはBase64またはバイナリ形式で送信想定
* **SageMaker呼び出し**
  `ContentType` は `"image/jpeg"` を指定
* **レスポンス返却**
  SageMakerの推論結果（Buffer）をそのままクライアントへバイナリで返す
* **タイムアウト設定**
  推論遅延を考慮し、Lambdaのタイムアウトは少なくとも1秒以上推奨
* **ペイロード制限**
  API Gateway WebSocketの最大ペイロードは128KB（2025年8月時点）なのでフレームサイズに注意

---

## 4. クライアント側受信処理例（JavaScript）

```javascript
ws.binaryType = "arraybuffer";

ws.onmessage = (event) => {
  const arrayBuffer = event.data;
  const blob = new Blob([arrayBuffer], { type: "image/jpeg" });
  const url = URL.createObjectURL(blob);

  const img = document.getElementById("processedImage");
  img.src = url;

  // 古いURLの解放
  if (img._lastUrl) URL.revokeObjectURL(img._lastUrl);
  img._lastUrl = url;
};
```

---

## 5. 高負荷・遅延対策

* **フレームサイズの削減**
  解像度・画質の低下でペイロード削減
* **モデルの軽量化**
  SageMakerエンドポイントのモデル最適化・スケーリング
* **並列処理**
  複数Lambdaによる処理分散

---

この構成であれば、Webブラウザから送信された画像フレームをほぼリアルタイムで推論処理し、結果を即座に返すことが可能です。

---

もし希望があれば、このまま**API Gateway WebSocketの設定例**と**SageMakerエンドポイント準備のポイント**もMarkdownで追記できますが、続けますか？


## 本格構成例 (webrtc+KVS)
https://github.com/aws-samples/python-samples-for-amazon-kinesis-video-streams-with-webrtc/tree/main