"""
AI Fit Pro API Gateway
Main application entry point with authentication and routing to microservices.
Primarily serves the JSON API used by the Next.js frontend, while keeping
legacy routes available as redirects for compatibility.
"""

import os
import sys
import time
import secrets
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

PROJECT_ROOT_EARLY = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT_EARLY / '.env')

from flask import (
    Flask, render_template, redirect, request, Response,
    url_for, flash, jsonify, session, g,
    current_app, has_app_context,
)
from flask_cors import CORS
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)
from authlib.integrations.flask_client import OAuth
from sqlalchemy.exc import InterfaceError, OperationalError
from werkzeug.utils import secure_filename
import requests as http_requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.database.models import (
    db,
    User,
    ScanHistory,
    WorkoutSession,
    Achievement,
    APIKey,
    init_db,
)
from gateway.auth_jwt import generate_tokens, decode_token, jwt_required, jwt_optional
from gateway.nutri_ai_lite import extract_nutrition_from_image, calculate_health_metrics, generate_score

login_manager = LoginManager()
oauth = OAuth()

HOP_BY_HOP_HEADERS = {
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailers', 'transfer-encoding', 'upgrade',
}


def _is_huggingface_runtime() -> bool:
    return os.environ.get('FITLIFE_RUNTIME') == 'huggingface'


def _runtime_data_root() -> Path:
    if _is_huggingface_runtime():
        return Path('/tmp/fitlife')
    return PROJECT_ROOT / 'data'


UPLOAD_FOLDER = _runtime_data_root() / 'uploads'
TRANSIENT_DB_ERRORS = (OperationalError, InterfaceError)


def _service_urls():
    return (
        os.environ.get('NUTRI_AI_URL', 'http://localhost:5001').rstrip('/'),
        os.environ.get('MUSCLE_AI_URL', 'http://localhost:5002').rstrip('/'),
    )


def _frontend_url() -> str:
    return os.environ.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')


def _is_huggingface_space_request() -> bool:
    host = request.host.lower() if request else ''
    return host.endswith('.hf.space') or _is_huggingface_runtime()


def _public_origin() -> str:
    forwarded_proto = request.headers.get('x-forwarded-proto', '').split(',')[0].strip()
    forwarded_host = request.headers.get('x-forwarded-host', '').split(',')[0].strip()
    host = forwarded_host or request.host

    if forwarded_proto and host:
        return f"{forwarded_proto}://{host}"
    if host.endswith('.hf.space'):
        return f"https://{host}"
    return request.host_url.rstrip('/')


def _space_root_html() -> str:
    frontend = _frontend_url()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Fit Pro API</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe5;
      --panel: rgba(255,255,255,0.82);
      --text: #18212b;
      --muted: #5d6670;
      --accent: #ef6f2d;
      --border: rgba(24,33,43,0.08);
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", system-ui, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(239,111,45,0.18), transparent 34%),
        linear-gradient(135deg, #eef5ef 0%, var(--bg) 52%, #f8e8db 100%);
      color: var(--text);
      display: grid;
      place-items: center;
      padding: 24px;
    }}
    .card {{
      width: min(760px, 100%);
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: 0 24px 90px rgba(24,33,43,0.1);
      padding: 32px;
      backdrop-filter: blur(12px);
    }}
    .eyebrow {{
      display: inline-block;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(239,111,45,0.1);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 16px 0 12px;
      font-size: clamp(32px, 6vw, 52px);
      line-height: 1.02;
    }}
    p {{
      margin: 0 0 24px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 26px;
    }}
    a {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 12px 18px;
      border-radius: 14px;
      font-weight: 600;
      text-decoration: none;
      color: var(--text);
      border: 1px solid var(--border);
      background: white;
    }}
    a.primary {{
      background: var(--accent);
      color: white;
      border-color: transparent;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      display: grid;
      gap: 8px;
    }}
    code {{
      color: var(--text);
      background: rgba(24,33,43,0.06);
      padding: 2px 6px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <main class="card">
    <span class="eyebrow">AI Fit Pro Backend</span>
    <h1>AI fitness API is live.</h1>
    <p>This Hugging Face Space serves the AI Fit Pro gateway used by the public frontend for auth, nutrition OCR, workout analysis, and coach chat.</p>
    <div class="links">
      <a class="primary" href="{frontend}" target="_blank" rel="noreferrer">Open Frontend</a>
      <a href="/health" target="_blank" rel="noreferrer">Health Check</a>
      <a href="/api/v1/health" target="_blank" rel="noreferrer">API Health</a>
    </div>
    <ul>
      <li>Frontend app: <code>{frontend}</code></li>
      <li>Nutrition OCR endpoint: <code>/api/v1/nutri-ai/upload</code></li>
      <li>Workout analysis endpoint: <code>/api/v1/muscle-ai/upload</code></li>
      <li>Coach chat endpoint: <code>/api/v1/ana/chat</code></li>
    </ul>
  </main>
</body>
</html>"""


def _proxy_request(target_url: str) -> Response:
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS and k.lower() != 'host'
    }
    try:
        upstream = http_requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            allow_redirects=False,
            timeout=60,
        )
        excluded = {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}
        response_headers = [
            (k, v) for k, v in upstream.headers.items() if k.lower() not in excluded
        ]
        return Response(upstream.content, status=upstream.status_code, headers=response_headers)
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': 'Service unavailable', 'details': str(e)}), 503


def _absolute_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith('http://') or path.startswith('https://'):
        return path
    return f"{_public_origin()}{path}"


def _with_db_retry(operation_name: str, callback, *, retries: int = 1, base_delay: float = 0.8):
    last_error = None
    for attempt in range(retries + 1):
        try:
            return callback()
        except TRANSIENT_DB_ERRORS as exc:
            last_error = exc
            db.session.rollback()
            if attempt >= retries:
                raise
            app_logger = current_app.logger if has_app_context() else None
            if app_logger:
                app_logger.warning(
                    'Transient database error during %s (attempt %s/%s): %s',
                    operation_name,
                    attempt + 1,
                    retries + 1,
                    exc,
                )
            time.sleep(base_delay * (attempt + 1))
    raise last_error


def _save_workout_session(user_id: int | None, exercise_type: str, result: dict) -> None:
    if not user_id:
        return

    movement = result.get('movement_assessment') or {}
    form_consistency = float(movement.get('form_consistency', 0) or 0) * 10
    depth_consistency = float(movement.get('depth_consistency', 0) or 0) * 10

    session = WorkoutSession(
        user_id=user_id,
        exercise_type=exercise_type,
        form_score=float(result.get('form_score', 0) or 0),
        reps=int(result.get('reps', 0) or 0),
        duration_seconds=int(float(result.get('duration_seconds', 0) or 0)),
        form_quality=float(movement.get('form_quality', 0) or 0) * 10,
        depth_quality=float(movement.get('depth_quality', 0) or 0) * 10,
        consistency=round((form_consistency + depth_consistency) / 2, 1),
        feedback=result.get('feedback') or result.get('recommendations') or [],
        video_path=result.get('video_url'),
    )
    def persist():
        db.session.add(session)
        db.session.commit()

    _with_db_retry('save-workout-session', persist)


def _extract_recommendations(explanation: str) -> list[str]:
    if not explanation:
        return []

    marker = 'RECOMMENDATIONS:'
    upper = explanation.upper()
    marker_index = upper.find(marker)
    if marker_index < 0:
        return []

    section = explanation[marker_index + len(marker):].strip()
    if not section:
        return []

    recommendations: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip().lstrip('-*').strip()
        if not line:
            continue
        recommendations.append(line)
    return recommendations[:6]


def _save_scan_history(user_id: int | None, payload: dict) -> None:
    if not user_id:
        return

    def persist():
        user = db.session.get(User, user_id)
        if not user:
            return

        nutrition_info = payload.get('nutrition_info') or {}
        product_name = (
            payload.get('product_name')
            or payload.get('source_name')
            or nutrition_info.get('product_name')
            or 'Fuel Scan'
        )
        brand = payload.get('brand') or nutrition_info.get('brand')
        recommendations = payload.get('recommendations')
        if recommendations is None:
            recommendations = _extract_recommendations(str(payload.get('explanation') or ''))

        scan = ScanHistory(
            user_id=user_id,
            product_name=str(product_name)[:255] if product_name else 'Fuel Scan',
            brand=str(brand)[:255] if brand else None,
            nutrition_data=nutrition_info,
            score=float(payload.get('score', 0) or 0),
            explanation=payload.get('explanation'),
            recommendations=recommendations,
            meal_type=payload.get('meal_type'),
        )
        user.increment_scan_count()
        db.session.add(scan)
        db.session.commit()

    _with_db_retry('save-scan-history', persist)


def _run_local_muscle_analysis(video_path: Path, exercise_type: str) -> dict:
    from services.muscle_ai_service.core.analysis import analyze_saved_video

    result = analyze_saved_video(video_path, exercise_type)
    result['video_url'] = _absolute_url(result.get('video_url'))
    return result


def _get_user_by_id(user_id):
    return _with_db_retry('load-user', lambda: db.session.get(User, user_id))


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(config_name='development'):
    template_folder = None if _is_huggingface_runtime() else '../web/templates'
    static_folder = None if _is_huggingface_runtime() else '../web/static'
    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url or db_url == 'sqlite:///data/fitlife.db':
        db_url = f'sqlite:///{PROJECT_ROOT / "data" / "fitlife.db"}'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', '')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    init_db(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    allowed_origins = [
        'http://localhost:3000',
        frontend_url,
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    _register_legacy_routes(app)
    _register_legacy_auth(app)
    _register_legacy_oauth(app)
    _register_legacy_dashboard(app)
    _register_legacy_static_pages(app)

    _register_api_auth(app)
    _register_api_user(app)
    _register_api_dashboard(app)
    _register_api_services(app)
    _register_api_ana(app)

    _register_error_handlers(app)
    _ensure_directories()

    return app


# ===================================================================
# LEGACY JINJA2 ROUTES (kept for backwards compatibility)
# ===================================================================

def _register_legacy_routes(app):
    @app.route('/')
    def index():
        if _is_huggingface_space_request():
            return Response(_space_root_html(), mimetype='text/html')
        return redirect(f"{_frontend_url()}/")

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'fitlife-gateway'}, 200

    @app.route('/nutri-ai')
    def nutri_ai_redirect():
        return redirect(f"{_frontend_url()}/nutri-ai")

    @app.route('/muscle-ai')
    def muscle_ai_redirect():
        return redirect(f"{_frontend_url()}/muscle-ai")

    @app.route('/ana')
    def ana():
        return redirect(f"{_frontend_url()}/ana")


def _register_legacy_auth(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return redirect(f"{_frontend_url()}/login")
        if current_user.is_authenticated:
            return redirect(f"{_frontend_url()}/dashboard")
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(request.args.get('next') or f"{_frontend_url()}/dashboard")
            flash('Invalid email or password', 'error')
        return render_template('auth/login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return redirect(f"{_frontend_url()}/register")
        if current_user.is_authenticated:
            return redirect(f"{_frontend_url()}/dashboard")
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            name = request.form.get('name', '').strip()
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return render_template('auth/register.html')
            if len(password) < 8:
                flash('Password must be at least 8 characters', 'error')
                return render_template('auth/register.html')
            user = User(email=email, name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Welcome to AI Fit Pro!', 'success')
            return redirect(f"{_frontend_url()}/dashboard")
        return render_template('auth/register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))


def _register_legacy_oauth(app):
    @app.route('/auth/google')
    def google_login():
        if current_user.is_authenticated:
            return redirect(f"{_frontend_url()}/dashboard")
        if not app.config.get('GOOGLE_CLIENT_ID'):
            flash('Google Sign-In is not configured.', 'error')
            return redirect(f"{_frontend_url()}/login")
        nonce = secrets.token_urlsafe(32)
        session['oauth_nonce'] = nonce
        return oauth.google.authorize_redirect(url_for('google_callback', _external=True), nonce=nonce)

    @app.route('/auth/google/callback')
    def google_callback():
        try:
            token = oauth.google.authorize_access_token()
            nonce = session.pop('oauth_nonce', None)
            user_info = oauth.google.parse_id_token(token, nonce=nonce)
        except Exception:
            flash('Failed to sign in with Google.', 'error')
            return redirect(f"{_frontend_url()}/login")
        if not user_info:
            flash('Could not retrieve your information from Google.', 'error')
            return redirect(f"{_frontend_url()}/login")
        email = user_info.get('email', '').lower()
        name = user_info.get('name', '')
        google_id = user_info.get('sub')
        if not email:
            flash('Could not get email from Google account.', 'error')
            return redirect(f"{_frontend_url()}/login")
        user = User.query.filter_by(email=email).first()
        if user:
            user.last_login = datetime.now(timezone.utc)
            if not user.google_id:
                user.google_id = google_id
            db.session.commit()
            login_user(user, remember=True)
        else:
            user = User(email=email, name=name, google_id=google_id)
            user.set_password(secrets.token_urlsafe(32))
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
        return redirect(f"{_frontend_url()}/dashboard")


def _register_legacy_dashboard(app):
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return redirect(f"{_frontend_url()}/dashboard")

    @app.route('/dashboard/history')
    @login_required
    def scan_history():
        return redirect(f"{_frontend_url()}/dashboard/history")

    @app.route('/dashboard/workouts')
    @login_required
    def workout_history():
        return redirect(f"{_frontend_url()}/dashboard/workouts")

    @app.route('/dashboard/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        return redirect(f"{_frontend_url()}/dashboard/settings")


def _register_legacy_static_pages(app):
    @app.route('/pricing')
    def pricing():
        return redirect(f"{_frontend_url()}/pricing")

    @app.route('/enterprise')
    def enterprise():
        return redirect(f"{_frontend_url()}/enterprise")

    @app.route('/developers')
    def developers():
        return redirect(f"{_frontend_url()}/developers")

    @app.route('/roadmap')
    def roadmap():
        return redirect(f"{_frontend_url()}/roadmap")

    @app.route('/contact')
    def contact():
        return redirect(f"{_frontend_url()}/contact")

    @app.route('/about')
    def about():
        return redirect(f"{_frontend_url()}/about")


# ===================================================================
# NEW JSON API (consumed by the Next.js frontend)
# ===================================================================

def _user_to_full_dict(user):
    health_score = _with_db_retry('user-health-score', lambda: user.health_score)
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'plan': user.plan,
        'age': user.age,
        'gender': user.gender,
        'height_cm': user.height_cm,
        'weight_kg': user.weight_kg,
        'activity_level': user.activity_level,
        'diet_type': user.diet_type,
        'goal': user.goal,
        'medical_conditions': user.medical_conditions or [],
        'allergies': user.allergies or [],
        'health_score': health_score,
        'scans_this_month': user.scans_this_month,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _register_api_auth(app):
    @app.route('/api/v1/auth/register', methods=['POST'])
    def api_auth_register():
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        if not email or not password or not name:
            return jsonify({'error': 'Name, email, and password are required'}), 400
        if _with_db_retry('auth-register-lookup', lambda: User.query.filter_by(email=email).first()):
            return jsonify({'error': 'Email already registered'}), 409
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        def create_user():
            user = User(email=email, name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user

        user = _with_db_retry('auth-register-create', create_user)

        tokens = generate_tokens(user.id)
        return jsonify({**tokens, 'user': _user_to_full_dict(user)}), 201

    @app.route('/api/v1/auth/login', methods=['POST'])
    def api_auth_login():
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = _with_db_retry('auth-login-load', lambda: User.query.filter_by(email=email).first())
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        def mark_login():
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

        _with_db_retry('auth-login-commit', mark_login)
        tokens = generate_tokens(user.id)
        return jsonify({**tokens, 'user': _user_to_full_dict(user)})

    @app.route('/api/v1/auth/refresh', methods=['POST'])
    def api_auth_refresh():
        data = request.get_json(silent=True) or {}
        token = data.get('refresh_token', '')
        payload = decode_token(token)
        if not payload or payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        user = _get_user_by_id(payload['sub'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        tokens = generate_tokens(user.id)
        return jsonify(tokens)

    @app.route('/api/v1/auth/google', methods=['GET'])
    def api_auth_google():
        if not app.config.get('GOOGLE_CLIENT_ID'):
            return jsonify({'error': 'Google OAuth not configured'}), 503
        nonce = secrets.token_urlsafe(32)
        session['oauth_nonce'] = nonce
        redirect_uri = url_for('api_auth_google_callback', _external=True)
        auth_url = oauth.google.create_authorization_url(redirect_uri, nonce=nonce)
        return jsonify({'redirect_url': auth_url['url']})

    @app.route('/api/v1/auth/google/callback')
    def api_auth_google_callback():
        try:
            token = oauth.google.authorize_access_token()
            nonce = session.pop('oauth_nonce', None)
            user_info = oauth.google.parse_id_token(token, nonce=nonce)
        except Exception:
            return jsonify({'error': 'Google authentication failed'}), 401

        email = (user_info or {}).get('email', '').lower()
        if not email:
            return jsonify({'error': 'Could not get email from Google'}), 401

        name = user_info.get('name', '')
        google_id = user_info.get('sub')
        user = _with_db_retry('google-auth-load', lambda: User.query.filter_by(email=email).first())
        if user:
            def touch_google_login():
                user.last_login = datetime.now(timezone.utc)
                if not user.google_id:
                    user.google_id = google_id
                db.session.commit()

            _with_db_retry('google-auth-update', touch_google_login)
        else:
            def create_google_user():
                user = User(email=email, name=name, google_id=google_id)
                user.set_password(secrets.token_urlsafe(32))
                db.session.add(user)
                db.session.commit()
                return user

            user = _with_db_retry('google-auth-create', create_google_user)

        tokens = generate_tokens(user.id)
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}")


def _register_api_user(app):
    @app.route('/api/v1/user', methods=['GET'])
    @jwt_required
    def api_user():
        user = _get_user_by_id(g.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(_user_to_full_dict(user))

    @app.route('/api/v1/user', methods=['DELETE'])
    @jwt_required
    def api_delete_user():
        user = _get_user_by_id(g.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        def delete_user():
            Achievement.query.filter_by(user_id=user.id).delete()
            APIKey.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()

        _with_db_retry('delete-user', delete_user)
        return jsonify({'status': 'deleted'})

    @app.route('/api/v1/user/settings', methods=['PUT'])
    @jwt_required
    def api_user_settings():
        user = _get_user_by_id(g.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json(silent=True) or {}
        for field in ['name', 'age', 'gender', 'height_cm', 'weight_kg', 'activity_level', 'diet_type', 'goal']:
            if field in data:
                setattr(user, field, data[field])
        if 'allergies' in data:
            user.allergies = data['allergies']
        if 'medical_conditions' in data:
            user.medical_conditions = data['medical_conditions']
        _with_db_retry('save-user-settings', db.session.commit)
        return jsonify(_user_to_full_dict(user))

    @app.route('/api/v1/user/scans', methods=['GET'])
    @jwt_required
    def api_user_scans():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        scans = _with_db_retry(
            'list-user-scans',
            lambda: ScanHistory.query.filter_by(user_id=g.current_user_id)
            .order_by(ScanHistory.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False),
        )
        return jsonify({
            'items': [s.to_dict() for s in scans.items],
            'total': scans.total,
            'page': scans.page,
            'pages': scans.pages,
        })

    @app.route('/api/v1/user/workouts', methods=['GET'])
    @jwt_required
    def api_user_workouts():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        workouts = _with_db_retry(
            'list-user-workouts',
            lambda: WorkoutSession.query.filter_by(user_id=g.current_user_id)
            .order_by(WorkoutSession.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False),
        )
        return jsonify({
            'items': [w.to_dict() for w in workouts.items],
            'total': workouts.total,
            'page': workouts.page,
            'pages': workouts.pages,
        })


def _register_api_dashboard(app):
    @app.route('/api/v1/dashboard/stats', methods=['GET'])
    @jwt_required
    def api_dashboard_stats():
        uid = g.current_user_id
        user = _get_user_by_id(uid)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        def load_dashboard_stats():
            total_scans = ScanHistory.query.filter_by(user_id=uid).count()
            total_workouts = WorkoutSession.query.filter_by(user_id=uid).count()
            avg_nutrition = db.session.query(db.func.avg(ScanHistory.score)).filter_by(user_id=uid).scalar() or 0
            avg_form = db.session.query(db.func.avg(WorkoutSession.form_score)).filter_by(user_id=uid).scalar() or 0
            return total_scans, total_workouts, avg_nutrition, avg_form

        total_scans, total_workouts, avg_nutrition, avg_form = _with_db_retry(
            'dashboard-stats',
            load_dashboard_stats,
        )
        health_score = _with_db_retry('dashboard-health-score', lambda: user.health_score)
        return jsonify({
            'health_score': health_score,
            'total_scans': total_scans,
            'total_workouts': total_workouts,
            'avg_nutrition': round(float(avg_nutrition), 1),
            'avg_form': round(float(avg_form), 1),
            'scans_this_month': user.scans_this_month,
            'plan': user.plan,
        })


def _register_api_services(app):
    @app.route('/api/v1/health', methods=['GET'])
    def api_health():
        return jsonify({'status': 'ok', 'service': 'fitlife-gateway'})

    # -- Nutri AI (direct, no microservice needed) ---------------------------
    @app.route('/api/v1/nutri-ai/upload', methods=['POST'])
    @jwt_optional
    def api_nutri_upload():
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        file = request.files['image']
        if not file.filename:
            return jsonify({'error': 'Empty filename'}), 400

        mime = file.content_type or 'image/jpeg'
        image_bytes = file.read()
        nutrition_info = extract_nutrition_from_image(image_bytes, mime)
        if 'error' in nutrition_info:
            return jsonify(nutrition_info), 422
        return jsonify({'success': True, 'nutrition_info': nutrition_info})

    @app.route('/api/v1/nutri-ai/analyze', methods=['POST'])
    @jwt_optional
    def api_nutri_analyze():
        data = request.get_json(silent=True) or {}
        nutrition_info = data.get('nutrition_info')
        user_profile = data.get('user_profile')
        if not nutrition_info or not user_profile:
            return jsonify({'error': 'nutrition_info and user_profile are required'}), 400

        health_metrics = calculate_health_metrics(user_profile)
        score, explanation = generate_score(user_profile, nutrition_info, health_metrics)
        result = {
            'success': True,
            'score': score,
            'explanation': explanation,
            'health_metrics': health_metrics,
            'nutrition_info': nutrition_info,
        }
        _save_scan_history(g.current_user_id, {
            **result,
            'product_name': data.get('product_name'),
            'brand': data.get('brand'),
            'meal_type': data.get('meal_type'),
        })
        return jsonify(result)

    # -- Muscle AI ----------------------------------------------------------
    @app.route('/api/v1/muscle-ai/exercises', methods=['GET'])
    def api_muscle_exercises():
        return jsonify({
            'exercises': [
                'regular_deadlift', 'sumo_deadlift', 'squat',
                'romanian_deadlift', 'zercher_squat', 'front_squat',
            ]
        })

    @app.route('/api/v1/muscle-ai/upload', methods=['POST'])
    @jwt_optional
    def api_muscle_upload():
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        file = request.files['video']
        exercise_type = request.form.get('exercise_type', '')
        if not file.filename or not exercise_type:
            return jsonify({'error': 'Video and exercise_type are required'}), 400

        filename = secure_filename(file.filename)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"{ts}_{filename}"
        video_dir = UPLOAD_FOLDER / 'videos'
        video_dir.mkdir(parents=True, exist_ok=True)
        save_path = video_dir / save_name
        file.save(str(save_path))

        try:
            result = _run_local_muscle_analysis(save_path, exercise_type)
            if save_path.exists():
                save_path.unlink()
            _save_workout_session(g.current_user_id, exercise_type, result)
            return jsonify(result)
        except Exception as local_error:
            app.logger.warning(f'Local muscle analysis failed, falling back to service: {local_error}')
            _, muscle_url = _service_urls()
            try:
                with open(save_path, 'rb') as f:
                    resp = http_requests.post(
                        f"{muscle_url}/muscle/api/analyze",
                        files={'video': (save_name, f, 'video/mp4')},
                        data={'exercise_type': exercise_type},
                        timeout=300,
                    )
                if not resp.ok:
                    body = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'error': resp.text}
                    return jsonify(body), resp.status_code
                result = resp.json()
                result['video_url'] = (
                    f"{muscle_url.rstrip('/')}{result['video_url']}"
                    if result.get('video_url')
                    else None
                )
                _save_workout_session(g.current_user_id, exercise_type, result)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 503
            finally:
                if save_path.exists():
                    save_path.unlink()

    @app.route('/api/v1/muscle-ai/task/<task_id>', methods=['GET'])
    def api_muscle_task(task_id):
        try:
            from gateway.tasks import analyze_video
            result = analyze_video.AsyncResult(task_id)
            if result.state == 'PENDING':
                return jsonify({'task_id': task_id, 'status': 'pending'})
            if result.state == 'STARTED':
                return jsonify({'task_id': task_id, 'status': 'processing'})
            if result.state == 'SUCCESS':
                payload = result.result
                if isinstance(payload, dict):
                    inner = payload.get('result')
                    if isinstance(inner, dict) and str(inner.get('video_url', '')).startswith('/'):
                        inner['video_url'] = _absolute_url(inner['video_url'])
                return jsonify({'task_id': task_id, 'status': 'completed', 'result': payload})
            return jsonify({'task_id': task_id, 'status': result.state.lower()})
        except Exception:
            return jsonify({'error': 'Task backend unavailable, use sync upload'}), 503


def _register_api_ana(app):
    @app.route('/api/v1/ana/chat', methods=['POST'])
    @jwt_optional
    def api_ana_chat():
        from services.nutri_ai_service.core.ana.ana_agent import chat as ana_chat_fn
        data = request.get_json(silent=True) or {}
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        user_profile = None
        if g.current_user_id:
            user = _get_user_by_id(g.current_user_id)
            if user:
                user_profile = {
                    'age': user.age, 'gender': user.gender,
                    'activity_level': user.activity_level,
                    'diet_type': user.diet_type, 'goal': user.goal,
                    'allergies': user.allergies or [],
                    'medical_history': {'diseases': user.medical_conditions or []},
                }

        reply = ana_chat_fn(
            message=message,
            history=data.get('history', []),
            user_profile=user_profile,
        )
        return jsonify({'reply': reply})


# ===================================================================
# Error Handlers
# ===================================================================

def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if _is_huggingface_runtime():
            return jsonify({'error': 'Not found'}), 404
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if _is_huggingface_runtime():
            return jsonify({'error': 'Internal server error'}), 500
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        if _is_huggingface_runtime():
            return jsonify({'error': 'Service unavailable'}), 503
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Service unavailable'}), 503
        return render_template('errors/503.html'), 503


def _ensure_directories():
    for d in [
        _runtime_data_root(),
        _runtime_data_root() / 'uploads',
        _runtime_data_root() / 'uploads' / 'videos',
        _runtime_data_root() / 'processed',
        PROJECT_ROOT / 'logs',
    ]:
        d.mkdir(parents=True, exist_ok=True)


app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000')),
        debug=os.environ.get('FLASK_DEBUG') == '1',
    )
