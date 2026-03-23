# zed-base

A Slack Clone Backend built with Django using **n-layered architecture**. This project provides a complete authentication system, user management, groups, channels, and messaging for a Slack-like messaging platform.

## 🎯 Project Overview

This is the backend-only implementation of a Slack clone, featuring:
- 🔐 Robust authentication system with four distinct user types
- 👥 Group management (workspaces/organizations)
- 💬 Channel management within groups
- 📝 Direct messaging support
- 🧵 Threaded conversations (reply to messages)
- ✏️ Message editing with full history tracking
- 👁️ User presence tracking (last seen, online status)
- 📚 Interactive API documentation with Swagger/OpenAPI

The project follows clean architecture principles with separation of concerns across multiple layers.

## 🏗️ Architecture

The project implements **n-layered architecture** with the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (Views/Serializers)          │
├─────────────────────────────────────────────────────────────┤
│                      Service Layer (Business Logic)         │
├─────────────────────────────────────────────────────────────┤
│                      Repository Layer (Data Access)         │
├─────────────────────────────────────────────────────────────┤
│                      Model Layer (Database Models)          │
└─────────────────────────────────────────────────────────────┘
```

### Layers Description

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Model** | `core/models/` | Database models and business entities |
| **Repository** | `core/repositories/` | Data access logic (CRUD operations) |
| **Service** | `core/services/` | Business logic and orchestration |
| **API** | `core/api/` | HTTP endpoints, serializers, and request handling |

## 👥 User Types

The system supports four different user roles:

| User Type | Description | Permissions |
|-----------|-------------|-------------|
| **Admin** | Full system access | Manage all users, groups, channels, and system configuration |
| **Super User** | Platform manager | Create groups, manage users across groups |
| **Super Group User** | Group manager | Manage a single group and its channels |
| **User** | Regular user | Basic access, join channels, send messages |

## 🛠️ Technology Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Database**: SQLite3 (located in project folder)
- **Authentication**: JWT (PyJWT) + Session-based
- **Password Hashing**: bcrypt 3.2.2
- **CORS**: django-cors-headers
- **API Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Mock Data**: Faker
- **Environment**: python-dotenv

## 📁 Project Structure

```
backend/
├── config/                     # Django project configuration
│   ├── settings.py            # Project settings (bcrypt, SQLite, CORS, Swagger)
│   ├── urls.py                # Main URL configuration
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── core/                       # Core application (all backend logic)
│   ├── models/                # Model Layer
│   │   ├── base.py            # Base model with timestamps
│   │   ├── user.py            # User model with 4 user types + presence tracking
│   │   ├── group.py           # Group and GroupMembership models
│   │   ├── channel.py         # Channel and ChannelMembership models
│   │   └── message.py         # Message and MessageEditHistory models
│   ├── repositories/          # Repository Layer
│   │   ├── base_repository.py # Generic CRUD operations
│   │   ├── user_repository.py # User-specific DB operations
│   │   ├── group_repository.py# Group-specific DB operations
│   │   ├── channel_repository.py # Channel-specific DB operations
│   │   └── message_repository.py # Message-specific DB operations
│   ├── services/              # Service Layer
│   │   ├── auth_service.py    # Auth, JWT, password management
│   │   ├── user_service.py    # User business logic
│   │   ├── group_service.py   # Group business logic
│   │   ├── channel_service.py # Channel business logic
│   │   └── message_service.py # Message business logic
│   ├── api/                   # API Layer
│   │   ├── authentication.py  # JWT authentication class
│   │   ├── exceptions.py      # Custom exception handler
│   │   ├── serializers.py     # Request/Response serializers
│   │   ├── urls.py            # API endpoints
│   │   └── views.py           # API views with Swagger annotations
│   ├── middleware.py          # Custom middleware (presence tracking)
│   ├── management/commands/
│   │   ├── create_dummy_users.py  # Command to create dummy users
│   │   └── generate_mock_data.py  # Command to generate mock data
│   └── migrations/            # Database migrations
├── db.sqlite3                 # SQLite database (in project folder)
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── venv/                      # Virtual environment
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zed-base
   ```

2. **Navigate to backend directory**
   ```bash
   cd backend
   ```

3. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Generate mock data (includes dummy users)**
   ```bash
   python manage.py generate_mock_data
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/`

## 📚 API Documentation (Swagger)

Interactive API documentation is available via Swagger UI:

| Documentation | URL |
|--------------|-----|
| **Swagger UI** | `http://localhost:8000/api/docs/` |
| **ReDoc** | `http://localhost:8000/api/redoc/` |
| **OpenAPI Schema** | `http://localhost:8000/api/schema/` |

## 🔌 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Register a new user |
| `POST` | `/api/auth/login/` | User login (returns JWT token) |
| `POST` | `/api/auth/logout/` | User logout |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT token |
| `POST` | `/api/auth/password/change/` | Change password (authenticated) |
| `POST` | `/api/auth/password/reset/` | Request password reset |
| `POST` | `/api/auth/password/reset/confirm/` | Confirm password reset |

### User Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/users/me/` | Get current user profile | Authenticated |
| `PATCH` | `/api/users/me/` | Update current user profile | Authenticated |
| `GET` | `/api/users/search/?q=query` | Search users | Authenticated |
| `GET` | `/api/users/types/` | Get available user types | Public |
| `GET` | `/api/users/statistics/` | Get user statistics | Admin only |
| `GET` | `/api/users/` | List all users | Admin only |
| `POST` | `/api/users/` | Create user | Admin only |
| `GET` | `/api/users/<id>/` | Get user by ID | Admin only |
| `PATCH` | `/api/users/<id>/` | Update user | Admin only |
| `DELETE` | `/api/users/<id>/` | Delete user | Admin only |

### Group Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/groups/` | List groups | Authenticated |
| `POST` | `/api/groups/` | Create group | Admin/Super User |
| `GET` | `/api/groups/search/?q=query` | Search groups | Authenticated |
| `GET` | `/api/groups/<id>/` | Get group details | Authenticated |
| `PATCH` | `/api/groups/<id>/` | Update group | Owner/Admin |
| `DELETE` | `/api/groups/<id>/` | Delete group | Owner/Admin |
| `GET` | `/api/groups/<id>/members/` | List group members | Authenticated |
| `POST` | `/api/groups/<id>/members/` | Add member to group | Group Admin |
| `PATCH` | `/api/groups/<id>/members/<user_id>/` | Update member role | Owner/Admin |
| `DELETE` | `/api/groups/<id>/members/<user_id>/` | Remove member | Group Admin |

### Channel Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/channels/` | List channels | Authenticated |
| `POST` | `/api/channels/` | Create channel | Admin/Super User/Group Admin |
| `GET` | `/api/channels/search/?q=query` | Search channels | Authenticated |
| `POST` | `/api/channels/dm/` | Create/get direct message | Authenticated |
| `GET` | `/api/channels/<id>/` | Get channel details | Authenticated |
| `PATCH` | `/api/channels/<id>/` | Update channel | Channel Owner/Admin |
| `DELETE` | `/api/channels/<id>/` | Delete channel | Channel Owner/Admin |
| `POST` | `/api/channels/<id>/join/` | Join public channel | Authenticated |
| `GET` | `/api/channels/<id>/members/` | List channel members | Authenticated |
| `POST` | `/api/channels/<id>/members/` | Add member to channel | Channel Admin |
| `DELETE` | `/api/channels/<id>/members/<user_id>/` | Remove member | Channel Admin |

### Message Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/channels/<id>/messages/` | Get channel messages | Channel Member |
| `POST` | `/api/channels/<id>/messages/` | Send message to channel | Channel Member |
| `GET` | `/api/messages/<id>/` | Get message with edit history | Channel Member |
| `PATCH` | `/api/messages/<id>/` | Edit message | Owner or Admin |
| `DELETE` | `/api/messages/<id>/` | Delete message (soft) | Owner or Admin |
| `GET` | `/api/messages/<id>/thread/` | Get thread replies | Channel Member |
| `POST` | `/api/messages/<id>/thread/` | Reply to message (thread) | Channel Member |
| `GET` | `/api/messages/<id>/history/` | Get message edit history | Channel Member |
| `GET` | `/api/messages/search/?q=query` | Search messages | Authenticated |

### Direct Message Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/dm/` | List DM conversations | Authenticated |
| `GET` | `/api/dm/<user_id>/` | Get DM conversation with user | Authenticated |
| `POST` | `/api/dm/<user_id>/` | Send DM to user | Authenticated |

### Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/`

## 👤 Dummy Users

After running `python manage.py generate_mock_data`, the following test users are created:

| Email | Username | User Type | Password |
|-------|----------|-----------|----------|
| admin@slackclone.com | admin | Admin | Test@123456 |
| superuser@slackclone.com | superuser | Super User | Test@123456 |
| supergroupuser@slackclone.com | supergroupuser | Super Group User | Test@123456 |
| user@slackclone.com | regularuser | User | Test@123456 |

> **Note**: All users use the same default password `Test@123456`. Change these in production!

## 🎲 Mock Data Generation

Generate comprehensive mock data for testing:

```bash
# Generate with defaults (20 users, 5 groups, 3 channels per group, 10 messages per channel)
python manage.py generate_mock_data

# Custom amounts
python manage.py generate_mock_data --users 50 --groups 10 --channels-per-group 5 --messages-per-channel 20

# With more threads
python manage.py generate_mock_data --replies-per-thread 10

# Custom password
python manage.py generate_mock_data --password=MyCustomPass123

# Clear existing data first
python manage.py generate_mock_data --clear
```

### Mock Data Options

| Option | Default | Description |
|--------|---------|-------------|
| `--users` | 20 | Number of regular users to create |
| `--groups` | 5 | Number of groups to create |
| `--channels-per-group` | 3 | Channels per group |
| `--messages-per-channel` | 10 | Messages per channel |
| `--replies-per-thread` | 5 | Max replies per thread |
| `--password` | Test@123456 | Password for all users |
| `--clear` | False | Clear existing data first |

### Sample Mock Data Output

```
Summary:
  Total Users: 34
  Total Groups: 8
  Total Channels: 41
  Total Group Memberships: 95
  Total Channel Memberships: 214
  Total Messages: 150
  Total Thread Replies: 45
  Total Edit History: 20
```

## 🔐 Authentication

### JWT Token Usage

The API uses **JWT-only authentication**. After successful login, you'll receive a JWT token. Use it in subsequent requests:

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@slackclone.com", "password": "Test@123456"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/users/me/
```

### User Presence

Users have presence tracking (like Slack):
- `last_seen`: When the user was last active
- `is_online`: True if active within 5 minutes
- `presence_display`: Human-readable ("Active", "Last seen 5 min ago", etc.)

Presence is automatically updated on each authenticated request.

## 🗄️ Database

The project uses **SQLite3** with the database file located at:
```
backend/db.sqlite3
```

The database is configured in `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## ⚙️ Configuration

Key settings in `config/settings.py`:

- **Custom User Model**: `AUTH_USER_MODEL = 'core.User'`
- **Password Hashing**: Uses bcrypt via `BCryptSHA256PasswordHasher`
- **CORS**: Enabled for all origins (development mode)
- **JWT Expiration**: 24 hours (configurable in `AuthService`)
- **Swagger/OpenAPI**: Configured via `drf-spectacular`
- **Authentication**: JWT-only (no session auth for API)

## 💬 Messaging Features

### Channel Messages
- Send messages to channels you're a member of
- Messages are ordered chronologically
- Only top-level messages are returned (replies are in threads)

### Threaded Conversations
- Reply to any message to create a thread
- Thread replies are separate from main channel messages
- Each message shows `reply_count` and `is_thread_parent`

### Message Editing
- Users can edit their own messages
- Admins can edit any message
- All edits are tracked in `MessageEditHistory`
- Edited messages show `is_edited: true` and `edited_at` timestamp

### Message Deletion
- Soft delete (message is marked as deleted, not removed)
- Users can delete their own messages
- Admins can delete any message
- Deleted messages show `is_deleted: true`

### Direct Messages
- Send DMs to any user via `/api/dm/<user_id>/`
- DM conversations are private between two users
- List all DM conversations via `/api/dm/`

### Example: Send a Message

```bash
# Send message to channel
curl -X POST http://localhost:8000/api/channels/1/messages/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello everyone!"}'

# Reply to a message (create thread)
curl -X POST http://localhost:8000/api/messages/1/thread/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "This is a reply!"}'

# Edit a message
curl -X PATCH http://localhost:8000/api/messages/1/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated message content"}'
```

## 📝 Development

### Code Quality Tools

```bash
# Format code with black
black .

# Lint code with flake8
flake8 .
```

### Running Tests

```bash
python manage.py test
```

## 📄 License

This project is part of zed-base. See the repository for license information.

## 🤝 Contributing

Contributions are welcome! Please follow the existing code structure and n-layered architecture principles.
