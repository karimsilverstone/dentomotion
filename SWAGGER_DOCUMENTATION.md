# Swagger/OpenAPI Documentation

The Django backend includes comprehensive API documentation using Swagger (drf-yasg).

## Accessing API Documentation

### Swagger UI (Interactive)
- **URL**: `https://your-domain.com/swagger/` or `/api-docs/`
- **Features**:
  - Interactive API testing
  - Try out endpoints directly from browser
  - View request/response schemas
  - Authentication testing

### ReDoc (Alternative UI)
- **URL**: `https://your-domain.com/redoc/`
- **Features**:
  - Clean, three-panel layout
  - Better for documentation reading
  - Searchable API reference

### OpenAPI Schema
- **JSON**: `https://your-domain.com/swagger.json`
- **YAML**: `https://your-domain.com/swagger.yaml`
- Import into Postman, Insomnia, or other API clients

## Using Swagger UI

### 1. **Without Authentication** (Public Endpoints)
Some endpoints like `/api/auth/login/` don't require authentication:
- Click on the endpoint
- Click "Try it out"
- Fill in the parameters
- Click "Execute"

### 2. **With Authentication** (Protected Endpoints)
Most endpoints require JWT authentication:

**Step 1: Get Access Token**
1. Go to `/api/auth/login/`
2. Click "Try it out"
3. Enter credentials:
   ```json
   {
     "email": "user@example.com",
     "password": "password123"
   }
   ```
4. Click "Execute"
5. Copy the `access` token from the response

**Step 2: Authorize**
1. Click the "Authorize" button at the top
2. Enter: `Bearer <your-access-token>`
3. Click "Authorize" then "Close"

**Step 3: Test Endpoints**
Now all authenticated endpoints will work with your token.

## Example: Testing the Complete Flow

### 1. Login
```
POST /api/auth/login/
Body:
{
  "email": "teacher@school.com",
  "password": "password123"
}
```

### 2. Authorize with Token
Copy the access token and click "Authorize" button.

### 3. List Your Classes
```
GET /api/classes/
```

### 4. Create Homework
```
POST /api/homework/
Body:
{
  "class_instance": 1,
  "title": "Math Assignment",
  "description": "Complete exercises 1-10",
  "due_date": "2024-12-20T23:59:59Z"
}
```

### 5. View Homework
```
GET /api/homework/1/
```

## API Organization

The Swagger documentation organizes endpoints by tags:

- **auth**: Authentication endpoints
- **users**: User management
- **centres**: Centre management
- **holidays**: Holiday management
- **terms**: Term date management
- **classes**: Class management
- **homework**: Homework operations
- **submissions**: Homework submissions
- **events**: Calendar and events
- **whiteboard**: Whiteboard sessions
- **dashboard**: Role-specific dashboards
- **analytics**: Analytics and reporting

## Features in Swagger UI

### Request Examples
Each endpoint shows example requests with all fields.

### Response Examples
See example responses for different status codes (200, 201, 400, 401, 403, 404).

### Schema Definitions
View detailed model schemas at the bottom of the page:
- User
- Centre
- Class
- Homework
- Submission
- Event
- WhiteboardSession
- etc.

### Filters and Pagination
- Test filtering: `?role=TEACHER&is_active=true`
- Test pagination: `?page=2`
- Test search: `?search=math`

## Development vs Production

### Development (DEBUG=True)
- Swagger UI is fully accessible
- No authentication required to view documentation
- Can test all endpoints interactively

### Production (DEBUG=False)
- Documentation still accessible but may require authentication
- Consider restricting access to internal IPs only
- To restrict access, modify `permission_classes` in schema_view

## Customizing Documentation

### Add Descriptions to Endpoints
In your views, add docstrings:

```python
class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoints.
    
    list: Get list of users (filtered by role and centre)
    create: Create a new user (Admin/Manager only)
    retrieve: Get user details
    update: Update user information
    destroy: Delete user (Admin only)
    """
```

### Add Response Examples
Use drf-yasg decorators:

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    operation_description="Login with email and password",
    responses={
        200: openapi.Response(
            description="Successful login",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        401: 'Invalid credentials'
    }
)
def login(self, request):
    # ... implementation
```

## Importing into API Clients

### Postman
1. Download schema: `https://your-domain.com/swagger.json`
2. In Postman: Import → Upload File → Select downloaded file
3. All endpoints will be imported with examples

### Insomnia
1. Create new request collection
2. Import from URL: `https://your-domain.com/swagger.json`
3. Or import downloaded file

## Troubleshooting

### Swagger UI Not Loading
- Check that `drf_yasg` is in `INSTALLED_APPS`
- Verify URL patterns are correct
- Check browser console for errors

### Authentication Not Working
- Make sure to include "Bearer " before the token
- Token format: `Bearer eyJ0eXAiOiJKV1QiLCJhbGc...`
- Check token hasn't expired (default: 60 minutes)

### Endpoints Not Showing
- Check viewsets are registered in router
- Verify URLs are included in urlpatterns
- Restart development server after changes

## Security Note

In production, consider:
- Restricting Swagger UI access to authenticated users
- Using IP whitelisting for documentation
- Disabling documentation entirely if not needed

To restrict access:
```python
permission_classes=[permissions.IsAdminUser]  # Admins only
# or
permission_classes=[permissions.IsAuthenticated]  # Any logged-in user
```

## Additional Resources

- drf-yasg documentation: https://drf-yasg.readthedocs.io/
- OpenAPI Specification: https://swagger.io/specification/
- Swagger UI Guide: https://swagger.io/tools/swagger-ui/

---

**Quick Links:**
- Swagger UI: `/swagger/` or `/api-docs/`
- ReDoc: `/redoc/`
- OpenAPI Schema: `/swagger.json`

