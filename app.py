from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from datetime import datetime
from sqlalchemy import case

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Инициализация приложения
app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college_schedule.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных и менеджера логинов
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели
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
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    try:
        selected_group = request.args.get('group')
        all_schedules = Schedule.query.all()
        groups = sorted(list(set(s.group_name for s in all_schedules)))
        schedules = []
        
        if selected_group:
            day_order = case({
                'Понедельник': 1,
                'Вторник': 2,
                'Среда': 3,
                'Четверг': 4,
                'Пятница': 5,
                'Суббота': 6
            }, value=Schedule.day)
            
            schedules = Schedule.query.filter_by(group_name=selected_group)\
                                    .order_by(day_order, Schedule.time)\
                                    .all()
        
        return render_template('public_schedule.html',
                             groups=groups,
                             selected_group=selected_group,
                             schedules=schedules)
    except Exception as e:
        logger.error(f"Error in student route: {str(e)}")
        flash('Произошла ошибка при загрузке расписания', 'error')
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('schedule'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('schedule'))
        flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

@app.route('/schedule')
@login_required
def schedule():
    if not current_user.is_admin:
        flash('Доступ запрещен. Только для администраторов.', 'error')
        return redirect(url_for('index'))
    
    try:
        filter_day = request.args.get('day')
        filter_group = request.args.get('group')

        query = Schedule.query

        if filter_day:
            query = query.filter(Schedule.day == filter_day)
        if filter_group:
            query = query.filter(Schedule.group_name == filter_group)

        day_order = case({
            'Понедельник': 1,
            'Вторник': 2,
            'Среда': 3,
            'Четверг': 4,
            'Пятница': 5,
            'Суббота': 6
        }, value=Schedule.day)

        schedules = query.order_by(day_order, Schedule.time).all()
        all_schedules = Schedule.query.all()
        groups = sorted(list(set(s.group_name for s in all_schedules)))
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

        return render_template('schedule.html', 
                            schedules=schedules,
                            groups=groups,
                            days=days,
                            selected_day=filter_day,
                            selected_group=filter_group)
    except Exception as e:
        logger.error(f"Error in schedule route: {str(e)}")
        flash('Произошла ошибка при загрузке расписания', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('schedule'))
    
    try:
        # Преобразование времени в формат ЧЧ:ММ
        time_str = request.form['time']
        if ':' not in time_str:
            time_str = f"{time_str[:2]}:{time_str[2:]}"

        new_schedule = Schedule(
            day=request.form['day'],
            time=time_str,
            subject=request.form['subject'],
            teacher=request.form['teacher'],
            room=request.form['room'],
            group_name=request.form['group_name']
        )
        db.session.add(new_schedule)
        db.session.commit()
        flash('Расписание успешно добавлено', 'success')
    except Exception as e:
        logger.error(f"Error adding schedule: {str(e)}")
        flash('Ошибка при добавлении расписания', 'error')
        db.session.rollback()
    
    return redirect(url_for('schedule'))

@app.route('/delete_schedule/<int:id>')
@login_required
def delete_schedule(id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('schedule'))
    
    try:
        schedule = Schedule.query.get_or_404(id)
        db.session.delete(schedule)
        db.session.commit()
        flash('Расписание успешно удалено', 'success')
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        flash('Ошибка при удалении расписания', 'error')
        db.session.rollback()
    
    return redirect(url_for('schedule'))

def init_db():
    try:
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            
            # Создаем администратора, если его нет
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', is_admin=True)
                admin.set_password('admin')
                db.session.add(admin)
                
                # Добавляем тестовое расписание
                test_schedules = [
                    Schedule(
                        day='Понедельник',
                        time='09:00',
                        subject='Математика',
                        teacher='Иванов И.И.',
                        room='101',
                        group_name='ИС-11'
                    ),
                    Schedule(
                        day='Понедельник',
                        time='10:30',
                        subject='Физика',
                        teacher='Петров П.П.',
                        room='102',
                        group_name='ИС-11'
                    ),
                    Schedule(
                        day='Вторник',
                        time='09:00',
                        subject='Информатика',
                        teacher='Сидоров С.С.',
                        room='103',
                        group_name='ИС-12'
                    )
                ]
                
                # Добавляем тестовые данные
                for schedule in test_schedules:
                    db.session.add(schedule)
                
                # Сохраняем изменения
                db.session.commit()
                print('База данных успешно инициализирована!')
    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {str(e)}')
        db.session.rollback()
        raise

if __name__ == '__main__':
    with app.app_context():
        # Удаляем старую базу данных
        if os.path.exists('college_schedule.db'):
            os.remove('college_schedule.db')
        
        # Инициализируем новую базу данных
        init_db()
    
    app.run(debug=True)
