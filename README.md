# NY Assembly Transcript API

A RESTful API providing access to New York State Assembly floor transcripts, member information, parsed segments, and interaction analysis.

[![Documentation](https://img.shields.io/badge/docs-read%20the%20docs-blue)]https://ny-assembly-api-docs.readthedocs.io/en/latest/)
[![API Status](https://img.shields.io/badge/API-online-success)](http://nyassembly.duckdns.org:8888)

## Live API

**Base URL**: `http://nyassembly.duckdns.org:8888`

**Demo API Key**: `drt7AfZlJqLxrVtNXBNxSd03rJzqNXkPinTDWEfn0IU`

**Documentation**: 'https://ny-assembly-api-docs.readthedocs.io/en/latest/'

## Quick Start

```python
import requests

API_KEY = "drt7AfZlJqLxrVtNXBNxSd03rJzqNXkPinTDWEfn0IU"
BASE_URL = "http://nyassembly.duckdns.org:8888"

# Get all assembly members
response = requests.get(
    f"{BASE_URL}/members",
    params={"key": API_KEY}
)

data = response.json()
print(f"Total members: {data['total']}")
```

## Features

- **Assembly Members**: Complete roster with district and session information
- **Floor Transcripts**: Full text of assembly floor proceedings  
- **Transcript Segments**: Parsed individual statements by members
- **Interaction Analysis**: Member-to-member interactions with sentiment analysis
- **Rate Limiting**: Fair usage limits (60 requests/minute)
- **Pagination**: Efficient data retrieval with offset/limit parameters

## Data Coverage

- **Sessions**: 2019-2025
- **Members**: 236+ current and former assembly members
- **Transcripts**: Complete floor proceedings
- **Interactions**: Questions, responses, acknowledgments with sentiment

## API Endpoints

| Endpoint | Description | Rate Limit |
|----------|-------------|------------|
| `GET /` | API information | 100/min |
| `GET /members` | List all members | 60/min |
| `GET /members/{id}` | Get specific member | 60/min |
| `GET /transcripts` | List transcript dates | 60/min |
| `GET /transcripts/{date}` | Get full transcript | 30/min |
| `GET /segments` | List parsed segments | 60/min |
| `GET /segments/{id}` | Get specific segment | 60/min |
| `GET /interactions` | List interactions | 60/min |
| `GET /interactions/{id}` | Get specific interaction | 60/min |

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - Database ORM
- **Psycopg2** - PostgreSQL adapter

### Infrastructure  
- **Ubuntu Server 24.04** - Operating system
- **Nginx** - Reverse proxy server
- **Systemd** - Service management
- **DuckDNS** - Dynamic DNS

### Libraries
- **SlowAPI** - Rate limiting
- **PyPDF2** - PDF text extraction
- **Requests** - HTTP client


## Deployment

### Prerequisites

- Ubuntu 24.04 LTS
- Python 3.12+
- PostgreSQL 16
- Nginx

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/DiDa-Capstone.git
cd DiDa-Capstone/API
```

2. **Set up Python environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure PostgreSQL**
```bash
sudo -u postgres psql
CREATE DATABASE assembly_data;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE assembly_data TO your_user;
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

5. **Run database migrations**
```bash
python init_db.py
```

6. **Test locally**
```bash
uvicorn main:app
```

### Production Deployment

1. **Create systemd service** (`/etc/systemd/system/assembly-api.service`):
```ini
[Unit]
Description=NY Assembly Transcript API
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
Group=your_user
WorkingDirectory=/path/to/API
Environment="PATH=/path/to/API/venv/bin"
ExecStart=/path/to/API/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Enable and start service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable assembly-api
sudo systemctl start assembly-api
```

3. **Configure Nginx** (`/etc/nginx/sites-available/assembly-api`):


4. **Enable Nginx site**
```bash
sudo ln -s /etc/nginx/sites-available/assembly-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. **Configure firewall**
```bash
sudo ufw allow 8888/tcp
```





## Security

- **API Key Authentication**: All endpoints require valid API key
- **Rate Limiting**: Prevents abuse (60 requests/minute)
- **Input Validation**: FastAPI automatic validation
- **SQL Injection Protection**: SQLAlchemy parameterized queries
- **CORS Configuration**: Allows cross-origin requests



## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

### Frameworks & Libraries
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL database integration
- [Requests](https://requests.readthedocs.io/) - HTTP library
- [PyPDF2](https://pypdf2.readthedocs.io/) - PDF text extraction
- [Psycopg](https://www.psycopg.org/) - PostgreSQL adapter
- [SlowAPI](https://slowapi.readthedocs.io/) - Rate limiting

### Infrastructure
- [DuckDNS](https://www.duckdns.org/) - Dynamic DNS service

### Data Sources
- [NY State Assembly](https://nyassembly.gov/av/session/) - Official transcripts
- [NY Senate Open Legislation API](https://legislation.nysenate.gov/static/docs/html/index.html) - API design inspiration

### Learning Resources
- "Design of Web APIs" by Arnaud Lauret - API design principles
- [GeeksforGeeks FastAPI Tutorial](https://www.geeksforgeeks.org/python/creating-first-rest-api-with-fastapi/) - Getting started

Special thanks to the New York State Assembly for providing public access to legislative transcripts.

## Contact

**Project Maintainer**: Nick Gutin

**Documentation**: _


---

**Built with love for transparent government data access**
