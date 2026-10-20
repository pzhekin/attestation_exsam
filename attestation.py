import time
from playwright.sync_api import sync_playwright
from auth_config import login
from links import urls


def automate_multiple_links():
    # Исправлено: добавляем, чтобы взять первую ссылку из списка,
    # и уже из неё вырезать 5 символов домена (с 8 по 12 символ включительно)
    mc_link = urls[0][8:13]  # Вырежет ровно 'dm.mm', 'tm.mm' и т.д.

    with sync_playwright() as p:
        # Запускаем браузер (headless=False, чтобы видеть процесс на экране)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Передаем страницу и вырезанный домен в функцию авторизации
        login(page, mc_link)

        # 2. Запускаем цикл по всем ссылкам из нашего списка
        for index, target_url in enumerate(urls, start=1):
            print(f"[{index}/{len(urls)}] Переход на страницу: {target_url}")

            try:
                page.goto(target_url)

                # Ожидаем появления кнопки #createExam на текущей странице
                page.wait_for_selector("#createExam", state="visible", timeout=15000)
                button = page.locator("#createExam")

                if button.is_disabled():
                    print(f"-> Кнопка на странице {index} уже заблокирована. Пропускаем.")
                    continue

                # Нажимаем на кнопку
                print(f"-> Клик по кнопке #createExam на странице {index}...")
                button.click()

                # Ждем, пока бэкенд обработает AJAX-запрос и разблокирует кнопку обратно
                page.wait_for_selector("#createExam:not([disabled])", timeout=20000)
                print(f"-> [Успешно] Запрос выполнен для страницы {index}!")

                # Небольшая пауза в 1-2 секунды между страницами, чтобы не перегружать сервер
                time.sleep(1.5)

            except Exception as e:
                print(f"-> [Ошибка] Не удалось обработать ссылку {target_url}. Причина: {e}")
                continue

        print("\nВсе ссылки из списка успешно обработаны!")
        browser.close()


if __name__ == "__main__":
    automate_multiple_links()
