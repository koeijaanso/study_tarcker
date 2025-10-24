from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager

from screens.home_screen import HomeScreen
from screens.schedule_screen import ScheduleScreen
from screens.tasks_screen import TasksScreen
from screens.debts_screen import DebtsScreen
from screens.subjects_screen import SubjectsScreen
from screens.exams_screen import ExamsScreen


class Root(BoxLayout):
    pass


class StudyTrackerApp(MDApp):
    def build(self):
        # попытка подключиться к базе данных при старте
        try:
            import database as db
            try:
                settings = db.get_settings()
                print("DB: настройки загружены:", settings)
            except Exception as e:
                print("DB: не удалось получить настройки:", e)
        except Exception as e:
            print("DB: модуль database не доступен или ошибка импорта:", e)

        # kv-шаблоны экранов
        Builder.load_file("kv/home_screen.kv")
        Builder.load_file("kv/schedule_screen.kv")
        Builder.load_file("kv/tasks_screen.kv")
        Builder.load_file("kv/debts_screen.kv")
        Builder.load_file("kv/subjects_screen.kv")
        Builder.load_file("kv/exams_screen.kv")

        # экранный менеджер
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ScheduleScreen(name="schedule"))
        sm.add_widget(TasksScreen(name="tasks"))
        sm.add_widget(DebtsScreen(name="debts"))
        sm.add_widget(SubjectsScreen(name="subjects"))
        sm.add_widget(ExamsScreen(name="exams"))

        # корневой layout
        root = BoxLayout(orientation="vertical")
        root.add_widget(sm)

        # нижняя навигация (кнопки для переключения на любую страницу)
        from kivy.uix.boxlayout import BoxLayout as _BL
        from kivy.uix.button import Button
        nav = _BL(size_hint_y=None, height="48dp")

        def make_btn(title, screen_name):
            b = Button(text=title)
            b.bind(on_release=lambda *_: setattr(sm, "current", screen_name))
            return b

        nav.add_widget(make_btn("Главная", "home"))
        nav.add_widget(make_btn("Расписание", "schedule"))
        nav.add_widget(make_btn("Задачи", "tasks"))
        nav.add_widget(make_btn("Задолженности", "debts"))
        nav.add_widget(make_btn("Предметы", "subjects"))
        nav.add_widget(make_btn("Экзамены", "exams"))

        root.add_widget(nav)
        return root


if __name__ == "__main__":
    StudyTrackerApp().run()
