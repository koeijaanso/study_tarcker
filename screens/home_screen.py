from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineListItem, OneLineAvatarListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from datetime import datetime, timedelta
from database import get_connection
from kivy.metrics import dp



class CalendarDayButton(MDFlatButton):
    """Кнопка дня в календаре"""

    def __init__(self, day, has_events=False, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.has_events = has_events
        self.text = str(day)
        self.size_hint = (1, 1)
        self.font_size = '14sp'

        # Подсветка дней с событиями
        if has_events:
            self.md_bg_color = (0.2, 0.6, 0.8, 0.3)


class HomeScreen(Screen):
    title = StringProperty("Главный экран")
    today_tasks = ListProperty([])
    upcoming_deadlines = ListProperty([])
    next_exam = ListProperty([])

    # Свойства для календаря со значениями по умолчанию
    current_month = NumericProperty(datetime.now().month)
    current_year = NumericProperty(datetime.now().year)
    calendar_days = ListProperty([])

    def on_pre_enter(self):
        self.init_calendar()
        self.load_all_sections()
        self.debug_check_all_tasks()

    def get_event_type_text(self, event_type):
        """Получить читаемое название типа события"""
        type_map = {
            'exam': 'Экзамен',
            'homework': 'Домашняя работа',
            'lecture': 'Лекция',
            'practice': 'Практика',
            'other': 'Задача'
        }
        return type_map.get(event_type, 'Событие')

    def get_events_for_date(self, date):
        """Получить все события для указанной даты"""
        try:
            print(f"🔍 Ищем события для даты: {date}")

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        LEFT JOIN subjects s ON t.subject_id = s.id 
                        WHERE t.due_date::date = %s 
                        AND t.status != 'completed'
                        ORDER BY 
                            CASE 
                                WHEN t.type = 'exam' THEN 1
                                ELSE 2 
                            END,
                            t.due_date ASC
                    """, (date,))
                    events = cur.fetchall()

                    print(f"📅 Найдено событий: {len(events)}")
                    for event in events:
                        print(f"   - {event['title']} ({event.get('type', 'no type')})")

                    return [dict(event) for event in events]
        except Exception as e:
            print(f"❌ Ошибка загрузки событий для даты {date}: {e}")
            return []

    def on_day_selected(self, day_info):
        """Обработка выбора дня в календаре"""
        if day_info['month'] == 'current':
            selected_date = day_info['date']
            print(f"🎯 Выбран день: {selected_date}")

            # Получаем события для выбранной даты
            events = self.get_events_for_date(selected_date)

            # Показываем диалог с событиями
            self.show_day_events_dialog(selected_date, events)

    # Вместо импорта MDDivider, добавьте этот метод в класс HomeScreen:
    def create_divider(self):
        """Создает простой разделитель"""
        from kivy.uix.widget import Widget
        divider = Widget(
            size_hint_y=None,
            height=dp(1),
            canvas_color=(0.9, 0.9, 0.9, 1)
        )

        # Добавляем линию на canvas
        from kivy.graphics import Color, Line
        with divider.canvas:
            Color(0.9, 0.9, 0.9, 1)
            Line(points=[dp(10), 0, divider.width - dp(10), 0], width=dp(1))

        return divider

    def show_day_events_dialog(self, date, events):
        """Показать красивый диалог с событиями дня"""
        print(f"🔄 Создаем диалог для {date}, событий: {len(events)}")

        # Закрываем предыдущий диалог, если он есть
        if hasattr(self, 'day_events_dialog') and self.day_events_dialog:
            self.day_events_dialog.dismiss()

        # Создаем красивый контент для диалога
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15),
            adaptive_height=True,
            size_hint_y=None,
            padding=dp(10)
        )

        # Красивый заголовок с датой
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(15)
        )

        # Иконка календаря
        from kivymd.uix.label import MDIcon
        header_layout.add_widget(MDIcon(
            icon="calendar",
            size_hint_x=None,
            width=dp(40),
            theme_text_color="Custom",
            text_color=(0.5, 0.3, 0.7, 1)
        ))

        # Текст заголовка
        header_text = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )
        header_text.add_widget(MDLabel(
            text="События дня",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            size_hint_y=None,
            height=dp(25)
        ))
        header_text.add_widget(MDLabel(
            text=date.strftime('%d.%m.%Y'),
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=(0.6, 0.6, 0.7, 1),
            size_hint_y=None,
            height=dp(20)
        ))

        header_layout.add_widget(header_text)
        header_layout.add_widget(MDLabel(size_hint_x=0.2))
        content.add_widget(header_layout)

        # Разделитель
        content.add_widget(self.create_simple_divider())

        if not events:
            # Сообщение когда событий нет
            empty_message = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(80),
                spacing=dp(10)
            )

            empty_message.add_widget(MDIcon(
                icon="calendar-remove",
                size_hint_y=None,
                height=dp(40),
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.8, 1)
            ))

            empty_message.add_widget(MDLabel(
                text="Событий нет",
                font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.6, 0.6, 0.7, 1),
                halign="center",
                size_hint_y=None,
                height=dp(25)
            ))

            content.add_widget(empty_message)
            content.height = dp(150)  # Фиксированная высота для пустого состояния
        else:
            # Список событий с иконками
            for event in events:
                event_item = self.create_event_list_item(event)
                content.add_widget(event_item)

            content.height = dp(80 + len(events) * 70)  # Высота зависит от количества событий

        # Создаем красивый диалог
        self.day_events_dialog = MDDialog(
            type="custom",
            content_cls=content,
            size_hint=(0.85, None),
            height=content.height + dp(100),  # Добавляем место для кнопок
            md_bg_color=(0.98, 0.98, 1, 1),
            radius=[25, 25, 25, 25],
            elevation=8,
            buttons=[
                MDFlatButton(
                    text="[color=5A2D8C]ЗАКРЫТЬ[/color]",
                    theme_text_color="Custom",
                    on_release=lambda x: self.day_events_dialog.dismiss()
                ),
            ],
        )

        print("✅ Красивый диалог создан, открываем...")
        self.day_events_dialog.open()

    def create_simple_divider(self):
        """Создает простой разделитель"""
        from kivy.uix.widget import Widget
        divider = Widget(
            size_hint_y=None,
            height=dp(1)
        )

        # Рисуем линию
        from kivy.graphics import Color, Rectangle
        with divider.canvas:
            Color(0.9, 0.9, 0.9, 1)
            Rectangle(pos=(dp(10), 0), size=(divider.width - dp(20), dp(1)))

        return divider

    def create_event_list_item(self, event):
        """Создает красивый элемент списка событий"""
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel, MDIcon

        # Основной контейнер
        item = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=dp(15),
            padding=dp(10),
            md_bg_color=(0.95, 0.95, 0.98, 1),
            radius=[10, 10, 10, 10]
        )

        # Иконка в зависимости от типа события
        icon_name = self.get_event_icon(event.get('type', 'other'))
        item.add_widget(MDIcon(
            icon=icon_name,
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=self.get_event_color(event.get('type', 'other'))
        ))

        # Текстовая информация
        text_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )

        # Основной текст
        text_layout.add_widget(MDLabel(
            text=event['title'],
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.3, 1),
            size_hint_y=None,
            height=dp(25),
            shorten=True,
            shorten_from='right'
        ))

        # Вторичный текст - исправляем отображение None
        subject_name = event.get('subject_name', 'Без предмета')
        if subject_name is None:
            subject_name = 'Без предмета'

        secondary_text = f"{subject_name} | {self.get_event_type_text(event.get('type'))}"
        text_layout.add_widget(MDLabel(
            text=secondary_text,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.6, 1),
            size_hint_y=None,
            height=dp(20)
        ))

        item.add_widget(text_layout)

        # Добавляем обработчик нажатия
        item.bind(on_touch_down=lambda instance, touch: self.on_event_item_pressed(instance, touch, event))

        return item

    def get_event_icon(self, event_type):
        """Возвращает иконку для типа события"""
        icons = {
            'exam': 'school',
            'homework': 'book-open-page-variant',
            'lecture': 'presentation',
            'practice': 'code-tags',
            'other': 'calendar-check'
        }
        return icons.get(event_type, 'calendar-check')

    def get_event_color(self, event_type):
        """Возвращает цвет для типа события"""
        colors = {
            'exam': (0.8, 0.2, 0.2, 1),
            'homework': (0.2, 0.6, 0.8, 1),
            'lecture': (0.3, 0.7, 0.3, 1),
            'practice': (0.9, 0.6, 0.1, 1),
            'other': (0.5, 0.3, 0.7, 1)
        }
        return colors.get(event_type, (0.5, 0.3, 0.7, 1))

    def on_event_item_pressed(self, instance, touch, event):
        """Обработчик нажатия на элемент события"""
        if instance.collide_point(*touch.pos):
            self.view_task_details(event)
            return True
        return False

    def init_calendar(self):
        """Инициализация календаря текущим месяцем"""
        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year
        self.update_calendar()

    def update_calendar(self):
        """Обновление отображения календаря"""
        # Получаем задачи для определения дней с событиями
        month_tasks = self.get_tasks_for_month(self.current_year, self.current_month)

        # Создаем календарь
        self.generate_calendar_days(self.current_year, self.current_month, month_tasks)

        # Обновляем UI календаря
        self.update_calendar_ui()

    def get_tasks_for_month(self, year, month):
        """Получаем задачи для указанного месяца"""
        try:
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT due_date::date as task_date, COUNT(*) as task_count
                        FROM tasks 
                        WHERE due_date::date BETWEEN %s AND %s 
                        AND status != 'completed'
                        GROUP BY due_date::date
                    """, (start_date, end_date))
                    tasks = cur.fetchall()
                    return {task['task_date']: task['task_count'] for task in tasks}
        except Exception as e:
            print(f"Ошибка загрузки задач для календаря: {e}")
            return {}

    def generate_calendar_days(self, year, month, month_tasks):
        """Генерация дней календаря"""
        # Первый день месяца
        first_day = datetime(year, month, 1)
        # Последний день месяца
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # Дни предыдущего месяца
        days_before = first_day.weekday()
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1

        if prev_month == 12:
            prev_last_day = datetime(prev_year, prev_month, 31)
        else:
            prev_last_day = datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)

        calendar_days = []

        # Добавляем дни предыдущего месяца
        for day in range(prev_last_day.day - days_before + 1, prev_last_day.day + 1):
            calendar_days.append({
                'day': day,
                'month': 'prev',
                'has_events': False
            })

        # Добавляем дни текущего месяца
        today = datetime.now().date()
        for day in range(1, last_day.day + 1):
            current_date = datetime(year, month, day).date()
            has_events = current_date in month_tasks
            is_today = current_date == today

            calendar_days.append({
                'day': day,
                'month': 'current',
                'has_events': has_events,
                'is_today': is_today,
                'date': current_date
            })

        # Добавляем дни следующего месяца
        days_after = 42 - len(calendar_days)  # 6 недель по 7 дней
        for day in range(1, days_after + 1):
            calendar_days.append({
                'day': day,
                'month': 'next',
                'has_events': False
            })

        self.calendar_days = calendar_days

    def update_calendar_ui(self):
        """Обновление UI календаря"""
        if not hasattr(self, 'ids') or 'calendar_grid' not in self.ids:
            return

        container = self.ids.calendar_grid
        container.clear_widgets()

        # Добавляем заголовки дней недели
        week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for day in week_days:
            container.add_widget(MDLabel(
                text=day,
                halign='center',
                font_style='Caption',
                size_hint_y=None,
                height=30
            ))

        # Добавляем дни календаря
        for day_info in self.calendar_days:
            if day_info['month'] == 'current':
                btn = CalendarDayButton(
                    day=day_info['day'],
                    has_events=day_info['has_events'],
                    on_release=lambda x, d=day_info: self.on_day_selected(d)
                )
                # Подсветка сегодняшнего дня
                if day_info.get('is_today', False):
                    btn.md_bg_color = (0.2, 0.8, 0.2, 0.3)
            else:
                btn = MDLabel(
                    text=str(day_info['day']),
                    halign='center',
                    theme_text_color='Secondary',
                    size_hint_y=None,
                    height=40
                )
            container.add_widget(btn)

    def show_day_tasks(self, date):
        """Показать задачи на выбранный день"""
        print(f"Задачи на {date}")

    def prev_month(self):
        """Переход к предыдущему месяцу"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()

    def next_month(self):
        """Переход к следующему месяцу"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()

    def load_all_sections(self):
        """Загружаем все секции главного экрана"""
        self.load_today_tasks()
        self.load_upcoming_deadlines()
        self.load_next_exam()


    def load_today_tasks(self):
        """Задачи на сегодня/ближайшие 24 часа И активные задачи без дат (БЕЗ экзаменов)"""
        self.today_tasks = []
        today = datetime.now().date()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Задачи на сегодня ИЛИ активные задачи без дат ИЛИ задачи с дедлайном в будущем
                    cur.execute("""
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        LEFT JOIN subjects s ON t.subject_id = s.id 
                        WHERE (
                            (t.due_date::date = %s)  -- Задачи с датой на сегодня
                            OR 
                            (t.due_date IS NULL AND t.status = 'active')  -- Активные задачи без даты
                            OR
                            (t.due_date::date > %s AND t.status = 'active')  -- Задачи с дедлайном в будущем
                        )
                        AND t.status = 'active'
                        AND (t.type IS NULL OR t.type != 'exam')
                        ORDER BY 
                            CASE 
                                WHEN t.due_date IS NULL THEN 2
                                WHEN t.due_date::date = %s THEN 1  -- Сегодняшние задачи в первую очередь
                                ELSE 3 
                            END,
                            t.due_date ASC,
                            t.created_at DESC;
                    """, (today, today, today))
                    tasks = cur.fetchall()
                    self.today_tasks = [dict(task) for task in tasks]

                    # Отладочная информация
                    print(f"Загружено задач на сегодня: {len(self.today_tasks)}")
                    for task in self.today_tasks:
                        print(f"Задача: {task['title']}, дата: {task.get('due_date')}, статус: {task.get('status')}")

        except Exception as e:
            print(f"Ошибка загрузки задач на сегодня: {e}")
            self.today_tasks = []

        # Обновляем UI
        if hasattr(self, 'ids') and 'today_container' in self.ids:
            container = self.ids.today_container
            container.clear_widgets()

            if not self.today_tasks:
                container.add_widget(MDLabel(
                    text="На сегодня задач нет",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=40
                ))
            else:
                for task in self.today_tasks:
                    subject_name = task.get('subject_name', 'Без предмета')
                    if subject_name is None:
                        subject_name = ''

                    deadline_text = ""
                    days_text = ""

                    if task.get('due_date'):
                        try:
                            # Если due_date - это datetime объект
                            if isinstance(task['due_date'], datetime):
                                deadline_date = task['due_date'].date()
                                deadline_text = task['due_date'].strftime("(%d.%m.%Y)")
                            # Если due_date - это строка из базы данных
                            elif isinstance(task['due_date'], str):
                                deadline_date = datetime.strptime(task['due_date'], "%Y-%m-%d %H:%M:%S").date()
                                deadline_text = deadline_date.strftime("(%d.%m.%Y)")
                            # Если due_date - это date объект
                            else:
                                deadline_date = task['due_date']
                                deadline_text = task['due_date'].strftime("(%d.%m.%Y)")

                            # Рассчитываем сколько дней осталось
                            today = datetime.now().date()
                            days_left = (deadline_date - today).days

                            if days_left == 0:
                                days_text = " - сегодня"
                            elif days_left == 1:
                                days_text = " - завтра"
                            elif days_left > 1:
                                days_text = f" - через {days_left} дн."
                            else:
                                days_text = " - просрочено"

                        except Exception as e:
                            print(f"Ошибка форматирования даты: {e}")
                            deadline_text = "(ошибка даты)"
                    else:
                        deadline_text = "(без даты)"
                        days_text = ""

                    item = OneLineAvatarListItem(
                        text=f"{task['title']} - {subject_name} {deadline_text}{days_text}",
                        on_release=lambda x, t=task: self.view_task_details(t)
                    )

                    icon_name = self.get_icon_for_task_type(task.get('type', 'other'))
                    icon = IconLeftWidget(icon=icon_name)
                    item.add_widget(icon)
                    container.add_widget(item)

    def load_upcoming_deadlines(self):
        """Ближайшие дедлайны (7 дней) И недавно добавленные задачи"""
        self.upcoming_deadlines = []
        today = datetime.now().date()
        seven_days_later = today + timedelta(days=7)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Дедлайны на 7 дней вперед ИЛИ недавние задачи без дат
                    cur.execute("""
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        LEFT JOIN subjects s ON t.subject_id = s.id 
                        WHERE (
                            (t.due_date::date BETWEEN %s AND %s)  -- Задачи с датой в ближайшие 7 дней
                            OR 
                            (t.due_date IS NULL AND t.created_at >= NOW() - INTERVAL '3 days')  -- Недавние задачи без дат
                        )
                        AND t.status = 'active'
                        AND (t.type IS NULL OR t.type != 'exam')
                        ORDER BY 
                            CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END,
                            t.due_date ASC 
                        LIMIT 10;  -- Увеличим лимит
                    """, (today, seven_days_later))
                    tasks = cur.fetchall()
                    self.upcoming_deadlines = [dict(task) for task in tasks]

                    # Отладочная информация
                    print(f"Загружено ближайших дедлайнов: {len(self.upcoming_deadlines)}")

        except Exception as e:
            print(f"Ошибка загрузки дедлайнов: {e}")
            self.upcoming_deadlines = []

        # Обновляем UI
        if hasattr(self, 'ids') and 'deadlines_container' in self.ids:
            container = self.ids.deadlines_container
            container.clear_widgets()

            if not self.upcoming_deadlines:
                container.add_widget(MDLabel(
                    text="Ближайших дедлайнов нет",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=40
                ))
            else:
                for task in self.upcoming_deadlines:
                    days_left = 0
                    deadline_date = None

                    if task.get('due_date'):
                        try:
                            if isinstance(task['due_date'], datetime):
                                deadline_date = task['due_date'].date()
                            elif isinstance(task['due_date'], str):
                                deadline_date = datetime.strptime(task['due_date'], "%Y-%m-%d %H:%M:%S").date()
                            else:
                                deadline_date = task['due_date']

                            days_left = (deadline_date - today).days
                        except Exception as e:
                            print(f"Ошибка расчета дней: {e}")
                            days_left = 0

                    # ИСПРАВЛЕНИЕ: Если subject_name = None, то не отображаем его
                    subject_name = task.get('subject_name')
                    if subject_name is None:
                        subject_display = ""
                    else:
                        subject_display = f" - {subject_name}"

                    if task.get('due_date') is None:
                        days_text = "новая задача"
                    elif days_left == 0:
                        days_text = "сегодня"
                    elif days_left == 1:
                        days_text = "завтра"
                    else:
                        days_text = f"через {days_left} дн."

                    formatted_date = ""
                    if deadline_date:
                        formatted_date = deadline_date.strftime("(%d.%m.%Y) ")
                    elif task.get('due_date') is None:
                        formatted_date = ""

                    # Формируем текст с учетом наличия предмета
                    display_text = f"{task['title']}{subject_display} {formatted_date}{days_text}"

                    item = OneLineListItem(
                        text=display_text.strip(),  # Убираем лишние пробелы
                        on_release=lambda x, t=task: self.view_task_details(t)
                    )
                    container.add_widget(item)

    def load_next_exam(self):
        """Следующий экзамен"""
        self.next_exam = []
        today = datetime.now().date()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        LEFT JOIN subjects s ON t.subject_id = s.id 
                        WHERE t.type = 'exam' 
                        AND t.due_date::date >= %s 
                        AND t.status != 'completed'
                        ORDER BY t.due_date ASC 
                        LIMIT 1;
                    """, (today,))
                    exam = cur.fetchone()

                    if exam:
                        self.next_exam = [dict(exam)]
        except Exception as e:
            print(f"Ошибка загрузки экзаменов: {e}")
            self.next_exam = []

        # Обновляем UI
        if hasattr(self, 'ids') and 'exam_container' in self.ids:
            container = self.ids.exam_container
            container.clear_widgets()

            if not self.next_exam:
                # Не добавляем никаких виджетов - секция сама скроется через свойства KV
                return
            else:
                exam_data = self.next_exam[0]
                days_left = 0
                if exam_data.get('due_date'):
                    try:
                        days_left = (exam_data['due_date'].date() - today).days
                    except:
                        days_left = 0

                subject_name = exam_data.get('subject_name')
                if not subject_name:  # Если subject_name = None или пустая строка
                    subject_name = ""  # Используем общее название

                exam_card = MDCard(
                    orientation="vertical",
                    padding=15,
                    size_hint_y=None,
                    height=120,
                    md_bg_color=(0.8, 0.2, 0.2, 1) if days_left <= 3 else (0.2, 0.6, 0.8, 1),
                    ripple_behavior=True,
                    on_release=lambda x: self.view_task_details(exam_data)
                )

                content = MDBoxLayout(orientation="vertical", spacing=5)
                content.add_widget(MDLabel(
                    text=f"Экзамен: {subject_name}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    font_style="H6",
                    size_hint_y=None,
                    height=30
                ))
                content.add_widget(MDLabel(
                    text=f"{exam_data['title']}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 0.9),
                    size_hint_y=None,
                    height=25
                ))

                exam_date = ""
                if exam_data.get('due_date'):
                    try:
                        exam_date = exam_data['due_date'].strftime("%d.%m.%Y")
                    except:
                        exam_date = "Дата не указана"

                if days_left == 0:
                    time_text = "Сегодня!"
                elif days_left == 1:
                    time_text = "Завтра!"
                else:
                    time_text = f"Через {days_left} дней"

                content.add_widget(MDLabel(
                    text=f"{exam_date} • {time_text}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 0.8),
                    font_style="Subtitle1",
                    size_hint_y=None,
                    height=25
                ))

                exam_card.add_widget(content)
                container.add_widget(exam_card)

    def get_icon_for_task_type(self, task_type):
        """Возвращает иконку в зависимости от типа задачи"""
        icons = {
            'exam': 'school',
            'homework': 'book',
            'lecture': 'presentation',
            'practice': 'code-tags',
            'other': 'format-list-checks'
        }
        return icons.get(task_type, 'format-list-checks')

    def view_task_details(self, task):
        """Просмотр деталей задачи"""
        print(f"Просмотр задачи: {task['title']}")

    def refresh_data(self):
        """Обновление всех данных"""
        self.load_all_sections()
        self.update_calendar()

    def debug_check_all_tasks(self):
        """Отладочная функция: проверяет все задачи в базе"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, title, type, due_date, status, created_at 
                        FROM tasks 
                        ORDER BY created_at DESC
                    """)
                    all_tasks = cur.fetchall()

                    print("=== ВСЕ ЗАДАЧИ В БАЗЕ ===")
                    for task in all_tasks:
                        print(f"ID: {task['id']}, Название: {task['title']}, Тип: {task.get('type', 'не указан')}, "
                              f"Дата: {task.get('due_date')}, Статус: {task.get('status')}, "
                              f"Создана: {task.get('created_at')}")
                    print("=========================")

        except Exception as e:
            print(f"Ошибка при проверке задач: {e}")


    def on_pre_enter(self):
        self.init_calendar()
        self.load_all_sections()
        self.debug_check_all_tasks()