# API Quick Reference

## Base URL
```
Production: https://your-domain.com/api/
Development: http://localhost:8000/api/
```

## Interactive API Documentation

For interactive API testing and detailed documentation:
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/swagger.json`

## Authentication Header
```
Authorization: Bearer <access_token>
```

## Common Response Format
```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

## User Roles
- `SUPER_ADMIN` - Full system access
- `CENTRE_MANAGER` - Centre-level access
- `TEACHER` - Class-level access
- `STUDENT` - Personal data access
- `PARENT` - Linked student access

## Quick Start Examples

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "TEACHER"
  }
}
```

### 2. Create Homework (Teacher)
```bash
curl -X POST http://localhost:8000/api/homework/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "class_instance": 1,
    "title": "Math Exercise 5",
    "description": "Complete pages 45-50",
    "due_date": "2024-12-15T23:59:59Z"
  }'
```

### 3. Submit Homework (Student)
```bash
curl -X POST http://localhost:8000/api/homework/1/submit/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@homework.pdf"
```

### 4. Get Dashboard Data
```bash
# Teacher Dashboard
curl -X GET http://localhost:8000/api/dashboard/teacher/ \
  -H "Authorization: Bearer <token>"

# Student Dashboard
curl -X GET http://localhost:8000/api/dashboard/student/ \
  -H "Authorization: Bearer <token>"
```

### 5. Join Whiteboard Session
```bash
curl -X POST http://localhost:8000/api/whiteboard/sessions/1/join/ \
  -H "Authorization: Bearer <token>"
```

Response includes WebSocket URL:
```json
{
  "message": "Successfully joined session",
  "websocket_url": "/ws/whiteboard/1/"
}
```

### 6. Get Analytics (Manager)
```bash
curl -X GET "http://localhost:8000/api/analytics/homework-trends/?days=30" \
  -H "Authorization: Bearer <token>"
```

## WebSocket Connection (Whiteboard)

```javascript
const socket = new WebSocket('ws://localhost:8000/ws/whiteboard/1/');

// Send drawing data
socket.send(JSON.stringify({
  type: 'draw',
  x: 100,
  y: 150,
  color: '#000000',
  size: 2
}));

// Receive drawing data
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle drawing data
};
```

## Pagination

All list endpoints support pagination:
```
GET /api/homework/?page=2
```

Response:
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/homework/?page=3",
  "previous": "http://localhost:8000/api/homework/?page=1",
  "results": [...]
}
```

## Filtering & Search

Many endpoints support filtering:
```
GET /api/homework/?class_instance=1&due_date__gte=2024-01-01
GET /api/events/?event_type=CLASS_EVENT
GET /api/users/?role=STUDENT&centre=1
```

## Error Responses

```json
{
  "error": "Error message here",
  "detail": "Detailed error information"
}
```

Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour

## File Uploads

Maximum file size: 10MB

Supported formats:
- Documents: `.pdf`, `.doc`, `.docx`, `.txt`
- Images: `.jpg`, `.jpeg`, `.png`
- Archives: `.zip`

## Testing with Postman/Insomnia

Import the OpenAPI schema (if available) or manually create requests using the examples above.

## Support

For detailed API documentation, visit:
- API Root: `/api/`
- Admin Panel: `/admin/`
- Health Check: `/api/health/`

