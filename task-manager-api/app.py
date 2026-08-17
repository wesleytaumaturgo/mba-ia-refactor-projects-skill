from flask import Flask
from flask_cors import CORS
import datetime

from config import load_settings
from database import db
from middlewares.auth import authenticate_request, public
from middlewares.rate_limit import RateLimiter
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

settings = load_settings()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.secret_key
app.config['SETTINGS'] = settings
app.config['LOGIN_RATE_LIMITER'] = RateLimiter(settings.login_rate_limit,
                                               settings.login_rate_window_seconds)

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)

# Negar por padrão: toda rota exige credencial, exceto as marcadas com @public.
app.before_request(authenticate_request)


@app.route('/health')
@public
def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}


@app.route('/')
@public
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
