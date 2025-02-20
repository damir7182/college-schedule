from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Инициализация приложения
app = Flask(__name__)

# Конфигурация для Render.com
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college_schedule.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных и менеджера логинов
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/student')
def student():
    try:
        selected_group = request.args.get('group')
        all_schedules = Schedule.query.all()
        
        if not all_schedules:
            # Если расписание пустое, показываем пустой список
            return render_template('public_schedule.html',
                                groups=[],
                                selected_group=None,
                                schedules=[])
        
        groups = sorted(list(set(s.group_name for s in all_schedules)))
        schedules = []
        
        if selected_group:
            schedules = Schedule.query.filter_by(group_name=selected_group)\
                                    .order_by(Schedule.day, Schedule.time)\
                                    .all()
        
        return render_template('public_schedule.html',
                             groups=groups,
                             selected_group=selected_group,
                             schedules=schedules)
    except Exception as e:
        # Логирование ошибки
        print(f"Error in student route: {str(e)}")
        flash('Произошла ошибка при загрузке расписания', 'error')
        return redirect(url_for('index'))

@app.route('/schedule')
@login_required
def schedule():
    try:
        filter_day = request.args.get('day')
        filter_group = request.args.get('group')
        filter_teacher = request.args.get('teacher')

        query = Schedule.query

        if filter_day:
            query = query.filter(Schedule.day == filter_day)
        if filter_group:
            query = query.filter(Schedule.group_name == filter_group)
        if filter_teacher:
            query = query.filter(Schedule.teacher == filter_teacher)

        schedules = query.order_by(Schedule.day, Schedule.time).all()
        all_schedules = Schedule.query.all()
        
        if not all_schedules:
            # Если расписание пустое
            return render_template('schedule.html',
                                schedules=[],
                                groups=[],
                                teachers=[])
        
        groups = sorted(list(set(s.group_name for s in all_schedules)))
        teachers = sorted(list(set(s.teacher for s in all_schedules)))

        return render_template('schedule.html', 
                            schedules=schedules,
                            groups=groups,
                            teachers=teachers)
    except Exception as e:
        # Логирование ошибки
        print(f"Error in schedule route: {str(e)}")
        flash('Произошла ошибка при загрузке расписания', 'error')
        return redirect(url_for('index'))

def init_db():
    with app.app_context():
        db.create_all()
        # Создание администратора, если его нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print('Администратор успешно создан!')
        
        # Проверка существования базовых данных
        if not Schedule.query.first():
            # Добавьте тестовое расписание, если база пуста
            test_schedule = Schedule(
                day='Понедельник',
                time='09:00',
                subject='Тестовый предмет',
                teacher='Тестовый преподаватель',
                room='101',
                group_name='Тестовая группа'
            )
            db.session.add(test_schedule)
            db.session.commit()
            print('Тестовое расписание создано!')
