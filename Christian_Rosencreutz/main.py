import random
import time
from memory_profiler import memory_usage


# Генерація випадкового повідомлення
def generate_random_message(length):
    return ''.join(random.choice(['0', '1']) for _ in range(length))


# 1. Простий послідовний алгоритм CRC-16-T10-DIF
def crc16_t10_dif(message):
    poly = 0x8BB7  # Поліном для CRC-16-T10-DIF
    crc = 0xFFFF  # Початкове значення CRC (усі біти встановлені у 1)

    # Доповнення повідомлення 16 нульовими бітами
    message += '0' * 16

    # Обробка кожного біту вхідного повідомлення
    for bit in message:
        # Зсунути регістр вліво та додати черговий біт повідомлення
        crc ^= (int(bit) << 15)

        # Перевіряємо старший біт та виконуємо XOR з поліномом при потребі
        if crc & 0x8000:  # Якщо старший біт встановлений в 1
            crc = (crc << 1) ^ poly  # Виконуємо XOR з поліномом
        else:
            crc <<= 1  # Виконуємо простий зсув без XOR

        # Залишаємо тільки 16 біт
        crc &= 0xFFFF

    return crc


# 2. Табличний алгоритм CRC-16-T10-DIF
# Функція створює таблицю для пришвидшення обчислення CRC
def create_crc16_table(poly):
    table = []  # Створюємо пустий список для зберігання значень CRC для кожного байта
    for i in range(256):  # Для всіх можливих значень байтів (0-255)
        crc = i << 8  # Зсуваємо байт вліво на 8 біт, щоб розмістити його в старших бітах регістру
        for _ in range(8):  # Виконуємо 8 циклів для обробки кожного біта байта
            if crc & 0x8000:  # Якщо старший біт встановлений (дорівнює 1)
                crc = (crc << 1) ^ poly  # Виконуємо XOR з поліномом
            else:
                crc <<= 1  # Виконуємо простий зсув вліво без XOR
        table.append(crc & 0xFFFF)  # Зберігаємо тільки молодші 16 біт значення у таблицю
    return table  # Повертаємо заповнену таблицю


# Табличне обчислення CRC з використанням попередньо згенерованої таблиці
def crc16_table(message, table):
    crc = 0xFFFF  # Початкове значення CRC (усі біти встановлені у 1)

    # Обробка кожного байта повідомлення
    for byte in bytearray(message.encode('utf-8')):  # Перетворюємо повідомлення у масив байтів
        # Визначаємо індекс для таблиці:
        # Старший байт регістру XOR з поточним байтом повідомлення
        index = (crc >> 8) ^ byte
        # Знаходимо значення з таблиці за індексом та об'єднуємо його з регістром
        crc = ((crc << 8) ^ table[index]) & 0xFFFF  # Залишаємо лише 16 біт результату

    return crc  # Повертаємо обчислене значення CRC


# Функція для інверсії бітів у числі
def reverse_bits(value, bit_size=16):
    result = 0
    for _ in range(bit_size):
        result = (result << 1) | (value & 1)  # Додаємо найменший біт до результату
        value >>= 1  # Зсуваємо вхідне значення вправо, щоб отримати наступний біт
    return result  # Повертаємо значення з інвертованим порядком бітів


# 3. Дзеркальний послідовний алгоритм CRC-16-T10-DIF
def crc16_t10_dif_mirror(message):
    poly = 0x8BB7  # Поліном для CRC-16-T10-DIF
    crc = 0xFFFF  # Початкове значення CRC (усі біти встановлені у 1)

    # Інверсія всіх бітів у кожному символі повідомлення для роботи з дзеркальним порядком
    message_reversed = ''.join(format(reverse_bits(int(b), 1), 'b') for b in message)

    # Обробка кожного біту інвертованого повідомлення
    for bit in message_reversed:
        # Зсунути регістр вправо та додати черговий біт повідомлення
        crc ^= (reverse_bits(int(bit), 1) << 15)  # Додаємо інвертований біт до старшого біта регістру

        # Виконуємо 8 ітерацій зсуву вправо та перевірки старшого біта
        for _ in range(8):
            if crc & 0x0001:  # Якщо молодший біт встановлений (дорівнює 1)
                crc = (crc >> 1) ^ poly  # Виконуємо XOR з поліномом
            else:
                crc >>= 1  # Простий зсув вправо без XOR

        crc &= 0xFFFF  # Обрізаємо результат до 16 бітів

    # Інвертуємо результат перед поверненням для коректного відображення
    return reverse_bits(crc)


# 4. Дзеркальний табличний алгоритм CRC-16-T10-DIF
# Функція для обчислення CRC з використанням таблиці та дзеркальної обробки байтів
def crc16_table_mirror(message, table):
    crc = 0xFFFF  # Початкове значення CRC (усі біти встановлені у 1)

    # Обробка кожного байта повідомлення у дзеркальному порядку
    for byte in bytearray(message.encode('utf-8')):  # Перетворюємо повідомлення у масив байтів
        # Інвертуємо порядок бітів у поточному байті
        byte_reversed = reverse_bits(byte, 8)

        # Виконуємо обчислення CRC:
        # Зсуваємо CRC на 8 біт вліво та виконуємо XOR з таблицею за індексом
        # Індекс обчислюється як старший байт CRC XOR з інвертованим байтом повідомлення
        index = (crc >> 8) ^ byte_reversed
        crc = ((crc << 8) ^ table[index]) & 0xFFFF  # Обрізаємо результат до 16 біт

    # Інвертуємо порядок бітів у кінцевому значенні CRC перед поверненням
    return reverse_bits(crc)


# Функція для проведення кількох раундів тестування
def run_tests(message, rounds):
    poly = 0x8BB7
    table = create_crc16_table(poly)

    # Ініціалізація змінних для підрахунку середніх значень
    total_simple_time = 0
    total_table_time = 0
    total_mirror_time = 0
    total_mirror_table_time = 0

    total_mem_simple = 0
    total_mem_table = 0
    total_mem_mirror = 0
    total_mem_mirror_table = 0

    for i in range(rounds):
        print(f"Раунд {i + 1} з {rounds}")

        # Простий послідовний алгоритм
        start_time = time.time()
        mem_usage_simple = memory_usage((crc16_t10_dif, (message,)))
        crc_simple = crc16_t10_dif(message)
        simple_time = time.time() - start_time
        total_simple_time += simple_time
        total_mem_simple += max(mem_usage_simple)
        # print(f"Простий послідовний: CRC = {crc_simple:04X}, Час: {simple_time:.6f} сек, Пам'ять: {max(mem_usage_simple)} MiB")

        # Табличний алгоритм
        start_time = time.time()
        mem_usage_table = memory_usage((crc16_table, (message, table)))
        crc_table = crc16_table(message, table)
        table_time = time.time() - start_time
        total_table_time += table_time
        total_mem_table += max(mem_usage_table)
        # print(f"Табличний: CRC = {crc_table:04X}, Час: {table_time:.6f} сек, Пам'ять: {max(mem_usage_table)} MiB")

        # Дзеркальний послідовний алгоритм
        start_time = time.time()
        mem_usage_mirror = memory_usage((crc16_t10_dif_mirror, (message,)))
        crc_mirror = crc16_t10_dif_mirror(message)
        mirror_time = time.time() - start_time
        total_mirror_time += mirror_time
        total_mem_mirror += max(mem_usage_mirror)
        # print(f"Дзеркальний послідовний: CRC = {crc_mirror:04X}, Час: {mirror_time:.6f} сек, Пам'ять: {max(mem_usage_mirror)} MiB")

        # Дзеркальний табличний алгоритм
        start_time = time.time()
        mem_usage_mirror_table = memory_usage((crc16_table_mirror, (message, table)))
        crc_mirror_table = crc16_table_mirror(message, table)
        mirror_table_time = time.time() - start_time
        total_mirror_table_time += mirror_table_time
        total_mem_mirror_table += max(mem_usage_mirror_table)
        # print(f"Дзеркальний табличний: CRC = {crc_mirror_table:04X}, Час: {mirror_table_time:.6f} сек, Пам'ять: {max(mem_usage_mirror_table)} MiB")

        # print("-" * 50)

    # Підрахунок середніх значень
    avg_simple_time = total_simple_time / rounds
    avg_table_time = total_table_time / rounds
    avg_mirror_time = total_mirror_time / rounds
    avg_mirror_table_time = total_mirror_table_time / rounds

    avg_mem_simple = total_mem_simple / rounds
    avg_mem_table = total_mem_table / rounds
    avg_mem_mirror = total_mem_mirror / rounds
    avg_mem_mirror_table = total_mem_mirror_table / rounds

    print("\nСередні результати після кількох раундів тестування:")
    print(f"Простий послідовний: Середній час: {avg_simple_time:.6f} сек, Середня пам'ять: {avg_mem_simple} MiB")
    print(f"Табличний: Середній час: {avg_table_time:.6f} сек, Середня пам'ять: {avg_mem_table} MiB")
    print(f"Дзеркальний послідовний: Середній час: {avg_mirror_time:.6f} сек, Середня пам'ять: {avg_mem_mirror} MiB")
    print(f"Дзеркальний табличний: Середній час: {avg_mirror_table_time:.6f} сек, Середня пам'ять: {avg_mem_mirror_table} MiB")


# Основна програма
if __name__ == "__main__":
    rounds = 50  # Кількість раундів тестування
    message = generate_random_message(1000)  # Генерація випадкового повідомлення
    print(f"Згенероване повідомлення: {message[:50]}... (довжина: {len(message)})")

    # Запуск тестування
    run_tests(message, rounds)
