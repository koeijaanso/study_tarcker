from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from datetime import datetime
from database import get_subjects, get_schedule_with_subjects, add_schedule_entry, \
    update_schedule_entry, delete_schedule_entry
from kivy.metrics import dp
from kivy.uix.modalview import ModalView


class CustomTimePicker(ModalView):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.3)
        self.background = ""

        # Основной контейнер
        main_layout = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            elevation=10,
            radius=dp(15),
            md_bg_color=(1, 1, 1, 1)
        )

        # Заголовок
        title_label = MDLabel(
            text='Выберите время',
            halign='center',
            font_style='H5',
            theme_text_color='Custom',
            text_color=(0.4, 0.2, 0.6, 1),
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        main_layout.add_widget(title_label)

        # Контейнер для времени - УБРАТЬ halign
        time_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(10)
        )

        # Поле часов
        hours_card = MDCard(
            orientation='vertical',
            size_hint=(0.3, 0.8),
            elevation=2,
            radius=dp(10),
            md_bg_color=(0.95, 0.93, 0.98, 1)
        )

        self.hours_label = MDLabel(
            text='09',
            halign='center',
            font_style='H4',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            bold=True
        )
        hours_card.add_widget(self.hours_label)

        hours_buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(2)
        )

        hours_up = MDIconButton(
            icon='chevron-up',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            on_press=self.increment_hours
        )
        hours_down = MDIconButton(
            icon='chevron-down',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            on_press=self.decrement_hours
        )

        hours_buttons.add_widget(hours_up)
        hours_buttons.add_widget(hours_down)
        hours_card.add_widget(hours_buttons)

        # Разделитель
        colon_label = MDLabel(
            text=':',
            halign='center',
            font_style='H4',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            size_hint_x=None,
            width=dp(20),
            bold=True
        )

        # Поле минут
        minutes_card = MDCard(
            orientation='vertical',
            size_hint=(0.3, 0.8),
            elevation=2,
            radius=dp(10),
            md_bg_color=(0.95, 0.93, 0.98, 1)
        )

        self.minutes_label = MDLabel(
            text='00',
            halign='center',
            font_style='H4',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            bold=True
        )
        minutes_card.add_widget(self.minutes_label)

        minutes_buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(2)
        )

        minutes_up = MDIconButton(
            icon='chevron-up',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            on_press=self.increment_minutes
        )
        minutes_down = MDIconButton(
            icon='chevron-down',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            on_press=self.decrement_minutes
        )

        minutes_buttons.add_widget(minutes_up)
        minutes_buttons.add_widget(minutes_down)
        minutes_card.add_widget(minutes_buttons)

        # Добавляем все в контейнер времени
        time_container.add_widget(hours_card)
        time_container.add_widget(colon_label)
        time_container.add_widget(minutes_card)

        main_layout.add_widget(time_container)

        # Кнопки действий
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(15)
        )

        cancel_btn = MDFlatButton(
            text='Отмена',
            theme_text_color='Custom',
            text_color=(0.5, 0.3, 0.7, 1),
            on_press=self.dismiss
        )

        ok_btn = MDRaisedButton(
            text='OK',
            md_bg_color=(0.5, 0.3, 0.7, 1),
            theme_text_color='Custom',
            text_color=(1, 1, 1, 1),
            on_press=self.set_time
        )

        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(ok_btn)
        main_layout.add_widget(buttons_layout)

        self.add_widget(main_layout)

        # Текущее время
        self.current_hours = 9
        self.current_minutes = 0

    def increment_hours(self, instance):
        """Увеличивает часы"""
        self.current_hours = (self.current_hours + 1) % 24
        self.hours_label.text = str(self.current_hours).zfill(2)

    def decrement_hours(self, instance):
        """Уменьшает часы"""
        self.current_hours = (self.current_hours - 1) % 24
        self.hours_label.text = str(self.current_hours).zfill(2)

    def increment_minutes(self, instance):
        """Увеличивает минуты"""
        self.current_minutes = (self.current_minutes + 5) % 60
        self.minutes_label.text = str(self.current_minutes).zfill(2)

    def decrement_minutes(self, instance):
        """Уменьшает минуты"""
        self.current_minutes = (self.current_minutes - 5) % 60
        self.minutes_label.text = str(self.current_minutes).zfill(2)

    def set_time(self, instance):
        """Устанавливает выбранное время"""
        try:
            from datetime import time
            selected_time = time(
                hour=self.current_hours,
                minute=self.current_minutes
            )
            self.callback(selected_time)
            self.dismiss()
        except Exception as e:
            print(f"Ошибка установки времени: {e}")


class SubjectMenuItem(OneLineListItem):
    """Кастомный элемент меню для предметов"""

    def __init__(self, subject, callback, **kwargs):
        super().__init__(**kwargs)
        self.subject = subject
        self.callback = callback

    def on_release(self):
        """Обработчик нажатия на элемент меню"""
        self.callback(self.subject)


class ScheduleScreen(Screen):
    schedule_entries = ListProperty([])
    subjects = ListProperty([])
    current_day = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view = "week"
        self.selected_day = None
        self.subjects_menu = None
        self.selected_subject = None
        self.dialog = None

    def on_pre_enter(self):
        """Загружаем данные при входе на экран"""
        self.load_subjects()
        self.load_schedule()
        self.setup_subjects_menu()
        self.update_display()

    def load_subjects(self):
        """Загружаем предметы из базы данных"""
        try:
            self.subjects = get_subjects()
            print(f"📚 Загружено предметов: {len(self.subjects)}")
        except Exception as e:
            print(f"❌ Ошибка загрузки предметов: {e}")
            self.subjects = []

    def setup_subjects_menu(self):
        """Создаем меню выбора предметов"""
        if not self.subjects:
            print("⚠️ Нет предметов для создания меню")
            return

        menu_items = []
        for subject in self.subjects:
            # Получаем информацию о преподавателе
            teacher_name = self.get_teacher_name(subject.get('teacher_id'))
            classroom = subject.get('classroom', '')

            item_text = f"{subject['name']}"
            if teacher_name or classroom:
                item_text += f" ({teacher_name}"
                if classroom:
                    item_text += f", ауд. {classroom}"
                item_text += ")"

            # Создаем кастомный элемент меню
            menu_item = {
                "viewclass": "OneLineListItem",
                "text": item_text,
                "on_release": self.create_subject_handler(subject)
            }
            menu_items.append(menu_item)

        self.subjects_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )
        print(f"✅ Меню предметов создано с {len(menu_items)} элементами")

    def create_subject_handler(self, subject):
        """Создает обработчик для выбора предмета"""

        def handler():
            self.select_subject(subject)

        return handler

    def get_teacher_name(self, teacher_id):
        """Получаем имя преподавателя по ID"""
        if not teacher_id:
            return ""
        try:
            from database import get_teacher_name
            return get_teacher_name(teacher_id)
        except:
            return ""

    def select_subject(self, subject):
        """Выбор предмета из меню"""
        print(f"🎯 Выбран предмет: {subject['name']}")
        self.selected_subject = subject
        if hasattr(self, 'subject_field'):
            teacher_name = self.get_teacher_name(subject.get('teacher_id'))
            classroom = subject.get('classroom', '')

            display_text = f"{subject['name']}"
            if teacher_name:
                display_text += f" - {teacher_name}"
            if classroom:
                display_text += f" (ауд. {classroom})"

            self.subject_field.text = display_text

        if self.subjects_menu:
            self.subjects_menu.dismiss()

    def load_schedule(self):
        """Загружаем расписание из базы"""
        try:
            self.schedule_entries = get_schedule_with_subjects()
            print(f"📅 Загружено записей расписания: {len(self.schedule_entries)}")
        except Exception as e:
            print(f"❌ Ошибка загрузки расписания: {e}")
            self.schedule_entries = []

    def switch_view(self, view_type):
        """Переключение между видом недели и дня"""
        self.current_view = view_type
        self.update_display()

    def update_display(self):
        """Обновляет отображение"""
        container = self.ids.schedule_container
        container.clear_widgets()

        # Показываем только вид недели
        self.show_week_view()

    def show_week_view(self):
        """Показывает вид недели"""
        container = self.ids.schedule_container

        # Заголовок недели
        title_label = MDLabel(
            text="Расписание на неделю",
            halign="center",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            size_hint_y=None,
            height=dp(50),
            bold=True
        )
        container.add_widget(title_label)

        # Дни недели
        days_of_week = [
            ("Понедельник", 0),
            ("Вторник", 1),
            ("Среда", 2),
            ("Четверг", 3),
            ("Пятница", 4),
            ("Суббота", 5),
            ("Воскресенье", 6)
        ]

        for day_name, day_index in days_of_week:
            day_entries = [entry for entry in self.schedule_entries
                           if entry.get('day_of_week') == day_index]

            card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(120) if day_entries else dp(100),
                padding=dp(20),
                spacing=dp(10),
                elevation=2
            )

            # Заголовок дня с кнопкой добавления
            header = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(30)
            )

            day_label = MDLabel(
                text=day_name,
                theme_text_color="Custom",
                text_color=(0.4, 0.2, 0.6, 1),
                font_style="H6",
                bold=True,
                size_hint_x=0.8
            )

            add_btn = MDIconButton(
                icon="plus",
                size_hint_x=0.2,
                theme_text_color="Custom",
                text_color=(0.5, 0.3, 0.7, 1),
                on_release=lambda x, day=day_index: self.add_schedule_entry(day)
            )

            header.add_widget(day_label)
            header.add_widget(add_btn)
            card.add_widget(header)

            if day_entries:
                for entry in day_entries:
                    start_time = entry.get('start_time', '').strftime('%H:%M') if entry.get('start_time') else ''
                    end_time = entry.get('end_time', '').strftime('%H:%M') if entry.get('end_time') else ''

                    pair_text = f"{start_time}-{end_time} - {entry.get('subject_name', 'Без названия')}"
                    if entry.get('classroom'):
                        pair_text += f" ({entry.get('classroom')})"

                    pair_layout = MDBoxLayout(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=dp(25)
                    )

                    pair_label = MDLabel(
                        text=f"• {pair_text}",
                        theme_text_color="Custom",
                        text_color=(0.3, 0.3, 0.4, 1),
                        size_hint_x=0.8
                    )

                    edit_btn = MDIconButton(
                        icon="pencil",
                        size_hint_x=0.1,
                        theme_text_color="Custom",
                        text_color=(0.5, 0.3, 0.7, 0.7),
                        on_release=lambda x, e=entry: self.edit_schedule_entry(e)
                    )

                    delete_btn = MDIconButton(
                        icon="delete",
                        size_hint_x=0.1,
                        theme_text_color="Custom",
                        text_color=(0.8, 0.2, 0.2, 0.7),
                        on_release=lambda x, e=entry: self.delete_schedule_entry(e)
                    )

                    pair_layout.add_widget(pair_label)
                    pair_layout.add_widget(edit_btn)
                    pair_layout.add_widget(delete_btn)
                    card.add_widget(pair_layout)
            else:
                empty_label = MDLabel(
                    text="Нет пар",
                    theme_text_color="Custom",
                    text_color=(0.6, 0.6, 0.7, 1),
                    halign="center",
                    size_hint_y=None,
                    height=dp(30)
                )
                card.add_widget(empty_label)

            container.add_widget(card)

    def add_schedule_entry(self, day_of_week):
        """Добавление новой пары в расписание"""
        print(f"➕ Добавление пары для дня: {day_of_week}")
        self.selected_subject = None
        self.show_schedule_dialog(day_of_week)

    def edit_schedule_entry(self, entry):
        """Редактирование существующей пары"""
        print(f"✏️ Редактирование пары: {entry.get('subject_name', '')}")
        # Находим предмет по ID
        subject_id = entry.get('subject_id')
        for subject in self.subjects:
            if subject['id'] == subject_id:
                self.selected_subject = subject
                break

        self.show_schedule_dialog(
            entry.get('day_of_week'),
            entry,
            is_edit=True
        )

    def show_schedule_dialog(self, day_of_week, entry=None, is_edit=False):
        """Показывает диалог добавления/редактирования пары"""
        print(f"🔄 Открытие диалога для дня {day_of_week}, редактирование: {is_edit}")

        # Создаем контент диалога
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15),
            size_hint_y=None,
            height=dp(350)
        )

        # Поле выбора предмета - делаем readonly и добавляем кнопку выбора
        subject_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60)
        )

        subject_layout.add_widget(MDLabel(
            text="Предмет:",
            size_hint_x=0.3,
            halign="left"
        ))

        # Поле только для отображения выбранного предмета
        self.subject_field = MDTextField(
            hint_text="Нажмите кнопку выбора",
            size_hint_x=0.5,
            readonly=True  # Только чтение - нельзя писать вручную
        )

        # Кнопка выбора предмета
        select_btn = MDRaisedButton(
            text="Выбрать",
            size_hint_x=0.2,
            md_bg_color=(0.5, 0.3, 0.7, 1),
            on_release=lambda x: self.show_subjects_menu_direct()
        )

        subject_layout.add_widget(self.subject_field)
        subject_layout.add_widget(select_btn)
        content.add_widget(subject_layout)

        # Поля времени
        time_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60)
        )

        self.start_time_field = MDTextField(
            hint_text="Время начала",
            size_hint_x=0.5,
            readonly=True
        )
        self.start_time_field.bind(focus=self.show_time_picker_start)

        self.end_time_field = MDTextField(
            hint_text="Время окончания",
            size_hint_x=0.5,
            readonly=True
        )
        self.end_time_field.bind(focus=self.show_time_picker_end)

        # Заполняем время если редактируем
        if is_edit and entry:
            if entry.get('start_time'):
                self.start_time_field.text = entry['start_time'].strftime('%H:%M')
            if entry.get('end_time'):
                self.end_time_field.text = entry['end_time'].strftime('%H:%M')

        time_layout.add_widget(self.start_time_field)
        time_layout.add_widget(self.end_time_field)
        content.add_widget(time_layout)

        # Кнопки диалога
        buttons = [
            MDFlatButton(
                text="Отмена",
                theme_text_color="Custom",
                text_color=(0.5, 0.3, 0.7, 1),
                on_release=lambda x: self.dialog.dismiss()
            ),
            MDRaisedButton(
                text="Сохранить" if is_edit else "Добавить",
                md_bg_color=(0.5, 0.3, 0.7, 1),
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                on_release=lambda x: self.save_schedule_entry(day_of_week, entry if is_edit else None)
            )
        ]

        title = "Редактировать пару" if is_edit else "Добавить пару"

        self.dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=content,
            buttons=buttons,
            size_hint=(0.8, None)
        )
        self.dialog.open()

    def show_subjects_menu_direct(self):
        """Показывает меню выбора предметов при клике на кнопку"""
        print("🎯 Открытие меню предметов")
        if self.subjects_menu:
            # Создаем временный виджет для привязки меню
            temp_widget = MDLabel()
            self.subjects_menu.caller = temp_widget
            self.subjects_menu.open()
        else:
            print("⚠️ Меню предметов не инициализировано")
            self.show_error("Сначала добавьте предметы в разделе 'Предметы'")

    def show_time_picker_start(self, instance, value):
        """Показывает выбор времени начала"""
        if value:
            print("⏰ Открытие выбора времени начала")
            time_picker = CustomTimePicker(callback=self.set_start_time)
            time_picker.open()

    def show_time_picker_end(self, instance, value):
        """Показывает выбор времени окончания"""
        if value:
            print("⏰ Открытие выбора времени окончания")
            time_picker = CustomTimePicker(callback=self.set_end_time)
            time_picker.open()

    def set_start_time(self, time_obj):
        """Устанавливает время начала"""
        self.start_time_field.text = time_obj.strftime('%H:%M')

    def set_end_time(self, time_obj):
        """Устанавливает время окончания"""
        self.end_time_field.text = time_obj.strftime('%H:%M')

    def validate_time_format(self, time_str):
        """Проверяет формат времени"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False

    def save_schedule_entry(self, day_of_week, entry=None):
        """Сохраняет пару в расписание"""
        if not self.selected_subject:
            self.show_error("Выберите предмет")
            return

        if not self.start_time_field.text or not self.end_time_field.text:
            self.show_error("Укажите время начала и окончания")
            return

        # Валидация формата времени
        if not self.validate_time_format(self.start_time_field.text):
            self.show_error("Неверный формат времени начала. Используйте ЧЧ:ММ")
            return

        if not self.validate_time_format(self.end_time_field.text):
            self.show_error("Неверный формат времени окончания. Используйте ЧЧ:ММ")
            return

        try:
            if entry:  # Редактирование
                update_schedule_entry(
                    entry_id=entry['id'],
                    subject_id=self.selected_subject['id'],
                    start_time=self.start_time_field.text,
                    end_time=self.end_time_field.text
                )
            else:  # Добавление
                add_schedule_entry(
                    subject_id=self.selected_subject['id'],
                    day_of_week=day_of_week,
                    start_time=self.start_time_field.text,
                    end_time=self.end_time_field.text
                )

            self.dialog.dismiss()
            self.load_schedule()
            self.update_display()
            self.show_success("Пара сохранена")

        except Exception as e:
            print(f"❌ Ошибка сохранения пары: {e}")
            self.show_error(f"Ошибка сохранения: {e}")

    def delete_schedule_entry(self, entry):
        """Удаляет пару из расписания"""
        self.dialog = MDDialog(
            title="Удаление пары",
            text=f"Удалить пару '{entry.get('subject_name', '')}'?",
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    theme_text_color="Custom",
                    text_color=(0.5, 0.3, 0.7, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Удалить",
                    md_bg_color=(0.8, 0.2, 0.2, 1),
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x: self.confirm_delete_schedule_entry(entry)
                )
            ]
        )
        self.dialog.open()

    def confirm_delete_schedule_entry(self, entry):
        """Подтверждает удаление пары"""
        try:
            delete_schedule_entry(entry['id'])
            self.dialog.dismiss()
            self.load_schedule()
            self.update_display()
            self.show_success("Пара удалена")

        except Exception as e:
            print(f"❌ Ошибка удаления пары: {e}")
            self.show_error(f"Ошибка удаления: {e}")

    def show_error(self, message):
        """Показывает сообщение об ошибке"""
        self.dialog = MDDialog(
            title="Ошибка",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=(0.5, 0.3, 0.7, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def show_success(self, message):
        """Показывает сообщение об успехе"""
        self.dialog = MDDialog(
            title="Успешно",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=(0.5, 0.3, 0.7, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()