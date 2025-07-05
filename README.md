# Portfolio Management Dashboard

A comprehensive portfolio and asset management dashboard built with FastAPI (Python) backend and React/TypeScript frontend.

## Features

- **Portfolio Tracking**: Real-time portfolio valuation and performance tracking
- **Risk Analytics**: Comprehensive risk metrics including Sharpe ratio, beta, volatility, and maximum drawdown
- **Portfolio Optimization**: Modern Portfolio Theory implementation with efficient frontier visualization
- **Market Data Integration**: Live market data via Yahoo Finance API
- **Real-time Updates**: WebSocket-based live price updates
- **Data Import/Export**: CSV/Excel portfolio import and export functionality

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **yfinance**: Yahoo Finance data integration
- **PyPortfolioOpt**: Portfolio optimization algorithms
- **Empyrical**: Financial risk metrics
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **Redis**: Caching layer

### Frontend
- **React**: User interface library
- **TypeScript**: Type-safe JavaScript
- **Chart.js**: Data visualization
- **Material-UI**: Component library
- **Axios**: HTTP client

## Project Structure

```
portfolio-manager/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend Docker configuration
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   └── Dockerfile         # Frontend Docker configuration
└── docker-compose.yml     # Multi-container setup
```

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Phases

This project is being developed in phases:

1. **Phase 1**: Project Foundation & Setup ✅
2. **Phase 2**: Core Data Models & API Structure
3. **Phase 3**: Market Data Integration
4. **Phase 4**: Portfolio Data Management
5. **Phase 5**: Basic Frontend Dashboard
6. **Phase 6**: Risk Analytics Engine
7. **Phase 7**: Advanced Visualizations
8. **Phase 8**: Portfolio Optimization
9. **Phase 9**: Real-Time Features & WebSockets
10. **Phase 10**: Testing, Performance & Deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and informational purposes only. It should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions.
