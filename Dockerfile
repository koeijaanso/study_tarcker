FROM kivy/buildozer:latest

# Исправляем проблему с --user в virtualenv
RUN sed -i 's/--user //g' /home/user/.venv/lib/python3.*/site-packages/buildozer/targets/android.py

WORKDIR /app
