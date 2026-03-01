# Server Management API

A RESTful API built with FastAPI for managing servers across multiple datacenters

## Features

- Create, read, update, and delete servers
- Manage server configurations as JSON
- Link servers to datacenters
- Comprehensive API documentation with Swagger UI
- Health check endpoint

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/krasnoshchok/server-management-api.git
cd server-management-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL database

Create a new database:

```bash
createdb server_management
```

### 5. Apply database schema

Run the SQL schema file to create tables:

```bash
psql server_management < sql/schema.sql
```

This will create the following tables:
- `datacenter` - Stores datacenter information
- `switch` - Network switch information
- `server` - Server inventory
- `switch_to_server` - Many-to-many relationship between switches and servers

The schema file also includes sample data for testing.

### 6. Configure environment variables

Create a `.env` file in the project root:

```env
# Database
DB_HOST=localhost
DB_NAME=server_management
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432


# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Docker Deployment

A Dockerfile and `docker-compose.yml` (now located in the `docker/` subdirectory) are provided to containerize the service and a PostgreSQL instance.

## Kubernetes / Minikube (local cluster)

If you prefer to run the application on a local Kubernetes cluster you can
use [minikube](https://minikube.sigs.k8s.io/).

### Installing minikube on macOS (M1/Apple Silicon)

1. Install dependencies via Homebrew:
   ```bash
   brew install hyperkit docker
   brew install minikube
   ```
   *`docker` is used as the driver by default; hyperkit is optional.*

2. Start the cluster using the Docker driver:
   ```bash
   minikube start --driver=docker
   ```

3. (Optional) Enable addons such as the dashboard or ingress:
   ```bash
   minikube addons enable dashboard
   minikube addons enable ingress
   ```

### Building the image inside minikube

```bash
# point your shell at minikube's Docker daemon
eval $(minikube docker-env)

docker build -t server-management-api:latest .
# you can now undo the env change with "eval $(minikube docker-env -u)"
```

Alternatively use the built-in helper:

```bash
minikube image build -t server-management-api:latest .
```

### Applying Kubernetes manifests

Manifests live in the `k8s/` directory and include the API deployment,
Postgres deployment/service, and a NodePort service for the API.

```bash
kubectl apply -f k8s/
```

The application will start and expose itself on port **30080** of the
minikube node. You can access it from the host with:

```bash
curl http://$(minikube ip):30080/health
```

or use port‑forwarding:

```bash
kubectl port-forward svc/server-api 8000:8000
```

### Initialising the database

Once the Postgres pod is ready run the schema script as before:

```bash
kubectl exec -i deploy/postgres -- \
    psql -U postgres -d server_management < sql/schema.sql
```

### Cleaning up

```bash
kubectl delete -f k8s/
minikube stop
```

The `k8s/` directory can be extended with ConfigMaps, secrets or a
`Job` to seed the database automatically.

### Build using Docker only

```bash
# Dockerfile is in docker/ so pass -f or change directory
docker build -f docker/Dockerfile -t server-management-api .
```

Run the container with the database connection specified via environment variables:

```bash
# use the same network or provide a reachable Postgres
docker run -e DB_HOST=host.docker.internal \
           -e DB_NAME=server_management \
           -e DB_USER=postgres \
           -e DB_PASSWORD=your_password \
           -e DB_PORT=5432 \
           -p 8000:8000 \
           server-management-api
```

### Using Docker Compose (recommended)

```bash
# bring up both database and api; compose file is in docker/
# from project root:
docker-compose -f docker/docker-compose.yml up --build  # run from project root
```

- API available at `http://localhost:8000`
- PostgreSQL listens on `localhost:5432` with credentials shown in `docker-compose.yml`.

Logs are mounted to `./logs` so the host can inspect `app.log`.

After the database container starts you still need to create the tables. You can either run the `sql/schema.sql` from the host against `localhost:5432` or exec into the container:

```bash
# once compose is running
docker exec -i $(docker-compose ps -q db) psql -U postgres -d server_management < sql/schema.sql
```

This will populate the schema and sample data as described above.

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

- **GET** `/health` - Verify the service is running

### Server Management

- **GET** `/servers/` - Retrieve all servers
- **GET** `/servers/{server_id}` - Retrieve a specific server by ID
- **POST** `/servers/` - Create a new server
- **PUT** `/servers/{server_id}` - Update an existing server
- **DELETE** `/servers/{server_id}` - Delete a server

## Usage Examples

### Create a new server

```bash
curl -X POST "http://localhost:8000/servers/" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "webserver.local.lan",
    "configuration": {"cpu_cores": 8, "ram_gb": 32},
    "datacenter_id": 1
  }'
```

> [!IMPORTANT]
> **Resource Limits Enforced**
> The server configuration strictly enforces hardware limits. Invalid values will result in a `400 Bad Request` error.
> * `cpu_cores`: Must be between **1** and **128**
> * `ram_gb`: Must be between **1** and **4096**


### Get all servers

Get first 100 servers (default):
```bash
curl -X GET "http://localhost:8000/servers/"
```

Get first 10 servers:
```bash
curl -X GET "http://localhost:8000/servers/?limit=10"
```

Get servers 11-20 (skip first 10, return next 10):
```bash
curl -X GET "http://localhost:8000/servers/?skip=10&limit=10"
```

Get servers 101-200:
```bash
curl -X GET "http://localhost:8000/servers/?skip=100&limit=100"
```

### Get a specific server

```bash
curl -X GET "http://localhost:8000/servers/1"
```

### Update a server

```bash
curl -X PUT "http://localhost:8000/servers/1" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "updated-webserver.local.lan",
    "configuration": {"cpu_cores": 16, "ram_gb": 64}
  }'
```

### Delete a server

```bash
curl -X DELETE "http://localhost:8000/servers/1"
```

## Project Structure
```
server-management-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection management
│   ├── models.py            # Pydantic models for validation
│   ├── constants.py         # Database table constants
│   ├── logging_config.py    # Logging configuration
│   └── routers/
│       ├── __init__.py
│       └── servers.py       # Server endpoint definitions
│
├── logs/
│   └── app.log              # Application logs (gitignored)
│
├── sql/
│   └── schema.sql           # Database schema and sample data
│
├── .env                     # Environment variables (gitignored)
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Design Decisions

### Database Connection Management

- Used context managers (`@asynccontextmanager`) for automatic connection cleanup
- `RealDictCursor` returns query results as dictionaries for easier JSON serialization
- Manual transaction management (commit/rollback) for better control

### No ORM Approach

- Direct SQL queries using `asyncpg` as per requirements
- Parameterized queries to prevent SQL injection
- Dynamic query building for partial updates

### API Design

- RESTful conventions (GET, POST, PUT, DELETE)
- Proper HTTP status codes (200, 201, 204, 400, 404)
- Comprehensive error handling with descriptive messages
- Request/response validation using Pydantic models

### JSON Configuration

- Server `configuration` field stored as JSONB in PostgreSQL
- Flexible schema allows different configurations per server
- Validated as dictionary type in Pydantic models

## Error Handling

The API returns standard HTTP error codes:

- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid input or missing required fields
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server-side error

## Testing

You can test the API using:

1. **Swagger UI** at http://localhost:8000/docs (interactive testing)
2. **curl** commands (see examples above)
3. **Postman** or similar API clients
4. **Python requests library**

## Logging

The application includes comprehensive logging for monitoring and debugging.

### Log Configuration

Configure logging in your `.env` file:
```env
# Logging (optional)
LOG_LEVEL=INFO          # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log   # Leave empty to disable file logging
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems (shows all query details)
- **INFO**: General informational messages (default, recommended for production)
- **WARNING**: Warning messages for unexpected events
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause the application to stop

### Log Output

Logs are written to two locations:

1. **Console/Terminal** - All logs appear in the terminal where you run uvicorn
2. **Log File** - Persistent logs saved to `logs/app.log` (if configured)

### Viewing Logs

**View logs in real-time:**
```bash
tail -f logs/app.log
```

### Example Log Output
```
2024-05-28 15:30:52 - INFO - Fetching servers with skip=0, limit=100
2024-05-28 15:30:52 - INFO - Retrieved 3 servers
2024-05-28 15:31:10 - INFO - Creating server: hostname=newserver.local, datacenter_id=1
2024-05-28 15:31:10 - INFO - Created server with id=4, hostname=newserver.local
2024-05-28 15:31:45 - WARNING - Server with id=99 not found
```

## Important Files

The following files are ignored by git (see `.gitignore`):
- `.env` - Contains sensitive database credentials
- `logs/` - Log files can grow large and contain sensitive data
- `__pycache__/` and `*.pyc` - Python bytecode files

## Development

To run in development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes

- The API follows PEP 8 style guidelines
- All endpoints include comprehensive docstrings
- Foreign key constraints are validated before operations
- Timestamps are automatically managed by PostgreSQL
- The `modified_at` field is updated on every server update
