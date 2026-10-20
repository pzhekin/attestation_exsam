import os
import sys
import time
from playwright.sync_api import sync_playwright
from auth_config import login

# Обеспечиваем правильный импорт локальных файлов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def generate_links_interactively():
    print("=== НАСТРОЙКА ЗАПУСКА ===")

    # 1. Запрашиваем первую букву домена
    while True:
        letter = input("Введите первую букву домена (s, d, t, f): ").strip().lower()
        if letter in ['s', 'd', 't', 'f']:
            mc_link = f"{letter}m.mm"
            break
        print("Ошибка! Допустимы только буквы s, d, t или f. Попробуйте снова.")

    # 2. Запрашиваем ID заказов
    print("\nВведите ID заказов через запятую или пробел (например: 7899558, 7932512):")
    raw_ids = input("ID заказов: ")

    # Парсим введенную строку: делим по запятым/пробелам и превращаем в числа
    raw_list = raw_ids.replace(',', ' ').split()
    order_ids = []
    for item in raw_list:
        if item.isdigit():
            order_ids.append(int(item))

    if not order_ids:
        print("Ошибка: Вы не ввели ни одного корректного ID!")
        sys.exit(1)

    # 3. Генерируем ссылки
    generated_urls = [f'https://{mc_link}/lmk/order/{i}/attestation' for i in order_ids]

    # 4. Сами перезаписываем файл links.py, чтобы сохранить историю и структуру
    with open("links.py", "w", encoding="utf-8") as f:
        f.write("# Файл сгенерирован автоматически при запуске\n")
        f.write(f"urls = {repr(generated_urls)}\n")

    print(f"\nУспешно сгенерировано ссылок: {len(generated_urls)} для домена {mc_link}!")
    print("Файл links.py обновлен.\n")

    return mc_link, generated_urls


def automate_multiple_links():
    # Запускаем интерактивный опрос перед стартом браузера
    mc_link, urls = generate_links_interactively()

    with sync_playwright() as p:
        # Запускаем браузер (headless=False, чтобы видеть процесс на экране)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Передаем страницу и вырезанный домен в функцию авторизации
        login(page, mc_link)

        # Запускаем цикл по всем сгенерированным ссылкам
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

                # Небольшая пауза между страницами
                time.sleep(1.5)

            except Exception as e:
                print(f"-> [Ошибка] Не удалось обработать ссылку {target_url}. Причина: {e}")
                continue

        print("\nВсе ссылки из списка успешно обработаны!")
        browser.close()


if __name__ == "__main__":
    automate_multiple_links()
