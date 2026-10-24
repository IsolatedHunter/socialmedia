from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from google.cloud import storage
import uuid
from werkzeug.exceptions import HTTPException



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Use the DATABASE_URL environment variable if it exists, otherwise fall back to local SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

friends_table = db.Table('friends_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    venmo_handle = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    updates = db.relationship('Update', backref='author', lazy=True, cascade="all, delete-orphan", order_by="desc(Update.timestamp)")
    friends = db.relationship('User', secondary=friends_table, primaryjoin=(friends_table.c.user_id == id), secondaryjoin=(friends_table.c.friend_id == id), backref=db.backref('friended_by', lazy='dynamic'), lazy='dynamic')

    def is_friend(self, user):
        return self.friends.filter(friends_table.c.friend_id == user.id).count() > 0

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    photo = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    error_code = db.Column(db.String(10))
    error_message = db.Column(db.Text)
    path = db.Column(db.String(255))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        location = request.form.get('location')
        photo_file = request.files.get('photo')
        
        photo_path_or_url = None
        
        if photo_file and photo_file.filename != '':
            # Generate a unique filename to prevent overwriting
            ext = photo_file.filename.rsplit('.', 1)[1].lower() if '.' in photo_file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            
            gcs_bucket_name = os.environ.get('GCS_BUCKET_NAME')
            
            if gcs_bucket_name:
                # SCALABLE MODE: Upload to Google Cloud Storage
                storage_client = storage.Client()
                bucket = storage_client.bucket(gcs_bucket_name)
                blob = bucket.blob(unique_filename)
                
                # Upload the file directly from memory
                blob.upload_from_file(photo_file, content_type=photo_file.content_type)
                
                # Make it publicly viewable and get the URL
                blob.make_public()
                photo_path_or_url = blob.public_url
            else:
                # LOCAL MODE: Fallback for local testing
                secure_name = secure_filename(unique_filename)
                photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_name))
                photo_path_or_url = secure_name # Just save the filename
            
        if content:
            new_update = Update(content=content, location=location, photo=photo_path_or_url, author=current_user)
            db.session.add(new_update)
            db.session.commit()
            return redirect(url_for('index'))
            
    friend_ids = [f.id for f in current_user.friends]
    feed_updates = Update.query.filter(Update.user_id.in_(friend_ids + [current_user.id])).order_by(Update.timestamp.desc()).all()
    incoming_requests = FriendRequest.query.filter_by(receiver_id=current_user.id).all()
    
    return render_template('index.html', updates=feed_updates, incoming_requests=incoming_requests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        venmo = request.form.get('venmo_handle')
        if venmo and venmo.startswith('@'): venmo = venmo[1:]
        
        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'error')
            return redirect(request.url) # Reloads page keeping the invite parameter
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        is_first_user = User.query.count() == 0
        
        new_user = User(username=username, password=hashed_pw, venmo_handle=venmo, is_admin=is_first_user)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        
        # If they came from an invite link, redirect them back to it to auto-send the request
        invite_target = request.args.get('invite')
        if invite_target:
            return redirect(url_for('invite', username=invite_target))
            
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            invite_target = request.args.get('invite')
            if invite_target:
                return redirect(url_for('invite', username=invite_target))
                
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'error')
            
    return render_template('login.html')

# --- NEW INVITE ROUTE ---
@app.route('/invite/<username>')
def invite(username):
    target_user = User.query.filter_by(username=username).first()
    
    if not target_user:
        flash("That invite link is invalid.", "error")
        return redirect(url_for('index'))
        
    # If they aren't logged in, send them to register but keep the target username in the URL
    if not current_user.is_authenticated:
        flash(f"Create an account or log in to connect with {username}!", "success")
        return redirect(url_for('register', invite=username))
        
    # If they are logged in, process the friend request
    if target_user == current_user:
        flash("You can't send an invite link to yourself!", "error")
        return redirect(url_for('index'))
        
    if current_user.is_friend(target_user):
        flash(f"You are already friends with {username}.", "error")
        return redirect(url_for('index'))
        
    existing_req = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=target_user.id).first()
    if existing_req:
        flash(f"You already sent a request to {username}.", "error")
    else:
        new_req = FriendRequest(sender_id=current_user.id, receiver_id=target_user.id)
        db.session.add(new_req)
        db.session.commit()
        flash(f"Friend request automatically sent to {username}!", "success")
        
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/send_request', methods=['POST'])
@login_required
def send_request():
    target_username = request.form.get('friend_username').strip()
    target_user = User.query.filter_by(username=target_username).first()
    
    if not target_user:
        flash('User not found.', 'error')
    elif target_user == current_user:
        flash('You cannot add yourself.', 'error')
    elif current_user.is_friend(target_user):
        flash('You are already connected.', 'error')
    else:
        existing_req = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=target_user.id).first()
        if existing_req:
            flash('Request already sent.', 'error')
        else:
            new_req = FriendRequest(sender_id=current_user.id, receiver_id=target_user.id)
            db.session.add(new_req)
            db.session.commit()
            flash(f'Friend request sent to {target_user.username}!', 'success')
            
    return redirect(url_for('index'))

@app.route('/handle_request/<int:req_id>/<action>', methods=['POST'])
@login_required
def handle_request(req_id, action):
    freq = FriendRequest.query.get_or_404(req_id)
    if freq.receiver_id != current_user.id: abort(403)
        
    if action == 'accept':
        current_user.friends.append(freq.sender)
        freq.sender.friends.append(current_user)
        db.session.delete(freq)
        db.session.commit()
        flash(f'You are now connected with {freq.sender.username}!', 'success')
    elif action == 'decline':
        db.session.delete(freq)
        db.session.commit()
        flash('Request declined.', 'success')
        
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        new_password = request.form.get('password')
        new_venmo = request.form.get('venmo_handle')
        
        if new_venmo:
            if new_venmo.startswith('@'): new_venmo = new_venmo[1:]
            current_user.venmo_handle = new_venmo
        else:
            current_user.venmo_handle = None
            
        if new_username and new_username != current_user.username:
            # Check for collision before changing
            if User.query.filter_by(username=new_username).first():
                flash('That username is already taken.', 'error')
                return redirect(url_for('settings'))
            current_user.username = new_username
            
        if new_password:
            current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('settings'))
        
    return render_template('settings.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin: abort(403)
        
    if request.method == 'POST':
        action = request.form.get('action')
        item_id = request.form.get('item_id')
        
        if action == 'delete_user':
            u = User.query.get(item_id)
            if u and u.id != current_user.id:
                db.session.delete(u)
                db.session.commit()
                flash('User deleted.', 'success')
        elif action == 'delete_update':
            upd = Update.query.get(item_id)
            if upd:
                db.session.delete(upd)
                db.session.commit()
                flash('Post deleted.', 'success')
        elif action == 'generate_demo_data':
            demo_data = [
                {'user': 'Alice', 'venmo': 'alice-test'},
                {'user': 'Bob', 'venmo': 'bob-venmo'},
                {'user': 'Charlie', 'venmo': 'charlie-money'}
            ]
            created_users = []
            for d in demo_data:
                user = User.query.filter_by(username=d['user']).first()
                if not user:
                    hashed_pw = generate_password_hash('password123', method='pbkdf2:sha256')
                    user = User(username=d['user'], password=hashed_pw, venmo_handle=d['venmo'])
                    db.session.add(user)
                created_users.append(user)
            db.session.commit()
            
            a, b, c = created_users[0], created_users[1], created_users[2]
            if not a.is_friend(b):
                a.friends.append(b)
                b.friends.append(a)
            if not b.is_friend(c):
                b.friends.append(c)
                c.friends.append(b)
            db.session.commit()
            
            demo_posts = [(a, "Studying for my physics exam...", "Campus Library"), (b, "Anyone grabbing food?", "Student Union"), (c, "Great weather today", "Main Plaza")]
            for author, content, loc in demo_posts:
                if not Update.query.filter_by(content=content, user_id=author.id).first():
                    db.session.add(Update(content=content, location=loc, author=author))
            db.session.commit()
            flash('Demo accounts generated! Log in with Alice, Bob, or Charlie (Password: password123)', 'success')
                
        return redirect(url_for('admin'))

    return render_template('admin.html', users=User.query.all(), updates=Update.query.order_by(Update.timestamp.desc()).all())

@app.route('/favicon.ico')
@app.route('/apple-touch-icon.png')
@app.route('/apple-touch-icon-precomposed.png')
def serve_icons():
    # Serves the icon from your static folder for all standard browser requests
    return send_from_directory(app.static_folder, 'icon-192.png', mimetype='image/png')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        code = e.code
        message = e.description
    else:
        code = 500
        message = str(e) or "An unexpected internal server error occurred."

    # Save the error to the database
    try:
        new_error = ErrorLog(error_code=str(code), error_message=message, path=request.path)
        db.session.add(new_error)
        db.session.commit()
    except Exception:
        db.session.rollback() # Prevent complete failure if the database itself is the issue

    return render_template('error.html', error_code=code, error_message=message), code

# --- ADMIN ERROR LOGS ROUTE ---
@app.route('/admin/errors', methods=['GET', 'POST'])
@login_required
def admin_errors():
    if not current_user.is_admin:
        abort(403)
        
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'clear_logs':
            ErrorLog.query.delete()
            db.session.commit()
            flash('All error logs have been cleared.', 'success')
            return redirect(url_for('admin_errors'))
            
    logs = ErrorLog.query.order_by(ErrorLog.timestamp.desc()).all()
    return render_template('admin_errors.html', logs=logs)

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)