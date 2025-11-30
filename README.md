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
DB_HOST=localhost
DB_NAME=server_management
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432
```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

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
│   └── routers/
│       ├── __init__.py
│       └── servers.py       # Server endpoint definitions
│
├── sql/
│   └── schema.sql           # Database schema and sample data
│
├── .env                     # Environment variables (not in git)
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Design Decisions

### Database Connection Management

- Used context managers (`@contextmanager`) for automatic connection cleanup
- `RealDictCursor` returns query results as dictionaries for easier JSON serialization
- Manual transaction management (commit/rollback) for better control

### No ORM Approach

- Direct SQL queries using `psycopg2` as per requirements
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
