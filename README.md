# Slack Clone Backend

A Slack Clone Backend built with Django using **n-layered architecture**. This project provides a complete authentication system, workspace management, channels, messaging, emoji reactions, and custom emojis for a Slack-like messaging platform.

## 🎯 Project Overview

This is the backend-only implementation of a Slack clone, featuring:

- 🔐 **Authentication** - JWT-based auth with four user types
- 🏢 **Workspaces** - Top-level organizational units (like Slack workspaces)
- 💬 **Channels** - Public/private channels within workspaces
- 📝 **Direct Messages** - Private 1:1 conversations
- 🧵 **Threaded Conversations** - Reply to messages, create threads
- ✏️ **Message Editing** - Full edit history tracking
- 👁️ **User Presence** - Last seen, online status
- 📂 **Channel Sections** - Organize channels in sidebar (custom sections)
- 😊 **Emoji Reactions** - React to messages (👍, ❤️, 😂)
- 🎨 **Custom Emojis** - Upload workspace-specific emojis
- 🔔 **Notifications** - @mentions, @channel, DMs, threads, keywords
- 👑 **Admin Access** - Full API access for admins (all channels, all messages)
- 📚 **Interactive API Documentation** - Swagger/OpenAPI

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

## ✨ Features

### Core Features

- **Workspaces** - Create and manage workspaces (formerly called "groups")
- **Channels** - Public, private, and direct message channels
- **Messaging** - Send, edit, delete messages with full history
- **Threads** - Reply to messages, nested conversations
- **User Management** - Four user types with different permissions
- **Admin Privileges** - Full system access (all APIs, all channels, all messages)

### Advanced Features

- **Channel Sections** - Organize channels into collapsible sidebar sections
  - Default sections: Starred, Channels, Direct Messages
  - Custom sections with colors and ordering
  - Drag-and-drop channel organization

- **Emoji Reactions** - React to messages with emojis
  - Unicode emojis (👍, ❤️, 😂, 🎉, etc.)
  - Toggle reactions on/off
  - Reaction counts and user lists

- **Custom Emojis** - Workspace-specific emoji uploads
  - Upload PNG/GIF/JPG as custom emojis
  - Emoji aliases (alternative names)
  - Usage tracking
  - **Admins can manage all emojis**

- **Admin Privileges** - Full system access for admins
  - Access all channels regardless of membership
  - View/edit/delete any message
  - Manage all workspaces, users, and settings
  - Full API access to all endpoints

## 👥 User Types

The system supports four different user roles:

| User Type | Description | Permissions |
|-----------|-------------|-------------|
| **Admin** | Full system access | Manage all users, workspaces, channels, system config. **Access to ALL channels regardless of membership.** |
| **Super User** | Platform manager | Create workspaces, manage users across workspaces. **Access to ALL channels regardless of membership.** |
| **Super Workspace User** | Workspace manager | Manage a single workspace and its channels |
| **User** | Regular user | Basic access, join channels, send messages |

> **Note**: Admins and Super Users automatically have access to all channels and can view/edit/delete any message, regardless of channel membership.

## 🛠️ Technology Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Database**: SQLite3 (development), PostgreSQL ready
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: bcrypt
- **CORS**: django-cors-headers
- **API Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Mock Data**: Faker
- **Image Handling**: Pillow (optional, for emoji image validation)

## 📁 Project Structure

```
backend/
├── config/                     # Django project configuration
│   ├── settings.py            # Project settings
│   ├── urls.py                # Main URL configuration
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── core/                       # Core application
│   ├── models/                # Model Layer
│   │   ├── base.py            # Base model with timestamps
│   │   ├── user.py            # User model + presence tracking
│   │   ├── workspace.py       # Workspace & membership models
│   │   ├── channel.py         # Channel & membership models
│   │   ├── channel_section.py # Channel organization (sidebar)
│   │   ├── message.py         # Message & edit history
│   │   ├── emoji.py           # Reactions & custom emojis
│   │   └── notification.py    # Notifications, settings, unread
│   ├── repositories/          # Repository Layer
│   │   ├── base_repository.py # Generic CRUD
│   │   ├── user_repository.py
│   │   ├── workspace_repository.py
│   │   ├── channel_repository.py
│   │   ├── channel_section_repository.py
│   │   ├── message_repository.py
│   │   ├── emoji_repository.py
│   │   └── notification_repository.py
│   ├── services/              # Service Layer
│   │   ├── auth_service.py    # Auth, JWT, passwords
│   │   ├── user_service.py
│   │   ├── workspace_service.py
│   │   ├── channel_service.py
│   │   ├── channel_section_service.py
│   │   ├── message_service.py
│   │   ├── emoji_service.py
│   │   └── notification_service.py
│   ├── api/                   # API Layer
│   │   ├── authentication.py  # JWT auth class
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── serializers.py     # Request/Response
│   │   ├── urls.py            # Endpoints
│   │   └── views.py           # API views (Swagger)
│   ├── middleware.py          # Presence tracking
│   ├── management/commands/
│   │   ├── create_dummy_users.py
│   │   └── generate_mock_data.py
│   └── migrations/            # Database migrations
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management
├── requirements.txt           # Dependencies
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
   cd slack_clone
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

6. **Generate mock data**
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

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Register new user |
| `POST` | `/api/auth/login/` | Login (returns JWT) |
| `POST` | `/api/auth/logout/` | Logout |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT token |
| `POST` | `/api/auth/password/change/` | Change password |
| `POST` | `/api/auth/password/reset/` | Request reset |
| `POST` | `/api/auth/password/reset/confirm/` | Confirm reset |

### Users

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/users/me/` | Get current profile | Authenticated |
| `PATCH` | `/api/users/me/` | Update profile | Authenticated |
| `GET` | `/api/users/search/?q=` | Search users | Authenticated |
| `GET` | `/api/users/types/` | Get user types | Public |
| `GET` | `/api/users/statistics/` | User stats | Admin |
| `GET` | `/api/users/` | List users | Admin |
| `POST` | `/api/users/` | Create user | Admin |
| `GET` | `/api/users/<id>/` | Get user | Admin |
| `PATCH` | `/api/users/<id>/` | Update user | Admin |
| `DELETE` | `/api/users/<id>/` | Delete user | Admin |

### Workspaces

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/workspaces/` | List workspaces | Authenticated |
| `POST` | `/api/workspaces/` | Create workspace | Admin/Super User |
| `GET` | `/api/workspaces/search/?q=` | Search | Authenticated |
| `GET` | `/api/workspaces/<id>/` | Get details | Authenticated *(Admin/Super User: all including private)* |
| `PATCH` | `/api/workspaces/<id>/` | Update | Owner/Admin/Super User |
| `DELETE` | `/api/workspaces/<id>/` | Delete | Owner/Admin/Super User |
| `GET` | `/api/workspaces/<id>/members/` | List members | Authenticated |
| `POST` | `/api/workspaces/<id>/members/` | Add member | Workspace Admin/Super User |
| `PATCH` | `/api/workspaces/<id>/members/<user_id>/` | Update role | Owner/Admin/Super User |
| `DELETE` | `/api/workspaces/<id>/members/<user_id>/` | Remove | Workspace Admin/Super User |

### Channels

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/channels/` | List channels | Authenticated |
| `POST` | `/api/channels/` | Create channel | Admin/Workspace Admin |
| `GET` | `/api/channels/search/?q=` | Search | Authenticated |
| `POST` | `/api/channels/dm/` | Get/create DM | Authenticated |
| `GET` | `/api/channels/<id>/` | Get details | Authenticated *(Admin/Super User: all including private)* |
| `PATCH` | `/api/channels/<id>/` | Update | Channel Admin/Super User |
| `DELETE` | `/api/channels/<id>/` | Delete | Channel Admin/Super User |
| `POST` | `/api/channels/<id>/join/` | Join public | Authenticated |
| `GET` | `/api/channels/<id>/members/` | List members | Authenticated |
| `POST` | `/api/channels/<id>/members/` | Add member | Channel Admin/Super User |
| `DELETE` | `/api/channels/<id>/members/<user_id>/` | Remove | Channel Admin/Super User |

### Channel Sections

Organize channels in sidebar with custom sections.

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/sections/?workspace_id=` | List sections | Authenticated |
| `POST` | `/api/sections/?workspace_id=` | Create section | Authenticated |
| `GET` | `/api/sections/<id>/` | Get section | Authenticated |
| `PATCH` | `/api/sections/<id>/` | Update | Owner |
| `DELETE` | `/api/sections/<id>/` | Delete | Owner |
| `POST` | `/api/sections/reorder/` | Reorder sections | Authenticated |
| `POST` | `/api/sections/<id>/toggle-collapse/` | Toggle collapse | Authenticated |
| `POST` | `/api/sections/<id>/channels/` | Add channel | Authenticated |
| `DELETE` | `/api/sections/<id>/channels/?channel_id=` | Remove channel | Authenticated |
| `POST` | `/api/sections/<id>/reorder-channels/` | Reorder channels | Authenticated |
| `POST` | `/api/sections/move-channel/` | Move between sections | Authenticated |

### Messages

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/channels/<id>/messages/` | Get messages | Channel Member *(Admin/Super User: all channels)* |
| `POST` | `/api/channels/<id>/messages/` | Send message | Channel Member |
| `GET` | `/api/messages/<id>/` | Get with history | Channel Member *(Admin/Super User: all messages)* |
| `PATCH` | `/api/messages/<id>/` | Edit | Owner/Admin/Super User |
| `DELETE` | `/api/messages/<id>/` | Delete (soft) | Owner/Admin/Super User |
| `GET` | `/api/messages/<id>/thread/` | Get replies | Channel Member *(Admin/Super User: all)* |
| `POST` | `/api/messages/<id>/thread/` | Reply | Channel Member *(Admin/Super User: all channels)* |
| `GET` | `/api/messages/<id>/history/` | Edit history | Channel Member *(Admin/Super User: all)* |
| `GET` | `/api/messages/search/?q=` | Search | Authenticated |

### Direct Messages

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/dm/` | List conversations | Authenticated |
| `GET` | `/api/dm/<user_id>/` | Get conversation | Authenticated |
| `POST` | `/api/dm/<user_id>/` | Send DM | Authenticated |

### Emoji Reactions

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/messages/<id>/reactions/` | List reactions | Authenticated |
| `POST` | `/api/messages/<id>/reactions/` | Add reaction | Authenticated |
| `DELETE` | `/api/messages/<id>/reactions/?emoji=` | Remove | Authenticated |
| `POST` | `/api/messages/<id>/reactions/toggle/` | Toggle reaction | Authenticated |

### Custom Emojis

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/emojis/?workspace_id=` | List emojis | Authenticated |
| `POST` | `/api/emojis/?workspace_id=` | Create emoji | Workspace Admin/Admin/Super User |
| `GET` | `/api/emojis/<id>/` | Get emoji | Authenticated |
| `DELETE` | `/api/emojis/<id>/` | Delete | Creator/Admin/Super User |
| `GET` | `/api/emojis/search/?q=` | Search | Authenticated |
| `POST` | `/api/emojis/alias/` | Create alias | Workspace Admin/Admin/Super User |

### Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/`

## 👤 Dummy Users

After running `python manage.py generate_mock_data`, the following test users are created:

| Email | Username | User Type | Password |
|-------|----------|-----------|----------|
| admin@slackclone.com | admin | Admin | Test@123456 |
| superuser@slackclone.com | superuser | Super User | Test@123456 |
| superworkspaceuser@slackclone.com | superworkspaceuser | Super Workspace User | Test@123456 |
| user@slackclone.com | regularuser | User | Test@123456 |

> **Note**: All users use the same default password `Test@123456`. Change these in production!

## 🎲 Mock Data Generation

Generate comprehensive mock data for testing:

```bash
# Generate with defaults (20 users, 5 workspaces, 3 channels per workspace, 10 messages per channel)
python manage.py generate_mock_data

# Custom amounts
python manage.py generate_mock_data --users 50 --workspaces 10 --channels-per-workspace 5 --messages-per-channel 20

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
| `--users` | 20 | Number of regular users |
| `--workspaces` | 5 | Number of workspaces |
| `--channels-per-workspace` | 3 | Channels per workspace |
| `--messages-per-channel` | 10 | Messages per channel |
| `--replies-per-thread` | 5 | Max replies per thread |
| `--password` | Test@123456 | Password for all users |
| `--clear` | False | Clear existing data first |

### Sample Mock Data Output

```
Summary:
  Total Users: 7
  Total Workspaces: 1
  Total Channels: 4
  Total Workspace Memberships: 5
  Total Channel Memberships: 11
  Total Messages: 53
  Total Thread Replies: 23
  Total Edit History: 15
  Total Channel Sections: 18
  Total Channel Section Items: 20
  Total Emoji Reactions: 299
  Total Notifications: 12
  Total Unread Counts: 17
  Total Keyword Alerts: 14
```

## 🔐 Authentication

### JWT Token Usage

The API uses **JWT-only authentication**. After successful login, you'll receive a JWT token:

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@slackclone.com", "password": "Test@123456"}'

# Response:
{
  "message": "Login successful",
  "user": {...},
  "token": "eyJhbGciOiJIUzI1NiIs..."
}

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

Configure in `config/settings.py`:

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
- **Password Hashing**: bcrypt via `BCryptSHA256PasswordHasher`
- **CORS**: Enabled for all origins (development)
- **JWT Expiration**: 24 hours (configurable in `AuthService`)
- **Swagger/OpenAPI**: Configured via `drf-spectacular`
- **Authentication**: JWT-only (no session auth for API)

## 💬 Messaging Features

### Channel Messages
- Send messages to channels you're a member of
- **Admins and Super Users can access messages in ALL channels**
- Messages are ordered chronologically
- Only top-level messages returned (replies in threads)

### Threaded Conversations
- Reply to any message to create a thread
- Thread replies separate from main channel messages
- Each message shows `reply_count` and `is_thread_parent`

### Message Editing
- Users can edit their own messages
- **Admins and Super Users can edit any message**
- All edits tracked in `MessageEditHistory`
- Edited messages show `is_edited: true` and `edited_at`

### Message Deletion
- Soft delete (marked as deleted, not removed)
- Users can delete their own messages
- **Admins and Super Users can delete any message**
- Deleted messages show `is_deleted: true`

### Direct Messages
- Send DMs to any user via `/api/dm/<user_id>/`
- DM conversations are private between two users
- List all DM conversations via `/api/dm/`

### Channel Sections
- Organize channels into collapsible sections
- Default sections: Starred, Channels, Direct Messages
- Create custom sections with colors
- Reorder sections and channels

### Emoji Reactions
- React to messages with any Unicode emoji
- Toggle reactions on/off
- See reaction counts and who reacted

### Custom Emojis
- Upload PNG/GIF/JPG as custom emojis
- Use as `:emoji-name:` in messages
- Create aliases for existing emojis
- Track usage statistics

### Notifications
- **@Mentions** - Notify users when mentioned by username
- **@channel / @here / @everyone** - Notify workspace members
- **Direct Message Alerts** - Notify on new DMs
- **Thread Reply Notifications** - Notify thread participants
- **Keyword Alerts** - Custom keyword subscriptions
- **Do Not Disturb** - Time-based DND mode
- **Per-Channel Mute** - Mute specific channels
- **Unread Counts** - Per-channel and total unread tracking
- **Notification Settings** - Full preference management

#### Notification Types

| Type | Description |
|------|-------------|
| `mention` | @username mentioned |
| `dm` | Direct message received |
| `thread_reply` | Reply in thread you're in |
| `reaction` | Reaction on your message |
| `channel_message` | New channel message |
| `keyword_alert` | Keyword match |
| `channel_mention` | @channel used |
| `here_mention` | @here used (online users) |
| `everyone_mention` | @everyone used |

#### Notification API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notifications/` | List notifications |
| `POST` | `/api/notifications/` | Mark as read |
| `GET` | `/api/notifications/<id>/` | Get notification |
| `POST` | `/api/notifications/<id>/` | Mark as read |
| `DELETE` | `/api/notifications/<id>/` | Delete notification |
| `GET` | `/api/notifications/settings/` | Get settings |
| `PATCH` | `/api/notifications/settings/` | Update settings |
| `GET` | `/api/notifications/unread/` | Unread summary |
| `POST` | `/api/notifications/unread/` | Mark all read |
| `POST` | `/api/notifications/unread/<channel_id>/` | Mark channel read |
| `GET` | `/api/notifications/keywords/` | List keywords |
| `POST` | `/api/notifications/keywords/` | Add keyword |
| `DELETE` | `/api/notifications/keywords/<id>/` | Delete keyword |
| `POST` | `/api/notifications/mute/channel/<id>/` | Mute channel |
| `DELETE` | `/api/notifications/mute/channel/<id>/` | Unmute channel |
| `GET` | `/api/notifications/dnd/` | Get DND status |
| `POST` | `/api/notifications/dnd/` | Set DND |

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

This project is part of Slack Clone Backend. See the repository for license information.

## 🤝 Contributing

Contributions are welcome! Please follow the existing code structure and n-layered architecture principles.
