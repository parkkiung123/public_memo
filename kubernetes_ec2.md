はい。ここは \*\*「EC2のIPをYAMLに書く必要があるのか」\*\*を実際の例で見ると分かりやすいです。

 前提をこうします。

```
EC2 #1
Public IP : 123.123.123.123
Private IP: 172.168.0.5

EC2 #2
Public IP : 123.123.123.124
Private IP: 172.168.0.6
```

 そして、

 - EC2 #1 → Kubernetes Control Plane
- EC2 #2 → Kubernetes Worker
- nginx → 4 Pod
- EC2 #1/#2に2 Podずつ配置
- 外部からNodePort `30080` でアクセス

 とします。

 ## 1\. まずEC2 #1でクラスタを作る

 EC2 #1で、

```
sudo kubeadm init --apiserver-advertise-address=172.168.0.5
```

 とします。

 ここで `172.168.0.5` が登場します。

 これは**Kubernetes API ServerがEC2 #1のどのIPで待ち受けるか**を指定しています。

 その後表示される、

```
kubeadm join 172.168.0.5:6443 --token xxxxx ...
```

 のようなコマンドをEC2 #2で実行します。

 つまり、

```
EC2 #1                         EC2 #2
172.168.0.5                    172.168.0.6
     │                              │
     │◄──── Kubernetes API ─────────│
     │       :6443                  │
     │                              │
 Control Plane                 Worker
```

 という関係になります。

---

 # 2\. nginxのDeployment YAML

 ここでは**EC2のIPは書きません**。

```
apiVersion: apps/v1
kind: Deployment

metadata:
  name: nginx

spec:
  replicas: 4

  selector:
    matchLabels:
      app: nginx

  template:
    metadata:
      labels:
        app: nginx

    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels:
                    app: nginx

      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
```

 EC2 #1で、

```
kubectl apply -f nginx.yaml
```

 と実行します。

 するとKubernetesが、

```
EC2 #1                         EC2 #2
172.168.0.5                    172.168.0.6
┌───────────────┐              ┌───────────────┐
│ Control Plane │              │ Worker        │
│               │              │               │
│ nginx Pod     │              │ nginx Pod     │
│ nginx Pod     │              │ nginx Pod     │
│               │              │ nginx Pod     │
└───────────────┘              └───────────────┘
```

 のように配置します。

 ただし、先ほどのYAMLの `preferredDuringScheduling...` は\*\*「なるべく分散する」\*\*という指定なので、厳密な2個ずつを保証するものではありません。

---

 # 3\. Service YAML

 次に、

```
apiVersion: v1
kind: Service

metadata:
  name: nginx

spec:
  type: NodePort

  selector:
    app: nginx

  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

 これを、

```
kubectl apply -f nginx-service.yaml
```

 します。

 するとNodePort `30080` が各Nodeの入口になります。

```
                       Internet
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
  123.123.123.123:30080       123.123.123.124:30080
        EC2 #1                      EC2 #2
             │                           │
             └──────────┬────────────────┘
                        │
                    Service
                     nginx
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼ ...
           Pod #1     Pod #2     Pod #3     Pod #4
```

 例えばブラウザから、

```
http://123.123.123.123:30080
```

 とアクセスできます。

 **EC2 #1に入ったからといって、必ずEC2 #1上のnginx Podに行くわけではありません。**

 ServiceがバックエンドのPodへ振り分けます。

---

 # 4\. ではYAMLの中にIPが出てくるのはどこ？

 今回の構成では、基本的にこうです。

 | 場所 | IP |
| --- | --- |
| `kubeadm init` | `172.168.0.5` |
| `kubeadm join` | `172.168.0.5:6443` |
| Deployment | **書かない** |
| Service | **書かない** |
| Pod | Kubernetesが割り当てる |
| 外部アクセス | `123.123.123.123:30080` など |

 つまり、

```
EC2のIP
   ↓
Kubernetesクラスタを作るときには必要
   ↓
Deploymentでは基本不要
   ↓
Serviceでも基本不要
   ↓
外部クライアントがアクセスするときにPublic IPを使う
```

 という感じです。

 ### なお1点だけ

 `123.123.123.123` や `172.168.0.5` は説明用の値ですよね。実際のAWS VPCでは通常 `172.16.0.0/12`、`192.168.0.0/16`、`10.0.0.0/8` などのプライベートアドレスを使います。もし実際に構築するなら、**EC2 #1/#2のSecurity GroupでTCP 6443、30080、ノード間通信などをどう開けるか**も重要になります。