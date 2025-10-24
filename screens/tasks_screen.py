from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from datetime import datetime, timedelta
from database import add_task, get_regular_tasks, delete_task, update_task, get_tasks, get_subjects


class CalendarDayButton(MDRectangleFlatButton):
    """Кнопка дня в календаре"""

    def __init__(self, day_info, on_select_callback, **kwargs):
        super().__init__(**kwargs)
        self.day_info = day_info
        self.on_select_callback = on_select_callback
        self.text = str(day_info['day'])
        self.size_hint = (1, 1)
        self.line_color = (0.9, 0.9, 0.9, 1)
        self.theme_text_color = "Custom"

        # Изначальное состояние
        self.is_selected = False
        self.update_appearance()

    def update_appearance(self):
        """Обновляет внешний вид кнопки"""
        if self.day_info['month'] != 'current':
            # Дни других месяцев - всегда серые
            self.text_color = (0.7, 0.7, 0.7, 1)
            self.md_bg_color = (0.95, 0.95, 0.95, 1)
        elif self.is_selected:
            # Выбранный день текущего месяца - фиолетовый
            self.md_bg_color = (0.5, 0.3, 0.7, 1)
            self.text_color = (1, 1, 1, 1)
        else:
            # Обычный день текущего месяца - белый
            self.md_bg_color = (1, 1, 1, 1)
            self.text_color = (0.2, 0.2, 0.2, 1)

    def on_release(self):
        """Обработчик нажатия"""
        if self.day_info['month'] == 'current':
            self.on_select_callback(self.day_info)

    def on_enter(self):
        """При наведении курсора"""
        if self.day_info['month'] == 'current' and not self.is_selected:
            self.md_bg_color = (0.5, 0.3, 0.7, 0.3)  # Полупрозрачный фиолетовый
            self.text_color = (0.5, 0.3, 0.7, 1)  # Фиолетовый текст

    def on_leave(self):
        """При уходе курсора"""
        if self.day_info['month'] == 'current' and not self.is_selected:
            self.update_appearance()  # Возвращаем обычный вид

    def set_selected(self, selected):
        """Устанавливает состояние выбора"""
        self.is_selected = selected
        self.update_appearance()


class TasksScreen(Screen):
    editing_task_id = None
    has_tasks = BooleanProperty(False)
    selected_subject = StringProperty("")
    selected_subject_id = StringProperty("")
    deadline_date = StringProperty("")

    # Свойства для кастомного календаря
    current_picker_year = NumericProperty(2025)
    current_picker_month = NumericProperty(10)
    selected_picker_date = None

    def on_pre_enter(self):
        """Загрузка списка ТОЛЬКО обычных задач при открытии экрана"""
        # АВТОМАТИЧЕСКАЯ ПРОВЕРКА ПРОСРОЧЕННЫХ ЗАДАЧ
        self.check_overdue_tasks()

        self.cancel_edit()
        self.load_tasks()
        self.update_subject_button_text()
        self.update_deadline_button_text()

    def check_overdue_tasks(self):
        """Проверяет и перемещает просроченные задачи в задолженности"""
        try:
            from database import check_and_move_overdue_tasks
            moved_count = check_and_move_overdue_tasks()

            if moved_count > 0:
                # Показываем уведомление о перемещенных задачах
                self.show_info(f"Автоматически перемещено {moved_count} просроченных задач в задолженности")

        except Exception as e:
            print(f"Ошибка при проверке просроченных задач: {e}")

    def show_info(self, message):
        """Показывает информационное сообщение"""
        self.dialog = MDDialog(
            title="Информация",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.buttons[0].md_bg_color = (0.3, 0.5, 0.7, 1)  # Синий цвет
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (1, 1, 1, 1)
        self.dialog.open()

    def update_subject_button_text(self):
        """Обновляет текст кнопки выбора предмета"""
        if hasattr(self, 'ids') and 'subject_dropdown_btn' in self.ids:
            if self.selected_subject:
                self.ids.subject_dropdown_btn.text = self.selected_subject
            else:
                self.ids.subject_dropdown_btn.text = "Выберите предмет"

    def update_deadline_button_text(self):
        """Обновляет текст кнопки выбора дедлайна"""
        if hasattr(self, 'ids') and 'deadline_btn' in self.ids:
            if self.deadline_date:
                self.ids.deadline_btn.text = self.deadline_date
            else:
                self.ids.deadline_btn.text = "Выберите дедлайн"

    def get_available_subjects(self):
        """Получает список предметов из базы данных"""
        try:
            subjects = get_subjects()
            return subjects
        except Exception as e:
            print(f"Ошибка при загрузке предметов: {e}")
            return []

    def open_subject_dropdown(self):
        """Открывает выпадающий список предметов"""
        subjects = self.get_available_subjects()

        menu_items = [
            {
                "text": subject["name"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=subject: self.select_subject(x),
            } for subject in subjects
        ]

        # Добавляем опцию "Без предмета"
        menu_items.append({
            "text": "Без предмета",
            "viewclass": "OneLineListItem",
            "on_release": lambda x=None: self.select_subject(None),
        })

        self.subject_menu = MDDropdownMenu(
            caller=self.ids.subject_dropdown_btn,
            items=menu_items,
            width_mult=4,
            max_height=dp(200)
        )
        self.subject_menu.open()

    def select_subject(self, subject):
        """Выбирает предмет из списка"""
        if subject is None:
            self.selected_subject = ""
            self.selected_subject_id = ""
        else:
            self.selected_subject = subject["name"]
            self.selected_subject_id = str(subject["id"])

        self.update_subject_button_text()

        if hasattr(self, 'subject_menu'):
            self.subject_menu.dismiss()

    def open_date_picker(self):
        """Открывает кастомный диалог выбора даты"""
        self.show_custom_date_picker()

    def show_custom_date_picker(self):
        """Показывает кастомный диалог выбора даты на русском"""
        # Закрываем предыдущий диалог если есть
        if hasattr(self, 'date_dialog') and self.date_dialog:
            self.date_dialog.dismiss()

        # Текущая дата
        now = datetime.now()
        self.current_picker_year = now.year
        self.current_picker_month = now.month
        self.selected_picker_date = None

        # Создаем контент
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15),
            adaptive_height=True,
            size_hint_y=None,
            padding=dp(20)
        )
        content.height = dp(450)

        # Заголовок
        header = MDLabel(
            text="ВЫБЕРИТЕ ДАТУ",
            font_style="H5",
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(header)

        # Выбор месяца и года
        month_year_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        # Кнопка предыдущий месяц
        prev_btn = MDFlatButton(
            text="<",
            theme_text_color="Custom",
            text_color=(0.5, 0.3, 0.7, 1),
            font_style="H5",
            on_release=lambda x: self.change_picker_month(-1)
        )
        month_year_layout.add_widget(prev_btn)

        # Текущий месяц и год
        self.picker_month_label = MDLabel(
            text=self.get_russian_month_year(self.current_picker_month, self.current_picker_year),
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            size_hint_x=1,
            bold=True
        )
        month_year_layout.add_widget(self.picker_month_label)

        # Кнопка следующий месяц
        next_btn = MDFlatButton(
            text=">",
            theme_text_color="Custom",
            text_color=(0.5, 0.3, 0.7, 1),
            font_style="H5",
            on_release=lambda x: self.change_picker_month(1)
        )
        month_year_layout.add_widget(next_btn)

        content.add_widget(month_year_layout)

        # Дни недели
        week_days_layout = MDGridLayout(
            cols=7,
            spacing=dp(2),
            size_hint_y=None,
            height=dp(30)
        )

        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for day in week_days:
            week_days_layout.add_widget(MDLabel(
                text=day,
                halign="center",
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.5, 0.3, 0.7, 1)
            ))

        content.add_widget(week_days_layout)

        # Календарь
        self.calendar_container = MDGridLayout(
            cols=7,
            spacing=dp(2),
            adaptive_height=True,
            size_hint_y=None,
            height=dp(200)
        )
        self.update_calendar_days()
        content.add_widget(self.calendar_container)

        # Выбранная дата
        self.selected_date_label = MDLabel(
            text="Дата не выбрана",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(self.selected_date_label)

        # Кнопки
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(20)
        )

        cancel_btn = MDFlatButton(
            text="ОТМЕНА",
            theme_text_color="Custom",
            text_color=(0.5, 0.3, 0.7, 1),
            on_release=lambda x: self.date_dialog.dismiss()
        )

        ok_btn = MDRaisedButton(
            text="ВЫБРАТЬ",
            md_bg_color=(0.5, 0.3, 0.7, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            on_release=self.confirm_date_selection
        )

        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(ok_btn)
        content.add_widget(buttons_layout)

        # Создаем диалог
        self.date_dialog = MDDialog(
            type="custom",
            content_cls=content,
            size_hint=(0.8, None),
            height=dp(500),
            md_bg_color=(0.98, 0.98, 1, 1),
            radius=[25, 25, 25, 25],
            elevation=8
        )

        self.date_dialog.open()

    def get_russian_month_year(self, month, year):
        """Возвращает месяц и год на русском"""
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return f"{months[month - 1]} {year}"

    def change_picker_month(self, delta):
        """Изменяет месяц в календаре"""
        self.current_picker_month += delta
        if self.current_picker_month > 12:
            self.current_picker_month = 1
            self.current_picker_year += 1
        elif self.current_picker_month < 1:
            self.current_picker_month = 12
            self.current_picker_year -= 1

        self.picker_month_label.text = self.get_russian_month_year(
            self.current_picker_month, self.current_picker_year
        )
        self.update_calendar_days()

    def update_calendar_days(self):
        """Обновляет дни в календаре"""
        if not hasattr(self, 'calendar_container'):
            return

        self.calendar_container.clear_widgets()

        # Сохраняем ссылки на кнопки для управления выделением
        self.day_buttons = []

        # Генерируем дни месяца
        calendar_days = self.generate_calendar_days(self.current_picker_year, self.current_picker_month)

        for day_info in calendar_days:
            btn = CalendarDayButton(
                day_info=day_info,
                on_select_callback=self.on_day_selected,
                size_hint_y=None,
                height=dp(35)
            )
            self.day_buttons.append(btn)
            self.calendar_container.add_widget(btn)

        # Если есть выбранная дата в этом месяце, выделяем её
        if hasattr(self, 'selected_picker_date') and self.selected_picker_date:
            for btn in self.day_buttons:
                if (btn.day_info['month'] == 'current' and
                        hasattr(btn.day_info, 'get') and
                        btn.day_info.get('date') == self.selected_picker_date):
                    btn.set_selected(True)
                    break

    def generate_calendar_days(self, year, month):
        """Генерирует дни для календаря"""
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # Дни предыдущего месяца
        days_before = (first_day.weekday() + 1) % 7  # Пн=0, Вс=6
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
                'month': 'prev'
            })

        # Добавляем дни текущего месяца (УБРАЛИ выделение сегодняшнего дня)
        for day in range(1, last_day.day + 1):
            current_date = datetime(year, month, day).date()

            calendar_days.append({
                'day': day,
                'month': 'current',
                'date': current_date
            })

        # Добавляем дни следующего месяца
        days_after = 42 - len(calendar_days)
        for day in range(1, days_after + 1):
            calendar_days.append({
                'day': day,
                'month': 'next'
            })

        return calendar_days

    def on_day_selected(self, day_info):
        """Обрабатывает выбор дня"""
        # Сбрасываем выделение у всех кнопок текущего месяца
        for btn in self.day_buttons:
            if hasattr(btn, 'set_selected') and btn.day_info['month'] == 'current':
                btn.set_selected(False)

        # Устанавливаем выделение для выбранной кнопки
        selected_btn = None
        for btn in self.day_buttons:
            if (btn.day_info['month'] == 'current' and
                    hasattr(btn.day_info, 'get') and
                    btn.day_info.get('date') == day_info['date']):
                btn.set_selected(True)
                selected_btn = btn
                break

        self.selected_picker_date = day_info['date']

        # Форматируем дату по-русски
        month_names = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]

        day = day_info['date'].day
        month = month_names[day_info['date'].month - 1]
        year = day_info['date'].year
        weekday = day_info['date'].strftime("%a")

        weekdays_ru = {
            "Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт",
            "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"
        }

        weekday_ru = weekdays_ru.get(weekday, weekday)
        self.selected_date_label.text = f"{weekday_ru}, {day} {month} {year}"

    def confirm_date_selection(self, instance):
        """Подтверждает выбор даты"""
        if not self.selected_picker_date:
            self.show_error("Выберите дату")
            return

        # Форматируем для отображения
        month_names = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]

        day = self.selected_picker_date.day
        month = month_names[self.selected_picker_date.month - 1]
        weekday = self.selected_picker_date.strftime("%a")

        weekdays_ru = {
            "Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт",
            "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"
        }

        weekday_ru = weekdays_ru.get(weekday, weekday)

        self.deadline_date = f"{weekday_ru}, {day} {month}"
        self.deadline_date_save = self.selected_picker_date.strftime("%Y-%m-%d")

        self.update_deadline_button_text()
        self.date_dialog.dismiss()

    def clear_deadline(self):
        """Очищает выбранный дедлайн"""
        self.deadline_date = ""
        if hasattr(self, 'deadline_date_save'):
            self.deadline_date_save = ""
        self.update_deadline_button_text()

    def load_tasks(self):
        """Загружает список ТОЛЬКО обычных учебных работ"""
        self.ids.list_container.clear_widgets()
        tasks = get_regular_tasks()

        # Фильтруем экзамены
        regular_tasks = [task for task in tasks if task.get('type') != 'exam']

        if not regular_tasks:
            # Если задач нет - показываем сообщение В list_container
            self.show_empty_message()
        else:
            # Если есть задачи - показываем их
            for task in regular_tasks:
                self.add_task_to_list(task)

    def show_empty_message(self):
        """Показывает сообщение когда задач нет"""
        empty_card = MDCard(
            orientation="vertical",
            padding=dp(20),
            size_hint_y=None,
            height=dp(120),
            elevation=2,
            md_bg_color=(0.95, 0.95, 0.95, 1)
        )

        content = MDBoxLayout(orientation="vertical", spacing=dp(10))

        content.add_widget(MDLabel(
            text="Пока нет задач",
            theme_text_color="Secondary",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        ))

        content.add_widget(MDLabel(
            text="Добавьте первую задачу используя форму выше",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(25)
        ))

        empty_card.add_widget(content)
        self.ids.list_container.add_widget(empty_card)

    def add_task_to_list(self, task_data):
        """Добавляет одну учебную работу в список с кнопками редактирования и удаления"""
        task_id = task_data['id']
        title = task_data.get('title', 'Без названия')
        task_type = task_data.get('type', 'не указан')
        subject_id = task_data.get('subject_id')
        description = task_data.get('description', '')
        status = task_data.get('status', 'активно')
        due_date = task_data.get('due_date')

        # Создаем карточку задачи
        card = MDCard(
            orientation="vertical",
            padding=dp(20),
            size_hint_y=None,
            height=dp(200),
            elevation=3
        )

        # Основной контент
        content = MDBoxLayout(orientation="vertical", spacing=dp(8))

        # Заголовок
        title_label = MDLabel(
            text=f"{title}",
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            font_style="H6",
            size_hint_y=None,
            height=dp(30),
            bold=True
        )

        # Тип работы
        display_type = task_type if task_type != 'exam' else 'задача'
        type_label = MDLabel(
            text=f"Тип: {display_type}",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None,
            height=dp(25)
        )

        # ПРЕДМЕТ
        subject_name = "Не указан"
        if subject_id:
            subject = self.get_subject_by_id(subject_id)
            if subject:
                subject_name = subject['name']

        subject_label = MDLabel(
            text=f"Предмет: {subject_name}",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None,
            height=dp(25)
        )

        # ДЕДЛАЙН (если есть)
        deadline_label = None
        if due_date:
            try:
                if isinstance(due_date, str):
                    deadline_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                else:
                    deadline_date = due_date.strftime("%d.%m.%Y")

                deadline_label = MDLabel(
                    text=f"Дедлайн: {deadline_date}",
                    theme_text_color="Custom",
                    text_color=(0.8, 0.2, 0.2, 1) if due_date < datetime.now() else (0.2, 0.6, 0.2, 1),
                    size_hint_y=None,
                    height=dp(25),
                    bold=True if due_date < datetime.now() else False
                )
            except Exception as e:
                print(f"Ошибка при форматировании даты: {e}")

        content.add_widget(title_label)
        content.add_widget(type_label)
        content.add_widget(subject_label)

        if deadline_label:
            content.add_widget(deadline_label)

        # Описание
        if description and "Предмет:" not in description:
            desc_label = MDLabel(
                text=f"{description}",
                theme_text_color="Custom",
                text_color=(0.3, 0.3, 0.4, 1),
                size_hint_y=None,
                height=dp(25)
            )
            content.add_widget(desc_label)

        # Кнопки действий
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        edit_btn = MDRaisedButton(
            text="Редактировать",
            size_hint_x=0.5,
            on_release=lambda x, task_id=task_id: self.edit_task(task_id)
        )
        edit_btn.md_bg_color = (0.5, 0.3, 0.7, 1)
        edit_btn.theme_text_color = "Custom"
        edit_btn.text_color = (1, 1, 1, 1)

        delete_btn = MDRaisedButton(
            text="Удалить",
            size_hint_x=0.5,
            on_release=lambda x, task_id=task_id: self.delete_task_dialog(task_id, title)
        )
        delete_btn.md_bg_color = (0.8, 0.2, 0.2, 1)
        delete_btn.theme_text_color = "Custom"
        delete_btn.text_color = (1, 1, 1, 1)

        buttons_layout.add_widget(edit_btn)
        buttons_layout.add_widget(delete_btn)

        card.add_widget(content)
        card.add_widget(buttons_layout)
        self.ids.list_container.add_widget(card)

    def get_subject_by_id(self, subject_id):
        """Получает предмет по ID"""
        try:
            subjects = self.get_available_subjects()
            for subject in subjects:
                if str(subject['id']) == str(subject_id):
                    return subject
            return None
        except Exception as e:
            print(f"Ошибка при получении предмета: {e}")
            return None

    def add_task(self):
        """Добавляет или обновляет учебную работу (НЕ экзамен)"""
        title = self.ids.input_task.text.strip()
        work_type = self.ids.input_type.text.strip()

        if not title:
            self.show_error("Введите название задачи")
            return

        # Формируем описание
        description = ""
        if self.selected_subject:
            description = f"Предмет: {self.selected_subject}"

        # Убеждаемся, что это НЕ экзамен
        if work_type and work_type.lower() in ['exam', 'экзамен']:
            self.show_error("Для добавления экзамена используйте экран экзаменов")
            return

        # Преобразуем дату дедлайна в формат для базы данных
        due_date = None
        if hasattr(self, 'deadline_date_save') and self.deadline_date_save:
            try:
                due_date = datetime.strptime(self.deadline_date_save, "%Y-%m-%d")
            except ValueError:
                self.show_error("Неверный формат даты дедлайна")
                return
        elif hasattr(self, 'deadline_date') and self.deadline_date:
            try:
                due_date = datetime.strptime(self.deadline_date, "%d.%m.%Y")
            except ValueError:
                self.show_error("Неверный формат даты дедлайна")
                return

        # Используем английские статусы для consistency
        task_type = work_type if work_type else 'task'

        if self.editing_task_id:
            # Режим редактирования
            try:
                update_task(
                    task_id=self.editing_task_id,
                    title=title,
                    description=description,
                    task_type=task_type,
                    subject_id=self.selected_subject_id if self.selected_subject_id else None,
                    due_date=due_date
                )
                self.show_success("Задача обновлена")
            except Exception as e:
                self.show_error(f"Ошибка при обновлении: {e}")
        else:
            # Режим добавления
            try:
                task_id = add_task(
                    title=title,
                    description=description,
                    task_type=task_type,
                    status='active',
                    subject_id=self.selected_subject_id if self.selected_subject_id else None,
                    due_date=due_date
                )
                print(f"Задача добавлена с ID: {task_id}")
                self.show_success("Задача добавлена")
            except Exception as e:
                self.show_error(f"Ошибка при добавлении: {e}")

        # Обновляем список и сбрасываем форму
        self.load_tasks()
        self.cancel_edit()

    def edit_task(self, task_id):
        """Редактирование учебной работы"""
        tasks = get_regular_tasks()
        task_to_edit = None

        for task in tasks:
            if task['id'] == task_id:
                task_to_edit = task
                break

        if not task_to_edit:
            self.show_error("Задача не найдена")
            return

        # Заполняем поля формы данными задачи
        self.ids.input_task.text = task_to_edit.get('title', '')

        task_type = task_to_edit.get('type', '')
        if task_type == 'exam':
            self.ids.input_type.text = ''
        else:
            self.ids.input_type.text = task_type

        # Устанавливаем предмет из базы данных
        subject_id = task_to_edit.get('subject_id')
        if subject_id:
            subject = self.get_subject_by_id(subject_id)
            if subject:
                self.selected_subject = subject['name']
                self.selected_subject_id = str(subject['id'])
        else:
            # Извлекаем предмет из описания
            description = task_to_edit.get('description', '')
            if description and "Предмет:" in description:
                old_subject = description.replace("Предмет:", "").strip()
                self.selected_subject = old_subject
                self.selected_subject_id = ""

        # Устанавливаем дедлайн
        due_date = task_to_edit.get('due_date')
        if due_date:
            try:
                if isinstance(due_date, str):
                    self.deadline_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                else:
                    self.deadline_date = due_date.strftime("%d.%m.%Y")
            except Exception as e:
                print(f"Ошибка при установке дедлайна: {e}")
                self.deadline_date = ""
        else:
            self.deadline_date = ""

        self.update_subject_button_text()
        self.update_deadline_button_text()

        # Устанавливаем режим редактирования
        self.editing_task_id = task_id
        self.ids.add_button.text = "Сохранить изменения"

        self.show_success("Режим редактирования. Измените данные и нажмите 'Сохранить изменения'")

    def delete_task_dialog(self, task_id, task_title):
        """Диалог подтверждения удаления"""
        self.dialog = MDDialog(
            title="Удаление задачи",
            text=f"Вы уверены, что хотите удалить задачу:\n\"{task_title}\"?",
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Удалить",
                    on_release=lambda x: self.delete_task(task_id)
                )
            ]
        )
        # Устанавливаем цвета для кнопок диалога
        self.dialog.buttons[0].md_bg_color = (0.8, 0.7, 0.9, 1)
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (0.4, 0.2, 0.6, 1)

        self.dialog.buttons[1].md_bg_color = (0.8, 0.2, 0.2, 1)
        self.dialog.buttons[1].theme_text_color = "Custom"
        self.dialog.buttons[1].text_color = (1, 1, 1, 1)

        self.dialog.open()

    def delete_task(self, task_id):
        """Удаляет задачу"""
        try:
            delete_task(task_id)
            self.dialog.dismiss()
            self.load_tasks()
            self.show_success("Задача удалена")
        except Exception as e:
            self.show_error(f"Ошибка при удалении: {e}")

    def cancel_edit(self):
        """Сбрасывает режим редактирования"""
        self.editing_task_id = None
        self.ids.add_button.text = "Добавить работу"
        self.ids.input_task.text = ""
        self.ids.input_type.text = ""
        self.selected_subject = ""
        self.selected_subject_id = ""

        # Сбрасываем даты
        self.deadline_date = ""
        if hasattr(self, 'deadline_date_save'):
            self.deadline_date_save = ""

        self.update_subject_button_text()
        self.update_deadline_button_text()

    def debug_check_database(self):
        """Проверка всех задач в базе"""
        all_tasks = get_tasks()
        print("=== ВСЕ ЗАДАЧИ В БАЗЕ ===")
        for task in all_tasks:
            print(
                f"ID: {task['id']}, Название: {task['title']}, Тип: {task.get('type', 'не указан')}, Статус: {task.get('status')}, Дедлайн: {task.get('due_date')}")
        print("=========================")

    def show_error(self, message):
        """Показывает сообщение об ошибке"""
        self.dialog = MDDialog(
            title="Ошибка",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.buttons[0].md_bg_color = (0.5, 0.3, 0.7, 1)
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (1, 1, 1, 1)
        self.dialog.open()

    def show_success(self, message):
        """Показывает сообщение об успехе"""
        self.dialog = MDDialog(
            title="Успешно",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.buttons[0].md_bg_color = (0.5, 0.3, 0.7, 1)
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (1, 1, 1, 1)
        self.dialog.open()