from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from datetime import datetime

# Инициализация объектов
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # Создание приложения Flask
    app = Flask(__name__)

    # Конфигурация
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college_schedule.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Определение моделей
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

    # Регистрация маршрутов
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
                schedules = Schedule.query.filter_by(group_name=selected_group)\
                                        .order_by(Schedule.day, Schedule.time)\
                                        .all()
            
            return render_template('public_schedule.html',
                                groups=groups,
                                selected_group=selected_group,
                                schedules=schedules)
        except Exception as e:
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
            flash('Неверное имя пользователя или пароль')
        return render_template('login.html')

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
            groups = sorted(list(set(s.group_name for s in all_schedules)))
            teachers = sorted(list(set(s.teacher for s in all_schedules)))
            days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

            return render_template('schedule.html', 
                                schedules=schedules,
                                groups=groups,
                                teachers=teachers,
                                days=days,
                                selected_day=filter_day,
                                selected_group=filter_group,
                                selected_teacher=filter_teacher)
        except Exception as e:
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
            new_schedule = Schedule(
                day=request.form['day'],
                time=request.form['time'],
                subject=request.form['subject'],
                teacher=request.form['teacher'],
                room=request.form['room'],
                group_name=request.form['group_name']
            )
            db.session.add(new_schedule)
            db.session.commit()
            flash('Расписание успешно добавлено', 'success')
        except Exception as e:
            flash('Ошибка при добавлении расписания', 'error')
            db.session.rollback()
        
        return redirect(url_for('schedule'))

    @app.route('/delete_
