from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from sqlalchemy import case

# Инициализация приложения
app = Flask(__name__)

# Конфигурация для Render.com
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')

# Настройка базы данных для Render.com
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///college_schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных и менеджера логинов
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(20), nullable=False)
    group_name = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/schedule')
@login_required
def schedule():
    try:
        if not current_user.is_admin:
            flash('Доступ запрещен. Только для администраторов.', 'danger')
            return redirect(url_for('index'))

        # Получаем параметры фильтрации
        filter_day = request.args.get('day')
        filter_group = request.args.get('group')

        # Базовый запрос
        query = Schedule.query

        # Применяем фильтры
        if filter_day:
            query = query.filter(Schedule.day == filter_day)
        if filter_group:
            query = query.filter(Schedule.group_name == filter_group)

        # Получаем все расписания
        schedules = query.all()

        # Получаем уникальные группы
        groups = sorted(list(set(s.group_name for s in Schedule.query.all())))

        # Список дней недели
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

        return render_template('schedule.html',
                             schedules=schedules,
                             groups=groups,
                             days=days,
                             selected_day=filter_day,
                             selected_group=filter_group)

    except Exception as e:
        print(f"Error in schedule route: {str(e)}")  # Для отладки
        flash('Произошла ошибка при загрузке расписания', 'danger')
        return redirect(url_for('index'))

# ... (остальной код остается без изменений)

def init_db():
    try:
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            
            # Создаем администратора, если его нет
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', is_admin=True)
                admin.set_password('admin')
                db.session.add(admin)
                db.session.commit()
                print('Администратор создан успешно!')

    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {str(e)}')
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
