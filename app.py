from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Проверка сессии перед каждым запросом
@app.before_request
def check_user_status():
    if current_user.is_authenticated:
        if request.endpoint != 'logout':
            if not current_user.is_admin and 'admin' in request.path:
                logout_user()
                flash('Сессия завершена')
                return redirect(url_for('index'))

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    selected_group = request.args.get('group')
    all_schedules = Schedule.query.all()
    groups = sorted(list(set(s.group_name for s in all_schedules)))
    schedules = []
    if selected_group:
        schedules = Schedule.query.filter_by(group_name=selected_group).order_by(Schedule.time).all()
    return render_template('public_schedule.html', groups=groups, selected_group=selected_group, schedules=schedules)

@app.route('/admin')
def admin():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('schedule'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('Вы успешно вошли в систему')
            return redirect(url_for('schedule'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/schedule')
@login_required
def schedule():
    schedules = Schedule.query.all()
    return render_template('schedule.html', schedules=schedules)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы')
    return redirect(url_for('index'))

@app.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    if not current_user.is_admin:
        return redirect(url_for('schedule'))
    
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
    flash('Расписание успешно добавлено')
    return redirect(url_for('schedule'))

@app.route('/delete_schedule/<int:id>')
@login_required
def delete_schedule(id):
    if not current_user.is_admin:
        return redirect(url_for('schedule'))
    
    schedule = Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Расписание успешно удалено')
    return redirect(url_for('schedule'))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
