# E-Commerce Platform with Advanced Forecasting

A comprehensive e-commerce platform built with Django REST Framework, featuring advanced sales forecasting, inventory management, and real-time analytics.

## Features

### Core E-Commerce Features
- User Authentication and Authorization
- Product Management
- Shopping Cart
- Order Processing
- Payment Integration
- Customer Support System
- Search and Filtering
- Reviews and Ratings

### Advanced Forecasting System
- Sales Prediction using Multiple Algorithms
  - Exponential Smoothing
  - ARIMA Models
  - Prophet
  - Machine Learning Models
- Automated Model Selection
- Confidence Intervals
- Seasonality Detection
- Anomaly Detection

### Inventory Management
- Real-time Stock Tracking
- Automated Reorder Points
- Multi-warehouse Support
- Stock Movement History
- Low Stock Alerts

### Analytics and Monitoring
- Sales Performance Metrics
- Customer Behavior Analysis
- Product Performance Tracking
- Forecast Accuracy Monitoring
- Real-time Dashboards

### Technical Features
- RESTful API Architecture
- Real-time Updates using Channels
- Celery Task Queue for Background Jobs
- Redis Caching
- Comprehensive Test Coverage
- API Documentation with Swagger/OpenAPI

## Installation

1. Clone the repository:
```bash
cd api-ecommrace
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/register/`: Register new user
- `POST /api/auth/login/`: Login user
- `POST /api/auth/refresh/`: Refresh JWT token

### Products
- `GET /api/products/`: List all products
- `POST /api/products/`: Create new product
- `GET /api/products/{id}/`: Get product details
- `PUT /api/products/{id}/`: Update product
- `DELETE /api/products/{id}/`: Delete product

### Orders
- `GET /api/orders/`: List user orders
- `POST /api/orders/`: Create new order
- `GET /api/orders/{id}/`: Get order details
- `PUT /api/orders/{id}/`: Update order status

### Forecasting
- `GET /api/forecasting/forecast/{product_id}/{warehouse_id}/`: Generate forecast
- `GET /api/forecasting/monitor/`: Get forecast monitoring summary
- `GET /api/forecasting/accuracy/`: Get forecast accuracy metrics
- `GET /api/forecasting/anomalies/`: Detect sales anomalies

### Analytics
- `GET /api/analytics/sales/`: Get sales analytics
- `GET /api/analytics/customers/`: Get customer analytics
- `GET /api/analytics/products/`: Get product analytics

## Environment Variables

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Architecture

The application follows a modular architecture with the following main components:

1. **Core Apps**
   - Account Management
   - Product Management
   - Order Processing
   - Payment Processing

2. **Advanced Features**
   - Forecasting System
   - Analytics Engine
   - Monitoring System
   - Notification Service

3. **Infrastructure**
   - Redis Cache
   - Celery Workers
   - WebSocket Channels
   - Database

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=.
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django REST Framework
- Facebook Prophet
- scikit-learn
- Redis
- Celery
- And all other open-source libraries used in this project

## Support

For support, email support@yourdomain.com or open an issue in the GitHub repository.
