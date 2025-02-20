from app import app, db, User, init_db

if __name__ == '__main__':
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
