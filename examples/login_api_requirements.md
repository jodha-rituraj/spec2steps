# Login API

1. `POST /api/v1/auth/login` accepts `{ "email": string, "password": string }`.
2. Valid credentials return `200` with `{ "accessToken": string, "expiresIn": number }`.
   `expiresIn` is 3600 seconds.
3. A wrong password returns `401` with `{ "error": "INVALID_CREDENTIALS" }`.
4. A malformed email returns `400` with `{ "error": "INVALID_EMAIL" }`.
5. A missing field returns `400` with `{ "error": "MISSING_FIELD", "field": <name> }`.
6. After 5 failed attempts within 15 minutes the account is locked and the API
   returns `423` with `{ "error": "ACCOUNT_LOCKED", "retryAfter": number }`.
7. `POST /api/v1/auth/logout` with a valid `Authorization: Bearer <token>` header
   returns `204`; the token is rejected with `401` afterwards.
