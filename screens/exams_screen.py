from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from database import add_exam, get_exams_only, delete_task, update_task


class ExamsScreen(Screen):
    editing_exam_id = None
    has_exams = BooleanProperty(False)  # Добавляем свойство

    def on_pre_enter(self):
        """Загрузка списка экзаменов при открытии экрана"""
        self.cancel_edit()
        self.load_exams()

    def load_exams(self):
        """Загружает список экзаменов"""
        self.ids.list_container.clear_widgets()
        exams = get_exams_only()

        # Обновляем свойство has_exams
        self.has_exams = len(exams) > 0

        print(f"=== ОТЛАДКА ExamsScreen ===")
        print(f"Загружено экзаменов: {len(exams)}")
        print(f"has_exams: {self.has_exams}")

        if not exams:
            # Если экзаменов нет - показываем сообщение
            self.show_empty_message()
        else:
            # Если есть экзамены - показываем их
            for exam in exams:
                self.add_exam_to_list(exam)

    def show_empty_message(self):
        """Показывает сообщение когда экзаменов нет"""
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
            text="Пока нет экзаменов",
            theme_text_color="Secondary",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        ))

        content.add_widget(MDLabel(
            text="Добавьте первый экзамен используя форму выше",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(25)
        ))

        empty_card.add_widget(content)
        self.ids.list_container.add_widget(empty_card)

    def add_exam_to_list(self, exam_data):
        """Добавляет один экзамен в список с кнопками редактирования и удаления"""
        exam_id = exam_data['id']
        title = exam_data.get('title', 'Без названия')
        due_date = exam_data.get('due_date')
        description = exam_data.get('description', '')

        if due_date:
            if isinstance(due_date, str):
                date_str = due_date
            else:
                date_str = due_date.strftime("%d.%m.%Y %H:%M")
        else:
            date_str = "Дата не указана"

        # Создаем карточку экзамена
        card = MDCard(
            orientation="vertical",
            padding=dp(20),
            size_hint_y=None,
            height=dp(165),
            elevation=3
        )

        # Основной контент
        content = MDBoxLayout(orientation="vertical", spacing=dp(8))

        # Заголовок
        title_label = MDLabel(
            text=f"{title}",
            theme_text_color="Custom",
            text_color=(0.8, 0.2, 0.2, 1),  # Красный для экзаменов
            font_style="H6",
            size_hint_y=None,
            height=dp(30),
            bold=True
        )

        # Дата
        date_label = MDLabel(
            text=f"{date_str}",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None,
            height=dp(25)
        )

        content.add_widget(title_label)
        content.add_widget(date_label)

        # Заметки (если есть)
        if description:
            note_label = MDLabel(
                text=f"{description}",
                theme_text_color="Custom",
                text_color=(0.3, 0.3, 0.4, 1),
                size_hint_y=None,
                height=dp(25)
            )
            content.add_widget(note_label)

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
            on_release=lambda x, exam_id=exam_id: self.edit_exam(exam_id)
        )
        edit_btn.md_bg_color = (0.5, 0.3, 0.7, 1)
        edit_btn.theme_text_color = "Custom"
        edit_btn.text_color = (1, 1, 1, 1)

        delete_btn = MDRaisedButton(
            text="Удалить",
            size_hint_x=0.5,
            on_release=lambda x, exam_id=exam_id: self.delete_exam_dialog(exam_id, title)
        )
        delete_btn.md_bg_color = (0.8, 0.2, 0.2, 1)
        delete_btn.theme_text_color = "Custom"
        delete_btn.text_color = (1, 1, 1, 1)

        buttons_layout.add_widget(edit_btn)
        buttons_layout.add_widget(delete_btn)

        card.add_widget(content)
        card.add_widget(buttons_layout)
        self.ids.list_container.add_widget(card)

    def edit_exam(self, exam_id):
        """Редактирование экзамена"""
        # Находим экзамен в базе
        exams = get_exams_only()
        exam_to_edit = None

        for exam in exams:
            if exam['id'] == exam_id:
                exam_to_edit = exam
                break

        if not exam_to_edit:
            self.show_error("Экзамен не найден")
            return

        # Заполняем поля формы данными экзамена
        self.ids.input_exam.text = exam_to_edit.get('title', '')
        self.ids.input_note.text = exam_to_edit.get('description', '')

        # Устанавливаем дату и время
        due_date = exam_to_edit.get('due_date')
        if due_date:
            if isinstance(due_date, str):
                date_str = due_date
            else:
                date_str = due_date.strftime("%d.%m.%Y %H:%M")
            self.ids.input_dt.text = date_str

        # Устанавливаем режим редактирования
        self.editing_exam_id = exam_id
        self.ids.add_button.text = "Сохранить изменения"

        self.show_success("Режим редактирования. Измените данные и нажмите 'Сохранить изменения'")

    def delete_exam_dialog(self, exam_id, exam_title):
        """Диалог подтверждения удаления"""
        self.dialog = MDDialog(
            title="Удаление экзамена",
            text=f"Вы уверены, что хотите удалить экзамен:\n\"{exam_title}\"?",
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Удалить",
                    on_release=lambda x: self.delete_exam(exam_id)
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

    def delete_exam(self, exam_id):
        """Удаляет экзамен"""
        try:
            delete_task(exam_id)
            self.dialog.dismiss()
            self.load_exams()
            self.show_success("Экзамен удален")
        except Exception as e:
            self.show_error(f"Ошибка при удалении: {e}")

    def cancel_edit(self):
        """Сбрасывает режим редактирования"""
        self.editing_exam_id = None
        self.ids.add_button.text = "Добавить экзамен"
        self.ids.input_exam.text = ""
        self.ids.input_dt.text = ""
        self.ids.input_note.text = ""

    def add_exam(self):
        """Добавляет или обновляет экзамен"""
        title = self.ids.input_exam.text.strip()
        dt = self.ids.input_dt.text.strip()
        note = self.ids.input_note.text.strip()

        if not title or not dt:
            self.show_error("Заполните название и дату экзамена")
            return

        if self.editing_exam_id:
            # Режим редактирования
            try:
                update_task(
                    task_id=self.editing_exam_id,
                    title=title,
                    description=note,
                    due_date=dt
                )
                self.show_success("Экзамен обновлен")
            except Exception as e:
                self.show_error(f"Ошибка при обновлении: {e}")
        else:
            # Режим добавления
            add_exam(title, note, None, None, dt)
            self.show_success("Экзамен добавлен")

        # Обновляем список и сбрасываем форму
        self.load_exams()
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