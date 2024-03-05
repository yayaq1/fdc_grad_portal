# To run all containers:
```
docker-compose up -d
```

# To take all containers down:
```
docker-compose down
```

# To take all containers down plus volumes:
```
docker-compose down -v
```

# DB Endpoints:
```
curl -X POST \
-H "Content-Type: application/json" \
-d '{"email": "example@example.com", "password": "password123"}' \
http://localhost:6001/register

curl -X POST \
-H "Content-Type: application/json" \
-d '{"email": "example@example.com", "password": "password123"}' \
http://localhost:6001/login

curl -X GET \
-H "Authorization: Bearer <your_token_here>" \
http://localhost:6001/check_token_status
```


Zip folder contains:
- Folder named 'db_api' with Flask REST API. Config file with db credentials and JWT key. Dockerfile for the API.
- Folder named 'resources' with our sql file
- Env file with Docker Postgres credentials
- Docker-compose file for easy scaling to further services in the future and postgres/api definitions + exposure
- README file with docker commands and sample endpoint calls
- Requirements.txt file for Docker

API Specs:
- Login/Register/JWT_check endpoints
- Migration feature added for easy DB schema changes
- CORS feature added for access via React app over browser
- Rate-limiting added (20 reqs/min per ip) to prevent attacks
- Prepared statements to avoid sql injection attacks
- JWT Integrated for session management
- Flask Compress added for quick REST calls
- Hosted on PORT 6001, exposed through Docker. Running in debug mod