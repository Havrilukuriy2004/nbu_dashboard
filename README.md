# NBU Open Data Dashboard

Автоматичний дашборд для відкритих даних НБУ з базовою аналітикою.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Після запуску відкрийте браузер за адресою, яку підкаже Streamlit (зазвичай `http://localhost:8501`).

## Набори даних

Доступні категорії:
- макро індикатори
- фінансові ринки
- банки
- міжнародні фінанси
- ринки капіталу

У бічному меню можна додати власний JSON-ендпоінт НБУ.
