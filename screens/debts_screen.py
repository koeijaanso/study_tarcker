from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from database import get_topics, add_topic, delete_topic, update_topic, get_subjects


class DebtsScreen(Screen):
    editing_topic_id = None
    has_debts = BooleanProperty(False)
    selected_subject = StringProperty("")  # Для хранения выбранного предмета
    selected_subject_id = StringProperty("")  # Для хранения ID предмета

    def on_pre_enter(self):
        """Загрузка списка задолженностей при открытии экрана"""
        self.cancel_edit()
        self.load_topics()
        self.update_subject_button_text()

    def update_subject_button_text(self):
        """Обновляет текст кнопки выбора предмета"""
        if hasattr(self, 'ids') and 'subject_dropdown_btn' in self.ids:
            if self.selected_subject:
                self.ids.subject_dropdown_btn.text = self.selected_subject
            else:
                self.ids.subject_dropdown_btn.text = "Выберите предмет"

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

    def load_topics(self):
        """Загружает список задолженностей"""
        if hasattr(self, 'ids') and 'list_container' in self.ids:
            self.ids.list_container.clear_widgets()
            topics = get_topics()

            # Обновляем свойство has_debts
            self.has_debts = len(topics) > 0

            print(f"=== ОТЛАДКА DebtsScreen ===")
            print(f"Загружено задолженностей: {len(topics)}")
            print(f"has_debts: {self.has_debts}")

            if not topics:
                # Если задолженностей нет - показываем сообщение
                self.show_empty_message()
            else:
                # Если есть задолженности - показываем их
                for topic in topics:
                    self.add_topic_to_list(topic)

    def show_empty_message(self):
        """Показывает сообщение когда задолженностей нет"""
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
            text="Пока нет задолженностей",
            theme_text_color="Secondary",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        ))

        content.add_widget(MDLabel(
            text="Добавьте первую задолженность используя форму выше",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(25)
        ))

        empty_card.add_widget(content)
        self.ids.list_container.add_widget(empty_card)

    def add_topic_to_list(self, topic_data):
        """Добавляет одну задолженность в список с кнопками редактирования и удаления"""
        topic_id = topic_data['id']
        name = topic_data.get('name', 'Без названия')
        work_type = topic_data.get('type', 'не указан')
        subject_id = topic_data.get('subject_id')

        # Получаем название предмета
        subject_name = "не указан"
        if subject_id:
            subjects = get_subjects()
            for subject in subjects:
                if subject['id'] == subject_id:
                    subject_name = subject.get('name', 'неизвестно')
                    break

        # Определяем высоту карточки в зависимости от типа
        card_height = dp(180 if name.startswith('Просрочено:') else 160)

        # Создаем карточку задолженности
        card = MDCard(
            orientation="vertical",
            padding=dp(20),
            size_hint_y=None,
            height=card_height,
            elevation=3
        )

        # Основной контент
        content = MDBoxLayout(orientation="vertical", spacing=dp(8))

        # Название задолженности
        name_label = MDLabel(
            text=f"{name}",
            theme_text_color="Custom",
            text_color=(0.4, 0.2, 0.6, 1),
            font_style="H6",
            size_hint_y=None,
            height=dp(30),
            bold=True
        )

        # Тип работы
        type_label = MDLabel(
            text=f"Тип: {work_type}",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None,
            height=dp(25)
        )

        # Предмет
        subject_label = MDLabel(
            text=f"Предмет: {subject_name}",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None,
            height=dp(25)
        )

        content.add_widget(name_label)
        content.add_widget(type_label)
        content.add_widget(subject_label)

        # Если это автоматически созданная задолженность, добавляем пометку
        if name.startswith('Просрочено:'):
            auto_label = MDLabel(
                text="Автоматически создана из просроченной задачи",
                theme_text_color="Custom",
                text_color=(0.8, 0.4, 0.1, 1),  # Оранжевый цвет
                font_style="Caption",
                size_hint_y=None,
                height=dp(12)
            )
            content.add_widget(auto_label)

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
            on_release=lambda x, topic_id=topic_id: self.edit_topic(topic_id)
        )
        edit_btn.md_bg_color = (0.5, 0.3, 0.7, 1)  # Фиолетовый
        edit_btn.theme_text_color = "Custom"
        edit_btn.text_color = (1, 1, 1, 1)

        delete_btn = MDRaisedButton(
            text="Удалить",
            size_hint_x=0.5,
            on_release=lambda x, topic_id=topic_id: self.delete_topic_dialog(topic_id, name)
        )
        delete_btn.md_bg_color = (0.8, 0.2, 0.2, 1)  # Красный для удаления
        delete_btn.theme_text_color = "Custom"
        delete_btn.text_color = (1, 1, 1, 1)

        buttons_layout.add_widget(edit_btn)
        buttons_layout.add_widget(delete_btn)

        card.add_widget(content)
        card.add_widget(buttons_layout)
        self.ids.list_container.add_widget(card)

    def edit_topic(self, topic_id):
        """Редактирование задолженности"""
        # Находим тему в базе
        topics = get_topics()
        topic_to_edit = None

        for topic in topics:
            if topic['id'] == topic_id:
                topic_to_edit = topic
                break

        if not topic_to_edit:
            self.show_error("Задолженность не найдена")
            return

        # Заполняем поля формы данными темы
        self.ids.input_task.text = topic_to_edit.get('name', '')
        self.ids.input_type.text = topic_to_edit.get('type', '')

        # Устанавливаем предмет из базы данных
        subject_id = topic_to_edit.get('subject_id')
        if subject_id:
            subjects = get_subjects()
            for subject in subjects:
                if subject['id'] == subject_id:
                    self.selected_subject = subject.get('name', '')
                    self.selected_subject_id = str(subject['id'])
                    break
        else:
            self.selected_subject = ""
            self.selected_subject_id = ""

        self.update_subject_button_text()

        # Устанавливаем режим редактирования
        self.editing_topic_id = topic_id
        self.ids.add_button.text = "Сохранить изменения"

        self.show_success("Режим редактирования. Измените данные и нажмите 'Сохранить изменения'")

    def delete_topic_dialog(self, topic_id, topic_name):
        """Диалог подтверждения удаления"""
        self.dialog = MDDialog(
            title="Удаление задолженности",
            text=f"Вы уверены, что хотите удалить задолженность:\n\"{topic_name}\"?",
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Удалить",
                    on_release=lambda x: self.delete_topic(topic_id)
                )
            ]
        )
        # Устанавливаем цвета для кнопок диалога
        self.dialog.buttons[0].md_bg_color = (0.8, 0.7, 0.9, 1)  # Светло-фиолетовый
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (0.4, 0.2, 0.6, 1)

        self.dialog.buttons[1].md_bg_color = (0.8, 0.2, 0.2, 1)  # Красный
        self.dialog.buttons[1].theme_text_color = "Custom"
        self.dialog.buttons[1].text_color = (1, 1, 1, 1)

        self.dialog.open()

    def delete_topic(self, topic_id):
        """Удаляет задолженность"""
        try:
            delete_topic(topic_id)
            self.dialog.dismiss()
            self.load_topics()
            self.show_success("Задолженность удалена")
        except Exception as e:
            self.show_error(f"Ошибка при удалении: {e}")

    def cancel_edit(self):
        """Сбрасывает режим редактирования"""
        self.editing_topic_id = None
        self.ids.add_button.text = "Добавить задолженность"
        self.ids.input_task.text = ""
        self.ids.input_type.text = ""
        self.selected_subject = ""
        self.selected_subject_id = ""
        self.update_subject_button_text()

    def add_debt(self):
        """Добавляет или обновляет задолженность"""
        name = self.ids.input_task.text.strip()
        work_type = self.ids.input_type.text.strip()

        if not name:
            self.show_error("Введите название задолженности")
            return

        if self.editing_topic_id:
            # Режим редактирования
            try:
                update_topic(
                    topic_id=self.editing_topic_id,
                    name=name,
                    work_type=work_type if work_type else 'не указан',
                    subject_id=self.selected_subject_id if self.selected_subject_id else None
                )
                self.show_success("Задолженность обновлена")
            except Exception as e:
                self.show_error(f"Ошибка при обновлении: {e}")
        else:
            # Режим добавления
            try:
                add_topic(
                    name=name,
                    work_type=work_type if work_type else 'не указан',
                    subject_id=self.selected_subject_id if self.selected_subject_id else None
                )
                self.show_success("Задолженность добавлена")
            except Exception as e:
                self.show_error(f"Ошибка при добавлении: {e}")

        # Обновляем список и сбрасываем форму
        self.load_topics()
        self.cancel_edit()

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
        # Фиолетовая кнопка для диалога
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
        # Фиолетовая кнопка для диалога
        self.dialog.buttons[0].md_bg_color = (0.5, 0.3, 0.7, 1)
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (1, 1, 1, 1)
        self.dialog.open()