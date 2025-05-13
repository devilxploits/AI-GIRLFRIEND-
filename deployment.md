# Sophia AI Chatbot - Deployment Guide

This guide provides detailed instructions for deploying the Sophia AI Chatbot to GitHub and Render.

## Preparing Your Files for Deployment

The codebase has been organized with a minimal directory structure to make deployment easier:

```
sophia-chatbot/
├── app.py               # Application setup and configuration
├── main.py              # Entry point
├── models.py            # Database models
├── views.py             # Route handlers and business logic
├── responses.json       # Response templates
├── static/              # Static assets (CSS, JS, images)
├── templates/           # HTML templates
├── requirements.txt     # Dependencies
└── README.md            # Project documentation
```

## 1. GitHub Deployment

### 1.1 Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in to your account
2. Click the "+" icon in the top-right corner and select "New repository"
3. Name your repository (e.g., "sophia-chatbot")
4. Add a description (optional)
5. Choose visibility (public or private)
6. Click "Create repository"

### 1.2 Upload Your Files

#### Option 1: Using Git CLI
```bash
# Initialize Git repository in your project directory
git init

# Add all files to staging
git add .

# Commit the files
git commit -m "Initial commit"

# Add your GitHub repository as remote
git remote add origin https://github.com/your-username/sophia-chatbot.git

# Push to GitHub
git push -u origin main
```

#### Option 2: Using GitHub Web Interface
1. In your new repository, click "uploading an existing file"
2. Drag and drop your files or click to select files
3. After selecting all files, click "Commit changes"

## 2. Render Deployment

### 2.1 Create a Render Account

1. Go to [Render](https://render.com) and sign up for an account
2. Verify your email address

### 2.2 Connect Your GitHub Repository

1. In your Render dashboard, click "New" and select "Web Service"
2. Connect your GitHub account if you haven't already
3. Select your "sophia-chatbot" repository
4. Click "Connect"

### 2.3 Configure Your Web Service

Configure the following settings:
- **Name**: sophia-chatbot (or any name you prefer)
- **Environment**: Python 3
- **Region**: Choose the region closest to your users
- **Branch**: main (or your preferred branch)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app`

### 2.4 Add Environment Variables

Add the following environment variables:
1. Click on "Advanced" and then "Add Environment Variable"
2. Add these key-value pairs:
   - `SESSION_SECRET`: [generate a random string]
   - `DATABASE_URL`: [your PostgreSQL URL] *or leave empty for SQLite*
   - `TELEGRAM_BOT_TOKEN`: [your Telegram bot token] *optional*
   - `INSTAGRAM_USERNAME`: [your Instagram username] *optional*
   - `INSTAGRAM_PASSWORD`: [your Instagram password] *optional*

### 2.5 Deploy the Service

1. Click "Create Web Service"
2. Wait for the build and deployment process to complete
3. Once deployed, you'll receive a URL for your application

## 3. Setting Up the Database

### 3.1 PostgreSQL on Render (Recommended)

1. In your Render dashboard, click "New" and select "PostgreSQL"
2. Configure your database:
   - **Name**: sophia-db (or any name you prefer)
   - **PostgreSQL Version**: 14 or newer
   - **Region**: Same as your web service
3. Click "Create Database"
4. Once created, copy the "Internal Database URL"
5. Go to your web service's environment variables
6. Update the `DATABASE_URL` with the copied URL

### 3.2 Alternative: Use SQLite (Not Recommended for Production)

If you don't set a `DATABASE_URL`, the application will default to SQLite, which is fine for testing but not recommended for production.

## 4. Post-Deployment Steps

### 4.1 Create an Admin Account

1. Visit your deployed app at the Render URL
2. Register a new account with your preferred username/password
3. Connect to your database and set the `is_admin` field to `TRUE` for your user

### 4.2 Configure Telegram Bot (Optional)

If you want to use the Telegram bot functionality:

1. Talk to [BotFather](https://t.me/botfather) on Telegram to create a new bot
2. Get the bot token and add it to your environment variables as `TELEGRAM_BOT_TOKEN`
3. Set the webhook URL:
   ```
   https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url={YOUR_RENDER_URL}/api/telegram
   ```

### 4.3 Configure Instagram Bot (Optional)

If you want to use the Instagram bot functionality:

1. Create an Instagram account for your bot
2. Add the username and password to your environment variables
3. The bot will automatically process Instagram messages

## 5. Troubleshooting

### 5.1 Database Connection Issues

- Verify that your `DATABASE_URL` is correctly formatted
- Check Render logs for any connection errors
- Ensure your database is accepting connections from your web service

### 5.2 Application Errors

- Check Render logs for Python errors
- Verify all required environment variables are set
- Ensure dependencies are correctly installed

### 5.3 File Permissions

Make sure your upload directories have write permissions. If needed, the app will create them automatically, but on some systems, you might need to configure permissions manually.

## 6. Updating Your Application

After making changes to your codebase:

1. Push the changes to GitHub
2. Render will automatically detect the changes and redeploy your application

## 7. Monitoring and Scaling

- Render provides basic monitoring out of the box
- Consider upgrading to a paid plan for better performance and scaling options
- For high-traffic applications, consider adding a CDN for static assets

---

For additional help, refer to the [Render Documentation](https://render.com/docs) or the [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/).