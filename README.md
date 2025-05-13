# Sophia AI Chatbot

A multi-language, persona-based chatbot named Sophia built with Flask. Sophia is a flirty, seductive virtual woman who responds in multiple languages with emotional intelligence.

## Features

- 💬 **Multi-language Support**: Detects and responds in the user's language
- 🌶️ **Seductive Personality**: Flirtatious responses based on message context
- 💯 **Message Tracking**: Free users get 50 messages per day
- 👑 **Premium Features**: Unlock voice replies and unlimited messaging
- 🔄 **Social Integration**: Telegram and Instagram bot interfaces
- 🎭 **Admin Panel**: Manage users and upload content
- 🎙️ **Voice Support**: Premium users get voice responses

## Directory Structure

```
sophia/
│
├── app.py               # Main application configuration
├── main.py              # Entry point for the application
├── models.py            # Database models
├── views.py             # Controllers and route handlers
├── responses.json       # Predefined response templates
│
├── static/              # Static assets
│   ├── css/
│   │   └── styles.css   # Custom styling
│   ├── js/
│   │   └── chat.js      # Client-side chat functionality
│   └── uploads/         # User uploads (created at runtime)
│       ├── images/      # Images for Sophia
│       ├── videos/      # Videos for Sophia
│       └── audio/       # Voice responses
│
└── templates/           # HTML templates
    ├── admin/           # Admin panel templates
    │   ├── dashboard.html
    │   ├── users.html
    │   ├── content.html
    │   └── upload.html
    ├── base.html        # Base template
    ├── index.html       # Main chat interface
    ├── login.html       # User login
    ├── register.html    # User registration
    └── upgrade.html     # Premium upgrade
```

## Installation and Setup

### Requirements

- Python 3.9 or higher
- PostgreSQL database (optional, falls back to SQLite)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/sophia-chatbot.git
   cd sophia-chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   ```

5. Visit `http://localhost:5000` in your browser

### Deployment to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app`
   - **Environment Variables**:
     - `SESSION_SECRET`: [generate a secret key]
     - `DATABASE_URL`: [your database connection string]

4. Click "Create Web Service"

## Database Setup

The application will automatically create tables when it first runs. By default, it uses:

- PostgreSQL if `DATABASE_URL` is provided as an environment variable
- SQLite (sophia_chat.db) as a fallback

## Telegram Bot Setup

1. Talk to BotFather on Telegram to create a new bot
2. Set the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
   - `WEBHOOK_URL`: Your app URL + `/api/telegram`

3. Set the webhook:
   ```
   https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}
   ```

## Instagram Bot Setup

1. Create an Instagram account for your bot
2. Set environment variables:
   - `INSTAGRAM_USERNAME`: Your bot's Instagram username
   - `INSTAGRAM_PASSWORD`: Your bot's Instagram password

## Admin Access

Default admin credentials:
- Username: `admin`
- Password: `admin`

**Important:** Change the admin password after first login.

## Customizing Sophia's Responses

Edit the `responses.json` file to customize how Sophia responds to different message types.

## License

This project is licensed under the MIT License - see the LICENSE file for details.