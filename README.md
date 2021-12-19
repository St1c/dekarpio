### Docker intro

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### To run migrations

```bash
docker-compose exec api npm run db-migrate:up
```


### Running appilications

The app should be accessible via: http://localhost:8080

The API is accessible via http://localhost:8080/api

Auth requests as HTTP POST to http://localhost:8080/api/auth/login with x-www-form-urlencoded body with email and password body