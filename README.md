# ServerlessJWT

Vercel 上で公開している Swagger UI は [https://jwt.ikeda042.homes/api/v1/docs](https://jwt.ikeda042.homes/api/v1/docs) から確認できる。

API のベースパスは `https://jwt.ikeda042.homes/api/v1` である。

テスト用エンドポイントは `https://jwt.ikeda042.homes/api/v1/test` 配下である。

## 利用上の注意

この API は JWT の生成・検証を試すためのデモ/ツール用途であり、実際のマイクロサービス認証基盤としてそのまま利用することは推奨しない。

本 API は `signing_key` / `verification_key` をリクエストで受け取る設計である。そのため、HS256 の共有シークレットや RS256 の秘密鍵を公開 API に渡すと、アプリケーションログ、プロキシ、APM、アクセス履歴、例外ログなどに秘密情報が残る可能性がある。

実運用では、認証サービスが JWT に署名し、各マイクロサービスが JWT をローカルで検証する構成を推奨する。特に `RS256` / `ES256` などの非対称鍵方式を使い、各サービスは公開鍵または JWKS をキャッシュして `iss`、`aud`、`exp`、`scope` などを検証する構成が望ましい。

`HS256` を使う場合でも、共有シークレットをこの API に送信せず、各サービスがシークレット管理基盤から共有シークレットを読み込んでローカル検証するべきである。中央 API で検証したい場合は、検証鍵をリクエストで渡すのではなく、認証サーバー側に保管し、サービス認証で保護された Token Introspection 風の内部 API として設計する。

本番用 JWT 発行エンドポイントは `POST https://jwt.ikeda042.homes/api/v1/token` である。
`alg` には `HS256` または `RS256` のみを指定できる。`signing_key` には、`HS256` の場合は共有シークレット、`RS256` の場合は PEM 形式の秘密鍵文字列を渡す。
`payload` を省略すると、`iss` は `https://jwt.ikeda042.home/api/v1/`、`exp` は発行時刻から 1 時間後、`user_name` は `ikeda042`、`scope` は `admin` になる。
発行した JWT は `GET https://jwt.ikeda042.homes/api/v1/token` で検証できる。`verification_key` には、`HS256` の場合は発行時と同じ共有シークレット、`RS256` の場合は PEM 形式の公開鍵文字列を渡す。

テスト用の認証情報は以下のとおりである。

- `account`: `test-user`
- `password`: `test-password`

## cURL Examples

テスト用トークンを取得する:

```bash
curl -X POST "https://jwt.ikeda042.homes/api/v1/test/token" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test-user",
    "password": "test-password"
  }'
```

取得したトークンで保護 API にアクセスする:

```bash
TOKEN="PASTE_ACCESS_TOKEN_HERE"

curl "https://jwt.ikeda042.homes/api/v1/test/protected" \
  -H "Authorization: Bearer ${TOKEN}"
```

本番用 JWT を `HS256` で生成する:

```bash
JWT=$(curl -s -X POST "https://jwt.ikeda042.homes/api/v1/token" \
  -H "Content-Type: application/json" \
  -d '{
    "alg": "HS256",
    "signing_key": "your-shared-secret"
  }' | python3 -c 'import json, sys; print(json.load(sys.stdin)["token"])')
```

本番用 JWT を `HS256` の共有シークレットで検証する:

```bash
curl -G "https://jwt.ikeda042.homes/api/v1/token" \
  --data-urlencode "token=${JWT}" \
  --data-urlencode "alg=HS256" \
  --data-urlencode "verification_key=your-shared-secret"
```
