# ... (предыдущий код остается без изменений)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('schedule'))

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

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ... (остальной код остается без изменений)
