from app import app, init_db

try:
    # Инициализация базы данных при запуске
    with app.app_context():
        init_db()
    print("База данных успешно инициализирована.")
except Exception as e:
    print(f"Ошибка при инициализации базы данных: {e}")

if __name__ == "__main__":
    app.run(debug=True)  # Включаем debug-режим для удобства разработки
