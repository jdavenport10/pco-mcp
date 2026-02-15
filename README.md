# Planning Center Online MCP Server

An MCP server that integrates with the Planning Center Online (PCO) API, enabling LLMs to query and manage PCO data through natural language. Runs as a shared HTTP server with per-user OAuth authentication.

## Features

- **OAuth Authentication**: Users sign in with their own PCO account — no shared service account
- **Full CRUD Operations**: Create, read, update, and delete service types, plans, plan items, plan times, and team members
- **Schedule Management**: View, accept, and decline schedule assignments
- **Song & Tag Management**: Search, create, and tag songs; manage arrangements and keys
- **Docker Deployment**: Single-command deployment for NAS or local network hosting

## Available Tools

| Category | Operations |
|---|---|
| **Service Types** | get, create, update, delete |
| **Plans** | get, create, update, delete |
| **Plan Times** | get, create, update, delete |
| **Plan Items** | get, create, update, delete, reorder |
| **Team Members** | get, assign, update, remove |
| **Schedules** | get, accept, decline |
| **Songs** | get, find, create |
| **Arrangements** | get all, get specific, get keys |
| **Tags** | assign to song, find songs by tags |

## Getting Started

### Prerequisites

- A [Planning Center Online](https://www.planningcenter.com/) account with API access
- A registered PCO OAuth application at https://api.planningcenteronline.com/oauth/applications
  - Set the callback URL to `http://your-server:8000/auth/callback`
  - Request scopes: `services`, `people`
- Docker (for deployment) or Python 3.12+

### Configuration

Copy `.env.example` to `.env` and fill in your values:

```
PCO_CLIENT_ID=your_pco_oauth_client_id
PCO_CLIENT_SECRET=your_pco_oauth_client_secret
BASE_URL=http://your-server-ip:8000
JWT_SIGNING_KEY=generate-a-random-secret-here
```

### Running with Docker

```bash
docker compose up --build
```

The server starts on port 8000.

### Running without Docker

```bash
pip install -r requirements.txt
python services.py
```

### Connecting an MCP Client

Point your MCP client (Claude Desktop, Cursor, etc.) at the server's HTTP endpoint:

```
http://your-server-ip:8000/mcp/
```

On first connection, the OAuth flow will redirect you to PCO to sign in and authorize access.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the [MIT License](LICENSE).

## Resources

- [Planning Center API Documentation](https://developer.planningcenteronline.com/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [pypco](https://github.com/billdeitrick/pypco)
