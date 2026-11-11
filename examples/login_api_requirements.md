# Login API

1. `POST /api/v1/auth/login` with `{ "email": string, "password": string }` returns `200` and
   `{ "accessToken": string, "expiresIn": 3600 }` for valid credentials.
2. A wrong password returns `401` with `{ "error": "INVALID_CREDENTIALS" }`.
3. `POST /api/v1/auth/logout` with `Authorization: Bearer <token>` returns `204`;
   the same token is rejected with `401` afterwards.
