import asyncio
import math
import time

from pyodide.ffi import JsException
from pyodide.http import pyfetch
import streamlit as st


API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


async def fetch_rates():
    """Загружает JSON через асинхронный Fetch API браузера."""

    response = await pyfetch(API_URL)
    response.raise_for_status()
    data = await response.json()

    if not isinstance(data, dict):
        raise ValueError("Ответ API должен быть объектом JSON.")
    if not isinstance(data.get("Valute"), dict) or not data["Valute"]:
        raise ValueError("В ответе нет списка валют.")
    if not isinstance(data.get("Date"), str):
        raise ValueError("В ответе нет даты курсов.")

    return data


async def get_rates():
    """Хранит успешный ответ в сессии на час, не кешируя coroutine."""

    cached = st.session_state.get("_rates_cache")
    if cached is not None and time.monotonic() - cached["loaded_at"] < 3600:
        return cached["data"]

    data = await asyncio.wait_for(fetch_rates(), timeout=20)
    st.session_state["_rates_cache"] = {
        "loaded_at": time.monotonic(),
        "data": data,
    }
    return data


def convert_to_rubles(amount, currency):
    """Пересчитывает сумму с учётом номинала валюты."""

    rate = currency["Value"] / currency["Nominal"]
    return amount * rate


async def main():
    st.set_page_config(page_title="Конвертер валют", layout="centered")
    st.title("Конвертер валют")
    st.write("Выберите валюту и узнайте стоимость суммы в рублях.")
    st.caption("Источник: [CBR-XML-Daily](https://www.cbr-xml-daily.ru/)")

    try:
        data = await get_rates()
        currencies = data["Valute"]
        date = data["Date"][:10]
    except (JsException, OSError, asyncio.TimeoutError):
        st.error("Не удалось получить курсы валют из API.")
        st.info(
            "Откройте сайт в обычном браузере, проверьте доступ к источнику "
            "и попробуйте другую сеть: Wi-Fi или мобильный интернет."
        )
        st.markdown(f"[Открыть источник курсов отдельно]({API_URL})")
        if st.button("Повторить загрузку"):
            st.rerun()
        return
    except (ValueError, KeyError, TypeError):
        st.error("Сервис вернул данные в неожиданном формате.")
        return

    if not isinstance(currencies, dict) or not currencies:
        st.error("В ответе сервиса нет списка валют.")
        return

    st.caption(f"Дата курса: {date}")
    st.caption("Справочный расчёт, не курс обмена в банке.")

    codes = sorted(currencies)
    default_index = codes.index("USD") if "USD" in codes else 0

    with st.form("converter"):
        code = st.selectbox("Валюта", codes, index=default_index)
        amount = st.number_input(
            "Сумма в выбранной валюте",
            min_value=0.0,
            value=100.0,
            step=1.0,
            format="%.2f",
        )
        submitted = st.form_submit_button("Перевести в рубли")

    if submitted:
        if not math.isfinite(amount):
            st.error("Введите конечное число.")
            return

        try:
            currency = currencies[code]
            rubles = convert_to_rubles(amount, currency)
            rate = currency["Value"] / currency["Nominal"]
            name = currency["Name"]
        except (KeyError, TypeError, ZeroDivisionError):
            st.error("Для выбранной валюты пришли неполные данные.")
            return

        st.subheader(name)
        st.metric(f"{amount:.2f} {code} в рублях", f"{rubles:.2f} RUB")
        st.caption(f"Курс за 1 {code}: {rate:.4f} RUB")


if __name__ == "__main__":
    await main()
