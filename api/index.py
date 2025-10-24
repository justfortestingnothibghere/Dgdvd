import os
import requests
from datetime import datetime
from flask import Flask, request, Response, jsonify, abort
from TeraboxDL import TeraboxDL  # Import the package

app = Flask(__name__)

# Load TeraBox cookie from env (set in Vercel dashboard)
COOKIE = os.getenv('TERABOX_COOKIE')
if not COOKIE:
    abort(500, 'TERABOX_COOKIE env var not set!')

terabox = TeraboxDL(COOKIE)

# Admin password from env
ADMIN_PASS = os.getenv('ADMIN_PASS', 'admin123')

# In-memory user data (password -> user dict). Production: Use DB like Vercel Postgres
# Example: {'arman': {'exp': '2025-12-31', 'downloads': 0, 'calls': 0, 'premium': False, 'cooldown_until': None}}
passwords = {
    'arman': {'exp': '2025-12-31', 'downloads': 0, 'calls': 0, 'premium': False, 'cooldown_until': None, 'userid': 'user1'}
}
# Limits example: free=5 downloads/day, premium=unlimited
DAILY_LIMIT_FREE = 5
DAILY_LIMIT_PREMIUM = float('inf')
COOLDOWN_SEC = 60  # 1 min between calls for free users

def check_user_limits(password):
    if password not in passwords:
        return False, 'Invalid password'
    user = passwords[password]
    now = datetime.now()
    # Check expiration
    if user['exp'] and now.strftime('%Y-%m-%d') > user['exp']:
        return False, 'Password expired'
    # Check cooldown
    if user['cooldown_until'] and now.timestamp() < user['cooldown_until']:
        return False, 'Cooldown active'
    # Check daily limit
    today = now.strftime('%Y-%m-%d')
    if user.get('last_date') != today:
        user['daily_downloads'] = 0
        user['last_date'] = today
    limit = DAILY_LIMIT_PREMIUM if user['premium'] else DAILY_LIMIT_FREE
    if user['daily_downloads'] >= limit:
        return False, 'Daily limit reached'
    user['calls'] += 1
    return True, 'OK'

def log_action(action, details=''):
    print(f"[{datetime.now()}] {action}: {details}")  # Console log, production: Send to DB/file/Slack

@app.route('/TeraBox/Download/Api/v1/safensecure/fast/Team-X-Og/<password>/', methods=['GET'])
def download_file(password):
    ok, msg = check_user_limits(password)
    if not ok:
        log_action('API_CALL_FAILED', f"Password: {password}, Reason: {msg}")
        abort(400, msg)
    
    user = passwords[password]
    dl_url = request.args.get('dl')
    file_type = request.args.get('file') or request.args.get('video') or 'file'  # Optional, for logging
    
    if not dl_url:
        abort(400, 'Missing dl param (TeraBox URL)')
    
    log_action('API_CALL_START', f"Password: {password}, URL: {dl_url[:50]}..., Type: {file_type}")
    
    # Get file info from TeraBox (public links only; for password-protected, add POST pwd to Terabox API)
    file_info = terabox.get_file_info(dl_url)
    if "error" in file_info:
        log_action('DOWNLOAD_FAILED', f"Password: {password}, Error: {file_info['error']}")
        return jsonify({'error': file_info['error']}), 400
    
    filename = file_info['file_name']
    direct_url = file_info['download_link']
    filesize = file_info['file_size']
    
    # Update user stats
    user['downloads'] += 1
    user['daily_downloads'] += 1
    user['cooldown_until'] = now.timestamp() + COOLDOWN_SEC if not user['premium'] else None
    log_action('STATS_UPDATE', f"Password: {password}, Downloads: {user['downloads']}, Size: {filesize}")
    
    # Stream download (proxy to avoid full download on server)
    try:
        r = requests.get(direct_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
    except Exception as e:
        log_action('STREAM_FAILED', f"Password: {password}, Error: {str(e)}")
        return jsonify({'error': 'Download link invalid'}), 500
    
    def generate():
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
    
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': r.headers.get('content-type', 'application/octet-stream'),
        'Content-Length': str(r.headers.get('content-length', 0))
    }
    
    log_action('DOWNLOAD_SUCCESS', f"Password: {password}, File: {filename}")
    return Response(generate(), headers=headers)

@app.route('/admin/pas/<admin_pass>/<new_pass>')
def admin_create_pass(admin_pass, new_pass):
    exp_str = request.args.get('exp')  # e.g., ?exp=2025-11-10 (format YYYY-MM-DD)
    if admin_pass != ADMIN_PASS:
        log_action('ADMIN_ACCESS_DENIED', f"Attempted: {admin_pass}")
        abort(401, 'Invalid admin password')
    
    if not exp_str:
        abort(400, 'Missing exp param (YYYY-MM-DD)')
    
    # Validate exp format (simple)
    try:
        datetime.strptime(exp_str, '%Y-%m-%d')
    except:
        abort(400, 'Invalid exp format')
    
    # Add new password (premium=False by default; add ?premium=true for premium)
    is_premium = request.args.get('premium') == 'true'
    passwords[new_pass] = {
        'exp': exp_str,
        'downloads': 0,
        'calls': 0,
        'premium': is_premium,
        'cooldown_until': None,
        'userid': new_pass,  # Or generate UUID
        'last_date': None,
        'daily_downloads': 0
    }
    
    log_action('ADMIN_PASSWORD_CREATED', f"New: {new_pass}, Exp: {exp_str}, Premium: {is_premium}")
    return jsonify({'success': True, 'message': f'Password {new_pass} created, expires {exp_str}'})

# Admin dashboard route (basic JSON view of users/logs - expand with auth)
@app.route('/admin/dashboard')
def admin_dashboard():
    if request.args.get('pass') != ADMIN_PASS:
        abort(401)
    log_action('ADMIN_DASHBOARD_VIEW', 'Accessed')
    return jsonify({
        'users': passwords,
        'total_calls': sum(u['calls'] for u in passwords.values()),
        'total_downloads': sum(u['downloads'] for u in passwords.values())
    })

if __name__ == '__main__':
    app.run(debug=True)
