try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception as e:
    raise RuntimeError(
        "psycopg2 не установлен или недоступен в этом окружении. Установите его: `pip install psycopg2-binary`"
    ) from e

from contextlib import contextmanager

# параметры подключения
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "study_tracker_app",
    "user": "postgres",
    "password": "1234567890"
}

# контекстный менеджер для подключения к базе
@contextmanager
def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        # конвертируем ошибку подключения в более понятную для UI/лога
        raise RuntimeError(f"DB connection failed: {e}") from e

    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# инициализация схемы (создаёт таблицы, если их ещё нет)
def init_db():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            theme TEXT,
            notifications_enabled BOOLEAN,
            default_notification_time TIME
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            age INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            full_name TEXT,
            contact_info TEXT,
            requirements TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            name TEXT,
            teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
            classroom TEXT,
            color TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
            name TEXT,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            type TEXT  -- ТОЛЬКО ОДИН РАЗ ЗДЕСЬ
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS schedule (
            id SERIAL PRIMARY KEY,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            day_of_week INTEGER,
            start_time TIME,
            end_time TIME
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
            due_date TIMESTAMP,
            status TEXT,
            priority INTEGER DEFAULT 1,
            is_automatic_debt BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS attachments (
            id SERIAL PRIMARY KEY,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            file_path TEXT,
            file_type TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            reminder_time TIMESTAMP
        )
        """
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)

def add_missing_columns():
    """Добавляет недостающие столбцы к существующим таблицам"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # Проверяем существование столбца type в таблице topics
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='topics' AND column_name='type'
                """)
                if not cur.fetchone():
                    # Добавляем столбец если он не существует
                    cur.execute("ALTER TABLE topics ADD COLUMN type TEXT")
                    print("DB: добавлен столбец 'type' в таблицу 'topics'")

                print("DB: проверка структуры таблиц завершена")
            except Exception as e:
                print("DB: ошибка при добавлении столбцов:", e)

# ----------------------------
# ОСНОВНЫЕ ФУНКЦИИ ДЛЯ ЗАДАЧ И ЭКЗАМЕНОВ
# ----------------------------

def get_tasks():
    """Получает ВСЕ задачи (включая экзамены)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            return cur.fetchall()

def get_regular_tasks():
    """Получает только обычные задачи (НЕ экзамены)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM tasks 
                WHERE (type IS NULL OR type != 'exam')
                AND (type NOT IN ('exam') OR type IS NULL)
                ORDER BY created_at DESC
            """)
            return cur.fetchall()

def get_exams_only():
    """Получает только экзамены"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM tasks 
                WHERE type = 'exam'
                ORDER BY due_date DESC
            """)
            return cur.fetchall()

def get_tasks_by_type(task_type=None):
    """Получает задачи по типу"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if task_type:
                cur.execute("SELECT * FROM tasks WHERE type = %s ORDER BY created_at DESC", (task_type,))
            else:
                cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            return cur.fetchall()

def add_task(title, description=None, task_type='other', subject_id=None, topic_id=None,
             due_date=None, status='pending', priority=1, is_automatic_debt=False):
    """Добавление задачи с поддержкой учебных работ"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tasks 
                (title, description, type, subject_id, topic_id, due_date, status, priority, is_automatic_debt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title, description, task_type, subject_id, topic_id, due_date, status, priority, is_automatic_debt))
            return cur.fetchone()['id']

def add_exam(title, description=None, subject_id=None, topic_id=None, due_date=None):
    """Добавляет экзамен (отдельная функция для ясности)"""
    return add_task(
        title=title,
        description=description,
        task_type='exam',  # Явно указываем тип 'exam'
        subject_id=subject_id,
        topic_id=topic_id,
        due_date=due_date,
        status='pending',
        priority=1,
        is_automatic_debt=False
    )

def delete_task(task_id):
    """Удаляет задачу по ID"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

def update_task(task_id, title=None, description=None, task_type=None, subject_id=None, due_date=None, status=None, priority=None):
    """Обновляет задачу"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            params = []

            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            if task_type is not None:
                updates.append("type = %s")
                params.append(task_type)
            if subject_id is not None:
                updates.append("subject_id = %s")
                params.append(subject_id)
            if due_date is not None:
                updates.append("due_date = %s")
                params.append(due_date)
            if status is not None:
                updates.append("status = %s")
                params.append(status)
            if priority is not None:
                updates.append("priority = %s")
                params.append(priority)

            if updates:
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)
                print(f"✅ Задача {task_id} обновлена: {', '.join(updates)}")

# ----------------------------
# ПРЕДМЕТЫ
# ----------------------------

def delete_subject(subject_id):
    """Удаляет предмет по ID"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))

def update_subject(subject_id, name=None, teacher_id=None, classroom=None, color=None):
    """Обновляет данные предмета"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            params = []

            if name is not None:
                updates.append("name = %s")
                params.append(name)
            if teacher_id is not None:
                updates.append("teacher_id = %s")
                params.append(teacher_id)
            if classroom is not None:
                updates.append("classroom = %s")
                params.append(classroom)
            if color is not None:
                updates.append("color = %s")
                params.append(color)

            if updates:
                params.append(subject_id)
                query = f"UPDATE subjects SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)

def get_subject_by_id(subject_id):
    """Получает предмет по ID"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
            return cur.fetchone()

def get_subjects():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subjects ORDER BY name")
            return cur.fetchall()

def add_subject(name, teacher_id=None, classroom=None, color=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subjects (name, teacher_id, classroom, color)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (name, teacher_id, classroom, color))
            return cur.fetchone()['id']

# ----------------------------
# SETTINGS
# ----------------------------

def get_settings():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM settings LIMIT 1")
            return cur.fetchone()

def update_settings(theme=None, notifications_enabled=None, default_notification_time=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE settings SET
                theme = COALESCE(%s, theme),
                notifications_enabled = COALESCE(%s, notifications_enabled),
                default_notification_time = COALESCE(%s, default_notification_time)
            """, (theme, notifications_enabled, default_notification_time))

# ----------------------------
# USERS
# ----------------------------

def get_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY username")
            return cur.fetchall()

def add_user(username, age):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, age) VALUES (%s, %s) RETURNING id", (username, age))
            return cur.fetchone()['id']

# ----------------------------
# TEACHERS
# ----------------------------

def get_teachers():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM teachers ORDER BY full_name")
            return cur.fetchall()

def add_teacher(full_name, contact_info=None, requirements=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO teachers (full_name, contact_info, requirements)
                VALUES (%s, %s, %s) RETURNING id
            """, (full_name, contact_info, requirements))
            return cur.fetchone()['id']

def get_teacher_name(teacher_id):
    """Получает имя преподавателя по ID"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT full_name FROM teachers WHERE id = %s", (teacher_id,))
            result = cur.fetchone()
            return result["full_name"] if result else "Неизвестно"

# ----------------------------
# TOPICS
# ----------------------------

def get_topics(subject_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if subject_id:
                cur.execute("SELECT * FROM topics WHERE subject_id=%s ORDER BY name", (subject_id,))
            else:
                cur.execute("SELECT * FROM topics ORDER BY name")
            return cur.fetchall()

def add_topic(name, subject_id=None, work_type='не указан'):
    """Добавляет тему/задолженность"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO topics (name, subject_id, type)
                VALUES (%s, %s, %s) RETURNING id
            """, (name, subject_id, work_type))
            return cur.fetchone()['id']

def delete_topic(topic_id):
    """Удаляет тему по ID"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM topics WHERE id = %s", (topic_id,))

def update_topic(topic_id, name=None, work_type=None, subject_id=None):
    """Обновляет тему"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            params = []

            if name is not None:
                updates.append("name = %s")
                params.append(name)
            if work_type is not None:
                updates.append("type = %s")
                params.append(work_type)
            if subject_id is not None:
                updates.append("subject_id = %s")
                params.append(subject_id)

            if updates:
                params.append(topic_id)
                query = f"UPDATE topics SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)

# ----------------------------
# SCHEDULE
# ----------------------------

def get_schedule():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM schedule ORDER BY day_of_week, start_time")
            return cur.fetchall()

def add_schedule_entry(subject_id, day_of_week, start_time, end_time):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO schedule (subject_id, day_of_week, start_time, end_time)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (subject_id, day_of_week, start_time, end_time))
            return cur.fetchone()['id']

# ----------------------------
# ATTACHMENTS
# ----------------------------

def get_attachments(task_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM attachments WHERE task_id=%s", (task_id,))
            return cur.fetchall()

def add_attachment(task_id, file_path, file_type):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO attachments (task_id, file_path, file_type)
                VALUES (%s, %s, %s) RETURNING id
            """, (task_id, file_path, file_type))
            return cur.fetchone()['id']

# ----------------------------
# REMINDERS
# ----------------------------

def get_reminders():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM reminders ORDER BY reminder_time")
            return cur.fetchall()

def add_reminder(task_id, reminder_time):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reminders (task_id, reminder_time)
                VALUES (%s, %s) RETURNING id
            """, (task_id, reminder_time))
            return cur.fetchone()['id']

# ----------------------------
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ----------------------------

def get_tasks_by_subject_and_date(subject_id, date):
    """Получает задания по предмету и дате"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM tasks 
                WHERE subject_id = %s AND DATE(due_date) = %s
                ORDER BY due_date
            """, (subject_id, date))
            return cur.fetchall()

# ----------------------------
# SCHEDULE FUNCTIONS
# ----------------------------

def get_schedule_with_subjects():
    """Получает расписание с информацией о предметах"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, sub.name as subject_name, sub.teacher_id, sub.classroom, sub.color,
                       t.full_name as teacher_name
                FROM schedule s 
                LEFT JOIN subjects sub ON s.subject_id = sub.id 
                LEFT JOIN teachers t ON sub.teacher_id = t.id
                ORDER BY s.day_of_week, s.start_time
            """)
            return cur.fetchall()

def get_schedule_by_day(day_of_week):
    """Получает расписание для конкретного дня"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, sub.name as subject_name, sub.teacher_id, sub.classroom, sub.color,
                       t.full_name as teacher_name
                FROM schedule s 
                LEFT JOIN subjects sub ON s.subject_id = sub.id 
                LEFT JOIN teachers t ON sub.teacher_id = t.id
                WHERE s.day_of_week = %s
                ORDER BY s.start_time
            """, (day_of_week,))
            return cur.fetchall()

def add_schedule_entry(subject_id, day_of_week, start_time, end_time):
    """Добавляет запись в расписание"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO schedule (subject_id, day_of_week, start_time, end_time)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (subject_id, day_of_week, start_time, end_time))
            return cur.fetchone()['id']

def update_schedule_entry(entry_id, subject_id=None, day_of_week=None, start_time=None, end_time=None):
    """Обновляет запись в расписании"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            params = []

            if subject_id is not None:
                updates.append("subject_id = %s")
                params.append(subject_id)
            if day_of_week is not None:
                updates.append("day_of_week = %s")
                params.append(day_of_week)
            if start_time is not None:
                updates.append("start_time = %s")
                params.append(start_time)
            if end_time is not None:
                updates.append("end_time = %s")
                params.append(end_time)

            if updates:
                params.append(entry_id)
                query = f"UPDATE schedule SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)

def delete_schedule_entry(entry_id):
    """Удаляет запись из расписания"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM schedule WHERE id = %s", (entry_id,))

def get_schedule_entry(entry_id):
    """Получает конкретную запись расписания"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, sub.name as subject_name, sub.teacher_id, sub.classroom, sub.color
                FROM schedule s 
                LEFT JOIN subjects sub ON s.subject_id = sub.id 
                WHERE s.id = %s
            """, (entry_id,))
            return cur.fetchone()


# В database.py добавим следующие функции:

def get_overdue_tasks():
    """Получает просроченные задачи (дедлайн прошел, статус не выполнен)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM tasks 
                WHERE due_date < NOW() 
                AND status != 'completed' 
                AND status != 'done'
                AND is_automatic_debt = FALSE
                AND (type IS NULL OR type != 'exam')
                ORDER BY due_date
            """)
            return cur.fetchall()


def move_task_to_debts(task_id):
    """Перемещает задачу в задолженности и помечает как автоматически созданную"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Получаем данные задачи
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()

            if not task:
                return False

            # Создаем задолженность на основе задачи
            debt_name = f"Просрочено: {task['title']}"
            work_type = task.get('type', 'просроченная задача')

            cur.execute("""
                INSERT INTO topics (name, subject_id, type)
                VALUES (%s, %s, %s) RETURNING id
            """, (debt_name, task.get('subject_id'), work_type))

            # Помечаем задачу как автоматически перемещенную в задолженности
            cur.execute("""
                UPDATE tasks SET is_automatic_debt = TRUE WHERE id = %s
            """, (task_id,))

            return True


def check_and_move_overdue_tasks():
    """Проверяет и перемещает все просроченные задачи в задолженности"""
    overdue_tasks = get_overdue_tasks()
    moved_count = 0

    for task in overdue_tasks:
        if move_task_to_debts(task['id']):
            moved_count += 1
            print(f"Перемещена просроченная задача: {task['title']}")

    return moved_count


def get_automatic_debts_count():
    """Получает количество автоматически созданных задолженностей"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count FROM topics 
                WHERE name LIKE 'Просрочено:%'
            """)
            return cur.fetchone()['count']

# ----------------------------
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ----------------------------

# Вызовите эту функцию после init_db()
try:
    init_db()
    add_missing_columns()
    print("DB: схема инициализирована")
except Exception as e:
    print("DB: не удалось инициализировать схему:", e)