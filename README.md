# ServerlessJWT

Vercel 上で公開している Swagger UI は [https://jwt.ikeda042.homes/api/v1/docs](https://jwt.ikeda042.homes/api/v1/docs) から確認できる。

API のベースパスは `https://jwt.ikeda042.homes/api/v1` である。

テスト用エンドポイントは `https://jwt.ikeda042.homes/api/v1/test` 配下である。

本番用 JWT 発行エンドポイントは `POST https://jwt.ikeda042.homes/api/v1/token` である。
`alg` には `HS256` または `RS256` のみを指定できる。`signing_key` には、`HS256` の場合は共有シークレット、`RS256` の場合は PEM 形式の秘密鍵文字列を渡す。
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
    "signing_key": "your-shared-secret",
    "payload": {
      "sub": "account-123",
      "name": "example-user",
      "role": "admin"
    }
  }' | python3 -c 'import json, sys; print(json.load(sys.stdin)["token"])')
```

本番用 JWT を `HS256` の共有シークレットで検証する:

```bash
curl -G "https://jwt.ikeda042.homes/api/v1/token" \
  --data-urlencode "token=${JWT}" \
  --data-urlencode "alg=HS256" \
  --data-urlencode "verification_key=your-shared-secret"
```
