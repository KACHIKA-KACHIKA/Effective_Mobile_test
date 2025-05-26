#  Платформа для обмена вещами (бартерная система)

Монолитное веб-приложение на Django для организации обмена вещами между пользователями. 
Пользователи смогут размещать объявления о товарах для обмена, просматривать чужие объявления и отправлять предложения на обмен. 
Приложение должно предоставлять удобный веб-интерфейс и, при необходимости, REST API для работы с объявлениями и обменными предложениями.

---

## Требования

- Python 3.8+
- pip
- Виртуальное окружение (strongly recommended)

---

## Установка

```bash
git clone https://github.com/KACHIKA-KACHIKA/Effective_Mobile_test.git
cd the_barter_system
python -m venv env
source env/bin/activate      # Linux/macOS
env\Scripts\activate.bat     # Windows
pip install -r requirements.txt
python manage.py createsuperuser
python manage.py runserver
```
