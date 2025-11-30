# OpenAPI 3.0 Documentation

The Django backend includes comprehensive API documentation using **OpenAPI 3.0** (via drf-spectacular).

## What's New in OpenAPI 3.0

OpenAPI 3.0 is the latest version of the OpenAPI Specification (formerly Swagger), featuring:

- ✅ **Better Security Schemes**: Improved JWT/Bearer token support
- ✅ **Enhanced Request Bodies**: Cleaner request body definitions
- ✅ **Multiple Content Types**: Better support for file uploads
- ✅ **Improved Components**: Reusable schemas, responses, and parameters
- ✅ **Links & Callbacks**: Better API relationship documentation
- ✅ **Deprecation Support**: Mark deprecated endpoints clearly

## Accessing API Documentation

### Swagger UI (Interactive)
- **URL**: `http://your-domain.com/swagger/` or `/api-docs/`
- **Features**:
  - Interactive API testing
  - Try out endpoints directly from browser
  - View request/response schemas
  - Persistent authentication (stays logged in)
  - Search and filter endpoints

### ReDoc (Alternative UI)
- **URL**: `http://your-domain.com/redoc/`
- **Features**:
  - Clean, three-panel layout
  - Better for documentation reading
  - Searchable API reference
  - Download button for schema

### OpenAPI 3.0 Schema
- **Download**: `http://your-domain.com/api/schema/`
- Add `?format=json` or `?format=yaml` for specific formats
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
1. Click the "Authorize" button (🔓) at the top right
2. In the "Bearer" field, enter your access token (without "Bearer " prefix)
3. Click "Authorize" then "Close"

**Step 3: Test Endpoints**
Now all authenticated endpoints will work with your token.
The authorization persists across page reloads (thanks to OpenAPI 3.0!).

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

The documentation organizes endpoints by tags:

| Tag | Description |
|-----|-------------|
| **Authentication** | Login, logout, token refresh, password reset |
| **Users** | User management and profiles |
| **Centres** | Centre management, holidays, term dates |
| **Classes** | Class management, enrolments, teacher assignments |
| **Homework** | Homework assignments and submissions |
| **Calendar** | Events and calendar management |
| **Whiteboard** | Real-time whiteboard sessions |
| **Dashboards** | Role-specific dashboard data |
| **Analytics** | Reports and analytics |

## Features in Swagger UI

### Request Examples
Each endpoint shows example requests with all fields and their types.

### Response Examples
See example responses for different status codes:
- `200 OK` - Successful response
- `201 Created` - Resource created
- `400 Bad Request` - Validation errors
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found

### Schema Definitions
View detailed model schemas in the "Schemas" section:
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
- Test ordering: `?ordering=-created_at`

## Security Configuration

### JWT Bearer Authentication
The API uses JWT Bearer token authentication:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

In OpenAPI 3.0, this is defined as:
```yaml
securitySchemes:
  Bearer:
    type: http
    scheme: bearer
    bearerFormat: JWT
```

## Development vs Production

### Development (DEBUG=True)
- Swagger UI is fully accessible
- No authentication required to view documentation
- Can test all endpoints interactively

### Production (DEBUG=False)
- Documentation still accessible
- Consider restricting access for security
- To restrict access, modify settings in `SPECTACULAR_SETTINGS`

## Customizing Documentation

### Add Descriptions to Endpoints
Use the `@extend_schema` decorator:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoints.
    """
    
    @extend_schema(
        summary="List all users",
        description="Get a paginated list of users filtered by role and centre",
        parameters=[
            OpenApiParameter(
                name='role',
                description='Filter by user role',
                required=False,
                type=str,
                enum=['SUPER_ADMIN', 'CENTRE_MANAGER', 'TEACHER', 'STUDENT', 'PARENT']
            ),
        ],
        responses={200: UserSerializer(many=True)},
        tags=['Users']
    )
    def list(self, request):
        # ... implementation
```

### Add Response Examples
```python
from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    summary="Login with email and password",
    request=LoginSerializer,
    responses={
        200: TokenSerializer,
        401: OpenApiExample(
            'Invalid credentials',
            value={'detail': 'No active account found with the given credentials'}
        )
    },
    examples=[
        OpenApiExample(
            'Valid login',
            value={'email': 'user@example.com', 'password': 'password123'},
            request_only=True
        ),
    ],
    tags=['Authentication']
)
def login(self, request):
    # ... implementation
```

### Add Tags to ViewSets
```python
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(tags=['Classes']),
    create=extend_schema(tags=['Classes']),
    retrieve=extend_schema(tags=['Classes']),
    update=extend_schema(tags=['Classes']),
    destroy=extend_schema(tags=['Classes']),
)
class ClassViewSet(viewsets.ModelViewSet):
    # ...
```

## Importing into API Clients

### Postman
1. Download schema: `http://your-domain.com/api/schema.json`
2. In Postman: Import → Upload File → Select downloaded file
3. All endpoints will be imported with examples
4. Set up environment variable for `{{baseUrl}}`

### Insomnia
1. Create new request collection
2. Import from URL: `http://your-domain.com/api/schema.yaml`
3. Or import downloaded file

### OpenAPI Generator
Generate client SDKs in any language:
```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate -i http://your-domain.com/api/schema.json -g python -o ./client

# Generate JavaScript client
openapi-generator-cli generate -i http://your-domain.com/api/schema.json -g javascript -o ./client
```

## Troubleshooting

### Swagger UI Not Loading
- Check that `drf_spectacular` is in `INSTALLED_APPS`
- Verify URL patterns are correct
- Check browser console for errors
- Clear browser cache

### Authentication Not Working
- Enter token WITHOUT "Bearer " prefix in the Authorize dialog
- Check token hasn't expired (default: 60 minutes)
- Get a new token from `/api/auth/login/`

### Endpoints Not Showing
- Check viewsets are registered in router
- Verify URLs are included in urlpatterns
- Restart development server after changes
- Check `SPECTACULAR_SETTINGS` configuration

### Schema Generation Errors
```bash
# Validate your schema
docker-compose exec web python manage.py spectacular --validate

# Generate schema to file for inspection
docker-compose exec web python manage.py spectacular --file schema.yaml
```

## Security Note

In production, consider:
- Restricting Swagger UI access to authenticated users
- Using IP whitelisting for documentation
- Disabling documentation entirely if not needed

To restrict access in settings:
```python
SPECTACULAR_SETTINGS = {
    # ... other settings
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
    # or
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
}
```

## Comparing OpenAPI 2.0 vs 3.0

| Feature | OpenAPI 2.0 (Swagger) | OpenAPI 3.0 |
|---------|----------------------|-------------|
| Request Body | In parameters | Separate `requestBody` |
| File Upload | `formData` type | `multipart/form-data` content |
| Security | `securityDefinitions` | `securitySchemes` in components |
| Callbacks | Not supported | ✅ Supported |
| Links | Not supported | ✅ Supported |
| Nullable | Not native | ✅ Native support |
| oneOf/anyOf | Limited | ✅ Full support |

## Additional Resources

- drf-spectacular documentation: https://drf-spectacular.readthedocs.io/
- OpenAPI 3.0 Specification: https://spec.openapis.org/oas/v3.0.3
- Swagger UI Guide: https://swagger.io/tools/swagger-ui/
- OpenAPI Generator: https://openapi-generator.tech/

---

## Quick Links

| Resource | URL |
|----------|-----|
| Swagger UI | `/swagger/` or `/api-docs/` |
| ReDoc | `/redoc/` |
| OpenAPI Schema | `/api/schema/` |
| Schema as JSON | `/api/schema/?format=json` |
| Schema as YAML | `/api/schema/?format=yaml` |

---

**OpenAPI Version**: 3.0.3  
**Library**: drf-spectacular 0.27.0
