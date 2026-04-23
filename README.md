# ServerlessJWT

Vercel 上で公開している Swagger UI は [https://jwt.ikeda042.homes/api/v1/docs](https://jwt.ikeda042.homes/api/v1/docs) から確認できます。

API のベースパスは `https://jwt.ikeda042.homes/api/v1` です。

テスト用の認証情報は以下です。

- `account`: `test-user`
- `password`: `test-password`

## cURL Examples

トークンを取得する:

```bash
curl -X POST "https://jwt.ikeda042.homes/api/v1/token" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test-user",
    "password": "test-password"
  }'
```

取得したトークンで保護APIにアクセスする:

```bash
TOKEN="PASTE_ACCESS_TOKEN_HERE"

curl "https://jwt.ikeda042.homes/api/v1/protected" \
  -H "Authorization: Bearer ${TOKEN}"
```
