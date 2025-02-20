from app import app, init_db

# Инициализация базы данных при запуске
init_db()

if __name__ == "__main__":
    app.run()
