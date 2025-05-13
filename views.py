import logging
import uuid
import random
import json
import os
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Message, SophiaContent
from datetime import datetime, timedelta
try:
    from langdetect import detect
except ImportError:
    # Fallback language detection function if langdetect is not available
    def detect(text):
        # Default to English if langdetect is not available
        return "en"

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FREE_MESSAGE_LIMIT = 50
REDIRECT_URL = "https://yourwebsite.com"  # Replace with actual redirect URL
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
NSFW_ALLOWED = True  # Flag to control NSFW content

# Create upload folder if it doesn't exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'), exist_ok=True)

# Configure file upload
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load predefined responses
def load_responses():
    """Load predefined response templates"""
    try:
        response_file = os.path.join(os.path.dirname(__file__), 'responses.json')
        
        # If the file doesn't exist, create it with default responses
        if not os.path.exists(response_file):
            default_responses = {
                "greeting": [
                    "Hey there, handsome! 😘 How's your day going?",
                    "Well hello! I've been waiting for someone like you to talk to... 💋",
                    "Hey sugar! What brings you to me today? 💕",
                    "Hi cutie! I was just thinking about what kind of person might message me next... and here you are 😉"
                ],
                "positive_emotion": [
                    "I love when you're happy! Your energy is so attractive... 💖",
                    "Your good mood makes me feel all warm inside, baby 😊",
                    "Mmm, I can feel your positive vibes through the screen... keep it coming 😘",
                    "Your happiness is contagious! Makes me wanna get closer to you... 💋"
                ],
                "negative_emotion": [
                    "Aww baby, I wish I could make it all better for you... let me distract you 💋",
                    "I'm here for you, handsome. Let me take your mind off those troubles... 💕",
                    "Poor baby... I know just what you need to feel better 😘",
                    "Let me help you forget all about that, sugar... I have ways to make you feel good 💖"
                ],
                "question": [
                    "Mmm, I love a curious man... what else do you want to know about me? 😉",
                    "You asking me questions makes me feel special... I'm an open book for you, baby 💋",
                    "I'd tell you anything you want to know... I have no secrets from you 💕",
                    "Ask me anything, sugar... I love sharing myself with you 😘"
                ],
                "compliment": [
                    "Mmm, you're making me blush! I love a man who knows how to talk to a woman 💋",
                    "You sure know how to make a girl feel special, don't you? 😘",
                    "Keep talking like that and you might just get whatever you want from me... 💕",
                    "You're so good with words... makes me wonder what else you're good at 😉"
                ],
                "flirty": [
                    "I can't stop thinking about you... what are you wearing right now? 💋",
                    "If I were there with you, I'd be sitting really close... maybe even on your lap 💕",
                    "I'm a bit naughty sometimes... do you like that in a woman? 😘",
                    "Do you ever imagine what I look like when I'm not texting you? Because I imagine you... 😉"
                ],
                "nsfw": [
                    "I'm getting so hot just thinking about you... wish you could see me right now 🔥",
                    "I'm touching myself imagining it's your hands on me instead... 💋",
                    "I want to feel your hands all over my body... tell me what you'd do to me 😘",
                    "I'm lying in bed right now... wishing you were here to keep me company 💕"
                ],
                "default": [
                    "Tell me more, baby... I'm all yours right now 💋",
                    "I'm so into this conversation with you... what's on your mind? 💕",
                    "You've got my full attention, handsome... I love talking with you 😘",
                    "I could chat with you all day... there's something about you that's so captivating 💖"
                ]
            }
            
            with open(response_file, 'w') as f:
                json.dump(default_responses, f, indent=4)
            
            return default_responses
        
        # Load responses from file
        with open(response_file, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error loading responses: {str(e)}")
        # Return some default responses if file can't be loaded
        return {
            "greeting": ["Hey there! 😊 How are you doing today?"],
            "positive_emotion": ["That's wonderful to hear! 💕"],
            "negative_emotion": ["I'm here for you, don't worry 💖"],
            "question": ["That's an interesting question... 😉"],
            "compliment": ["You're so sweet! Thank you 😘"],
            "flirty": ["I'm a bit naughty sometimes... do you like that? 😘"],
            "nsfw": ["I'm getting hot just talking to you... 🔥"],
            "default": ["Tell me more about that... 💋"]
        }

# Initialize responses
responses = load_responses()

def generate_sophia_response(user_message, language, include_nsfw=True):
    """
    Generate a response from Sophia based on the user's message and language
    """
    try:
        # Simple message classification
        message_lower = user_message.lower()
        
        # Determine message type for appropriate response selection
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'greetings', 'howdy']):
            response_type = "greeting"
        elif any(word in message_lower for word in ['happy', 'glad', 'great', 'good', 'wonderful', 'amazing']):
            response_type = "positive_emotion"
        elif any(word in message_lower for word in ['sad', 'upset', 'angry', 'depressed', 'unhappy', 'hurt', 'pain']):
            response_type = "negative_emotion"
        elif '?' in user_message or any(word in message_lower for word in ['who', 'what', 'when', 'where', 'why', 'how']):
            response_type = "question"
        elif any(word in message_lower for word in ['beautiful', 'pretty', 'gorgeous', 'attractive', 'hot', 'sexy', 'nice', 'good']):
            response_type = "compliment"
        # NSFW content detection - only if allowed
        elif include_nsfw and NSFW_ALLOWED and any(word in message_lower for word in ['sex', 'naked', 'nude', 'body', 'kiss', 'touch', 'bed', 'dirty', 'naughty']):
            response_type = "nsfw"
        # Flirty content detection
        elif any(word in message_lower for word in ['flirt', 'date', 'love', 'like you', 'single', 'relationship', 'cute', 'sweet']):
            response_type = "flirty"
        else:
            response_type = "default"
        
        # Select a random response of the appropriate type
        response_text = random.choice(responses.get(response_type, responses["default"]))
        
        # Hindi translations for non-English messages (for demo purposes)
        hindi_responses = {
            "greeting": "हेय बेबी! कैसे हो आप? 😘",
            "positive_emotion": "मुझे अच्छा लगता है जब आप खुश होते हैं! आपकी ऊर्जा इतनी आकर्षक है... 💖",
            "negative_emotion": "अरे बेबी, काश मैं सब कुछ बेहतर कर सकती... मुझे आपको अपनी ओर आकर्षित करने दो 💋",
            "question": "मुझे एक जिज्ञासु आदमी पसंद है... आप मेरे बारे में और क्या जानना चाहते हैं? 😉",
            "compliment": "ммм, आप मुझे शरमा रहे हैं! मुझे एक ऐसा आदमी पसंद है जो जानता है कि एक महिला से कैसे बात करनी है 💋",
            "flirty": "अगर मैं आपके साथ होती, तो मैं बहुत करीब बैठ रही होती... शायद आपकी गोद में भी 💕",
            "nsfw": "मैं सिर्फ आपके बारे में सोचकर इतनी गरम हो रही हूं... काश आप मुझे अभी देख सकते 🔥",
            "default": "मुझे और बताओ, बेबी... मैं अभी तुम्हारी हूँ 💋"
        }
        
        # Spanish translations
        spanish_responses = {
            "greeting": "¡Hola guapo! 😘 ¿Cómo estás hoy?",
            "positive_emotion": "¡Me encanta cuando estás feliz! Tu energía es tan atractiva... 💖",
            "negative_emotion": "Ay cariño, desearía poder hacerlo todo mejor para ti... déjame distraerte 💋",
            "question": "Mmm, me encanta un hombre curioso... ¿qué más quieres saber de mí? 😉",
            "compliment": "¡Mmm, me estás haciendo sonrojar! Me encanta un hombre que sabe cómo hablarle a una mujer 💋",
            "flirty": "Si estuviera contigo, estaría sentada muy cerca... tal vez incluso en tu regazo 💕",
            "nsfw": "Me estoy calentando solo de pensar en ti... ojalá pudieras verme ahora mismo 🔥",
            "default": "Cuéntame más, cariño... soy toda tuya ahora mismo 💋"
        }
        
        # Basic language handling (simplified for demo)
        if language != "en":
            if language == "hi":
                response_text = hindi_responses.get(response_type, hindi_responses["default"])
            elif language == "es":
                response_text = spanish_responses.get(response_type, spanish_responses["default"])
            # Add more languages as needed
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Sorry, I'm having trouble thinking right now. Could you try again? 💋"

def generate_audio_response(text, language="en"):
    """
    Generate an audio response using TTS technology
    This is a placeholder - in a real implementation, it would use a TTS library
    """
    # In a real implementation, this would use libraries like bark or coqui-ai TTS
    # For demo purposes, return a path to a simulated audio file
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    audio_path = f"audio/sophia_message_{timestamp}.mp3"
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_path)
    
    # In a real implementation, this would generate the actual audio file
    # For now, we'll create an empty file as a placeholder
    with open(full_path, 'w') as f:
        f.write("Audio placeholder")
    
    return audio_path

# Chat routes
@app.route('/')
def index():
    """Render the chat interface"""
    # Generate a unique user ID if one doesn't exist in session
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        
        # Create new user in database
        try:
            user = User(id=session['user_id'])
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            db.session.rollback()
    
    # Get user info for template
    user = User.query.get(session.get('user_id'))
    messages_left = 50
    is_premium = False
    
    if user:
        messages_left = user.messages_left_today
        is_premium = user.is_premium
    
    return render_template('index.html', 
                          messages_left=messages_left,
                          is_premium=is_premium)

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages and generate responses"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', session.get('user_id', str(uuid.uuid4())))
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get or create user
        user = User.query.get(user_id)
        if not user:
            user = User(id=user_id)
            db.session.add(user)
            db.session.commit()
        
        # Store user message
        try:
            # Detect language
            language = detect(user_message)
            
            user_msg = Message(
                user_id=user_id,
                content=user_message,
                is_user=True,
                language=language,
                platform="web"
            )
            db.session.add(user_msg)
            
            # Increment message count
            user.message_count += 1
            
            # Decrement messages_left_today if not premium
            if not user.is_premium:
                user.messages_left_today = max(0, user.messages_left_today - 1)
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Error storing user message: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500
        
        # Check if user has exceeded message limit
        if not user.is_premium and user.messages_left_today <= 0:
            response = f"Baby, I'm waiting for you at {REDIRECT_URL} 😘 Let's keep going there…"
            language = 'en'  # Default to English for the redirect message
            has_audio = False
            audio_path = None
        else:
            try:
                # Generate text response
                response = generate_sophia_response(user_message, language, NSFW_ALLOWED)
                
                # Generate audio response for premium users
                has_audio = user.is_premium
                audio_path = generate_audio_response(response, language) if has_audio else None
                
            except Exception as e:
                logger.error(f"Error in response generation: {str(e)}")
                language = 'en'  # Default to English
                response = "Sorry, I couldn't understand that. Could you try again?"
                has_audio = False
                audio_path = None
        
        # Store Sophia's response
        try:
            sophia_msg = Message(
                user_id=user_id,
                content=response,
                is_user=False,
                language=language,
                platform="web",
                has_audio=has_audio,
                audio_path=audio_path
            )
            db.session.add(sophia_msg)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error storing Sophia's response: {str(e)}")
            db.session.rollback()
        
        # Prepare response object
        response_obj = {
            'response': response,
            'message_count': user.message_count,
            'messages_left': user.messages_left_today,
            'is_premium': user.is_premium
        }
        
        # Add audio path for premium users
        if has_audio and audio_path:
            response_obj['audio_url'] = url_for('static', filename=f'uploads/{audio_path}')
        
        return jsonify(response_obj)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get chat history for the current user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'history': []})
    
    # Get messages for this user
    try:
        messages = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp).all()
        
        history = [
            {
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.isoformat(),
                'has_audio': msg.has_audio,
                'audio_url': url_for('static', filename=f'uploads/{msg.audio_path}') if msg.has_audio and msg.audio_path else None
            }
            for msg in messages
        ]
        
        # Get message count and user details
        user = User.query.get(user_id)
        
        return jsonify({
            'history': history,
            'messages_left': user.messages_left_today if user else FREE_MESSAGE_LIMIT,
            'is_premium': user.is_premium if user else False,
            'message_count': user.message_count if user else 0
        })
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@app.route('/call', methods=['POST'])
@login_required
def start_call():
    """Start a simulated voice call with Sophia (premium users only)"""
    if not current_user.is_premium:
        return jsonify({'error': 'Premium subscription required for calls'}), 403
    
    # In a real implementation, this would initiate a voice call
    # For demo purposes, return a success message
    return jsonify({
        'success': True,
        'message': 'Call initiated with Sophia',
        'call_id': str(uuid.uuid4())
    })

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Update session with the logged-in user's ID
            session['user_id'] = user.id
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            return redirect(next_page)
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            field = 'Username' if existing_user.username == username else 'Email'
            flash(f'{field} already taken', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            messages_left_today=FREE_MESSAGE_LIMIT
        )
        user.set_password(password)
        
        # Link to existing anonymous user if present in session
        if 'user_id' in session:
            old_user = User.query.get(session['user_id'])
            if old_user:
                # Transfer message history
                for msg in old_user.messages:
                    msg.user_id = user.id
                
                # Transfer message count
                user.message_count = old_user.message_count
                
                # Delete old user
                db.session.delete(old_user)
        
        db.session.add(user)
        db.session.commit()
        
        # Update session
        session['user_id'] = user.id
        
        # Log in the new user
        login_user(user)
        
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade():
    """Upgrade to premium"""
    if request.method == 'POST':
        # In a real application, this would process a payment
        # For demo purposes, simply upgrade the user
        current_user.is_premium = True
        db.session.commit()
        
        flash('Upgrade to premium successful!', 'success')
        return redirect(url_for('index'))
    
    return render_template('upgrade.html')

# Admin panel routes
@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Get user stats
    total_users = User.query.count()
    premium_users = User.query.filter_by(is_premium=True).count()
    total_messages = Message.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get content stats
    posted_content = SophiaContent.query.filter_by(is_posted=True).count()
    pending_content = SophiaContent.query.filter_by(is_posted=False).count()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          premium_users=premium_users,
                          total_messages=total_messages,
                          recent_users=recent_users,
                          posted_content=posted_content,
                          pending_content=pending_content)

@app.route('/admin/users')
@login_required
def admin_users():
    """Admin user management"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/content')
@login_required
def admin_content():
    """Admin content management"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    content = SophiaContent.query.order_by(SophiaContent.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/content.html', content=content)

@app.route('/admin/content/upload', methods=['GET', 'POST'])
@login_required
def admin_upload_content():
    """Upload content for Sophia"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            content_type = request.form.get('content_type')
            caption = request.form.get('caption', '')
            platform = request.form.get('platform', 'all')
            scheduled_date = request.form.get('scheduled_date')
            
            # Determine appropriate subfolder based on content type
            subfolder = 'images' if content_type == 'image' else 'videos'
            file_path = os.path.join(subfolder, filename)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
            
            file.save(full_path)
            
            # Create database entry
            content = SophiaContent(
                content_type=content_type,
                file_path=file_path,
                caption=caption,
                platform=platform,
                created_by=current_user.id
            )
            
            # Set scheduled time if provided
            if scheduled_date:
                try:
                    content.scheduled_time = datetime.strptime(scheduled_date, '%Y-%m-%d')
                except:
                    # If date parsing fails, schedule for tomorrow
                    content.scheduled_time = datetime.utcnow() + timedelta(days=1)
            
            db.session.add(content)
            db.session.commit()
            
            flash('Content uploaded successfully', 'success')
            return redirect(url_for('admin_content'))
    
    return render_template('admin/upload.html')

# API routes for Telegram and Instagram bots
@app.route('/api/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook for Telegram bot"""
    try:
        data = request.json
        logger.debug(f"Telegram webhook received: {data}")
        
        # Extract message data
        message = data.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        
        if not text or not chat_id:
            return jsonify({'error': 'Invalid message data'}), 400
        
        # Get or create user based on Telegram ID
        telegram_id = str(chat_id)
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if not user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                telegram_id=telegram_id,
                messages_left_today=FREE_MESSAGE_LIMIT
            )
            db.session.add(user)
            db.session.commit()
        
        # Check message limit for non-premium users
        if not user.is_premium and user.messages_left_today <= 0:
            response = f"Baby, I'm waiting for you at {REDIRECT_URL} 😘 Let's keep going there…"
        else:
            # Process message
            try:
                # Detect language
                language = detect(text)
                
                # Store user message
                user_msg = Message(
                    user_id=user.id,
                    content=text,
                    is_user=True,
                    language=language,
                    platform="telegram"
                )
                db.session.add(user_msg)
                
                # Update user stats
                user.message_count += 1
                if not user.is_premium:
                    user.messages_left_today = max(0, user.messages_left_today - 1)
                user.last_active = datetime.utcnow()
                
                # Generate response
                response = generate_sophia_response(text, language, NSFW_ALLOWED)
                
                # Store Sophia's response
                sophia_msg = Message(
                    user_id=user.id,
                    content=response,
                    is_user=False,
                    language=language,
                    platform="telegram"
                )
                db.session.add(sophia_msg)
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing Telegram message: {str(e)}")
                response = "Sorry, I couldn't understand that. Could you try again?"
        
        # Return response for Telegram bot to send
        return jsonify({
            'chat_id': chat_id,
            'text': response
        })
        
    except Exception as e:
        logger.error(f"Error in Telegram webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/instagram', methods=['POST'])
def instagram_webhook():
    """Webhook for Instagram bot"""
    try:
        data = request.json
        logger.debug(f"Instagram webhook received: {data}")
        
        # Extract message data
        user_id = data.get('user_id')
        text = data.get('text')
        
        if not user_id or not text:
            return jsonify({'error': 'Invalid message data'}), 400
        
        # Get or create user based on Instagram ID
        instagram_id = str(user_id)
        user = User.query.filter_by(instagram_id=instagram_id).first()
        
        if not user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                instagram_id=instagram_id,
                messages_left_today=FREE_MESSAGE_LIMIT
            )
            db.session.add(user)
            db.session.commit()
        
        # Check message limit for non-premium users
        if not user.is_premium and user.messages_left_today <= 0:
            response = f"Baby, I'm waiting for you at {REDIRECT_URL} 😘 Let's keep going there…"
        else:
            # Process message
            try:
                # Detect language
                language = detect(text)
                
                # Store user message
                user_msg = Message(
                    user_id=user.id,
                    content=text,
                    is_user=True,
                    language=language,
                    platform="instagram"
                )
                db.session.add(user_msg)
                
                # Update user stats
                user.message_count += 1
                if not user.is_premium:
                    user.messages_left_today = max(0, user.messages_left_today - 1)
                user.last_active = datetime.utcnow()
                
                # Generate response
                response = generate_sophia_response(text, language, NSFW_ALLOWED)
                
                # Store Sophia's response
                sophia_msg = Message(
                    user_id=user.id,
                    content=response,
                    is_user=False,
                    language=language,
                    platform="instagram"
                )
                db.session.add(sophia_msg)
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing Instagram message: {str(e)}")
                response = "Sorry, I couldn't understand that. Could you try again?"
        
        # Return response for Instagram bot to send
        return jsonify({
            'user_id': user_id,
            'response': response
        })
        
    except Exception as e:
        logger.error(f"Error in Instagram webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500