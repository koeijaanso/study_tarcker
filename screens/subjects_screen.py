from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from database import get_subjects, add_subject, get_teachers, delete_subject, update_subject, get_subject_by_id


class SubjectItem(MDBoxLayout):
    pass


class SubjectsScreen(Screen):
    has_subjects = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.editing_subject_id = None
        self.dialog = None

    def on_pre_enter(self):
        """Загрузка списка предметов при открытии экрана"""
        self.cancel_edit()
        self.load_subjects()

    def load_subjects(self):
        """Загружает список предметов"""
        print("Загрузка предметов...")
        try:
            self.ids.list_container.clear_widgets()
            subjects = get_subjects()
            print(f"Получено предметов: {len(subjects)}")

            # Обновляем свойство has_subjects
            self.has_subjects = len(subjects) > 0

            if not subjects:
                # Если предметов нет - показываем сообщение
                self.show_empty_message()
            else:
                # Если есть предметы - показываем их
                for sub in subjects:
                    self.add_subject_to_list(sub)

        except Exception as e:
            print(f"Ошибка при загрузке предметов: {e}")
            self.show_error(f"Ошибка загрузки: {e}")

    def show_empty_message(self):
        """Показывает сообщение когда предметов нет"""
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
            text="Пока нет предметов",
            theme_text_color="Secondary",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        ))

        content.add_widget(MDLabel(
            text="Добавьте первый предмет используя форму выше",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(25)
        ))

        empty_card.add_widget(content)
        self.ids.list_container.add_widget(empty_card)

    def add_subject_to_list(self, subject_data):
        """Добавляет один предмет в список с кнопками редактирования и удаления"""
        try:
            subject_id = subject_data['id']
            name = subject_data.get('name', 'Без названия')
            classroom = subject_data.get('classroom', '')

            # Получаем имя преподавателя
            teacher_name = ""
            if subject_data.get("teacher_id"):
                teacher_name = self.get_teacher_name(subject_data["teacher_id"])

            # Создаем карточку предмета
            card = MDCard(
                orientation="vertical",
                padding=dp(20),
                size_hint_y=None,
                height=dp(140),
                elevation=3
            )

            # Основной контент
            content = MDBoxLayout(orientation="horizontal", spacing=dp(15))

            # Текстовая информация
            text_layout = MDBoxLayout(orientation="vertical", spacing=dp(8))

            # Название предмета
            name_label = MDLabel(
                text=f"{name}",
                theme_text_color="Custom",
                text_color=(0.4, 0.2, 0.6, 1),
                font_style="H6",
                size_hint_y=None,
                height=dp(30),
                bold=True
            )

            # Дополнительная информация
            info_text = ""
            if teacher_name:
                info_text += f"{teacher_name}"
            if classroom:
                if teacher_name:
                    info_text += " • "
                info_text += f"Ауд. {classroom}"

            info_label = MDLabel(
                text=info_text if info_text else "Нет дополнительной информации",
                theme_text_color="Custom",
                text_color=(0.3, 0.3, 0.4, 1),
                size_hint_y=None,
                height=dp(25)
            )

            text_layout.add_widget(name_label)
            text_layout.add_widget(info_label)

            content.add_widget(text_layout)

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
                on_release=lambda x, sid=subject_id: self.edit_subject(sid)
            )
            edit_btn.md_bg_color = (0.5, 0.3, 0.7, 1)  # Фиолетовый
            edit_btn.theme_text_color = "Custom"
            edit_btn.text_color = (1, 1, 1, 1)

            delete_btn = MDRaisedButton(
                text="Удалить",
                size_hint_x=0.5,
                on_release=lambda x, sid=subject_id: self.delete_subject_dialog(sid, name)
            )
            delete_btn.md_bg_color = (0.8, 0.2, 0.2, 1)  # Красный для удаления
            delete_btn.theme_text_color = "Custom"
            delete_btn.text_color = (1, 1, 1, 1)

            buttons_layout.add_widget(edit_btn)
            buttons_layout.add_widget(delete_btn)

            card.add_widget(content)
            card.add_widget(buttons_layout)
            self.ids.list_container.add_widget(card)

        except Exception as e:
            print(f"Ошибка при добавлении предмета в список: {e}")

    def edit_subject(self, subject_id):
        """Редактирование предмета"""
        print(f"Редактирование предмета ID: {subject_id}")
        try:
            # Находим предмет в базе
            subject_to_edit = get_subject_by_id(subject_id)

            if not subject_to_edit:
                self.show_error("Предмет не найден")
                return

            # Заполняем поля формы данными предмета
            self.ids.input_subject.text = subject_to_edit.get('name', '')

            # Заполняем преподавателя
            teacher_name = ""
            if subject_to_edit.get("teacher_id"):
                teacher_name = self.get_teacher_name(subject_to_edit["teacher_id"])
            self.ids.input_teacher.text = teacher_name

            self.ids.input_room.text = subject_to_edit.get('classroom', '')

            # Устанавливаем режим редактирования
            self.editing_subject_id = subject_id
            self.ids.add_button.text = "Сохранить изменения"

            self.show_success("Режим редактирования. Измените данные и нажмите 'Сохранить изменения'")

        except Exception as e:
            print(f"Ошибка при редактировании: {e}")
            self.show_error(f"Ошибка редактирования: {e}")

    def delete_subject_dialog(self, subject_id, subject_name):
        """Диалог подтверждения удаления"""
        self.dialog = MDDialog(
            title="Удаление предмета",
            text=f"Вы уверены, что хотите удалить предмет:\n\"{subject_name}\"?",
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Удалить",
                    on_release=lambda x, sid=subject_id: self.delete_subject(sid)
                )
            ]
        )
        # Устанавливаем цвета для кнопок диалога
        self.dialog.buttons[0].theme_text_color = "Custom"
        self.dialog.buttons[0].text_color = (0.5, 0.3, 0.7, 1)

        self.dialog.buttons[1].md_bg_color = (0.8, 0.2, 0.2, 1)  # Красный
        self.dialog.buttons[1].theme_text_color = "Custom"
        self.dialog.buttons[1].text_color = (1, 1, 1, 1)

        self.dialog.open()

    def delete_subject(self, subject_id):
        """Удаляет предмет"""
        print(f"Удаление предмета ID: {subject_id}")
        try:
            delete_subject(subject_id)
            if self.dialog:
                self.dialog.dismiss()
            self.load_subjects()
            self.show_success("Предмет удален")
        except Exception as e:
            print(f"Ошибка при удалении: {e}")
            self.show_error(f"Ошибка при удалении: {e}")

    def cancel_edit(self):
        """Сбрасывает режим редактирования"""
        self.editing_subject_id = None
        self.ids.add_button.text = "Добавить предмет"
        self.ids.input_subject.text = ""
        self.ids.input_teacher.text = ""
        self.ids.input_room.text = ""

    def add_subject(self):
        """Добавляет или обновляет предмет"""
        name = self.ids.input_subject.text.strip()
        teacher_name = self.ids.input_teacher.text.strip()
        classroom = self.ids.input_room.text.strip()

        if not name:
            self.show_error("Введите название предмета")
            return

        try:
            if self.editing_subject_id:
                # Режим редактирования
                print(f"Обновление предмета ID: {self.editing_subject_id}")
                update_subject(
                    subject_id=self.editing_subject_id,
                    name=name,
                    teacher_id=None,
                    classroom=classroom if classroom else None,
                    color="0.5,0.3,0.7,1"  # Фиолетовый по умолчанию
                )
                self.show_success("Предмет обновлен")
            else:
                # Режим добавления
                print("Добавление нового предмета")
                add_subject(
                    name=name,
                    teacher_id=None,
                    classroom=classroom if classroom else None,
                    color="0.5,0.3,0.7,1"  # Фиолетовый по умолчанию
                )
                self.show_success("Предмет добавлен")

            # Обновляем список и сбрасываем форму
            self.load_subjects()
            self.cancel_edit()

        except Exception as e:
            print(f"Ошибка при сохранении предмета: {e}")
            self.show_error(f"Ошибка сохранения: {e}")

    def get_teacher_name(self, teacher_id):
        """Получает имя преподавателя по ID"""
        try:
            teachers = get_teachers()
            for teacher in teachers:
                if teacher['id'] == teacher_id:
                    return teacher['full_name']
        except Exception as e:
            print(f"Ошибка при получении имени преподавателя: {e}")
        return ""

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