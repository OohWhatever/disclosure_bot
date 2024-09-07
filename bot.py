import discord
import requests
import json
import asyncio
from discord import Embed

# Токен вашего бота и ID каналов
DISCORD_BOT_TOKEN = ''
DISCORD_CHANNEL_ID = 1280593565571092552  # ID канала для отчетов
DISCORD_STATUS_CHANNEL_ID = 1282081789367554260  # ID канала для состояния
DISCL_URL = 'https://bugbounty.standoff365.com/disclosed-reports/'

# Функция для получения данных из API
def get_report_data(report_disclose_id):
    url = f"https://api.standoff365.com/api/bug-bounty/ui/report-disclose/{report_disclose_id}"
    response = requests.get(url)
    return response

# Функция для чтения текущего report_disclose_id из файла
def read_current_id(file_path):
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 1  # Если файл не найден, начинаем с 1
    except ValueError:
        return 1  # Если в файле невалидные данные, начинаем с 1

# Функция для записи текущего report_disclose_id в файл
def write_current_id(file_path, report_disclose_id):
    with open(file_path, 'w') as file:
        file.write(str(report_disclose_id))

# Инициализация клиента Discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Переменная для хранения сообщения о состоянии
status_message = None

# Обработчик события готовности бота
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await check_reports()

# Функция для отправки или обновления сообщения о состоянии
async def update_status_embed(report_disclose_id, status_message_text):
    global status_message
    status_channel = client.get_channel(DISCORD_STATUS_CHANNEL_ID)

    if status_channel:
        # Создаем embed для состояния
        embed = Embed(title="Статус проверки отчетов",
                      description=f"Проверка отчета с ID {report_disclose_id}",
                      color=0x3498db,
                      timestamp=datetime.now()  # Добавляем отметку времени
        embed.add_field(name="Текущее состояние", value=status_message_text, inline=False)
        embed.set_footer(text="Статус обновляется каждые 30 секунд")

        # Если сообщение еще не создано, создаем новое embed-сообщение
        if status_message is None:
            status_message = await status_channel.send(embed=embed)
        else:
            # Если сообщение уже создано, редактируем его
            await status_message.edit(embed=embed)
    else:
        print("Не удалось найти канал для статусов.")

# Функция для проверки новых отчетов
async def check_reports():
    file_path = 'current_report_id.txt'
    report_disclose_id = read_current_id(file_path)

    while True:
        response = get_report_data(report_disclose_id)
        if response.status_code == 200:
            data = response.json()
            if 'name' in data:
                # Создаем embed-сообщение для отчета
                embed = Embed(title=f"Найден новый отчет! ID: {report_disclose_id}",
                              description=f"**Заголовок**: {data['name']}\n**Ссылка**: https://bugbounty.standoff365.com/disclosed-reports/{report_disclose_id}",
                              color=0x00ff00,
                              timestamp=datetime.utcnow())  # Добавляем отметку времени
                embed.add_field(name="Критичность", value=data['severity'])
                embed.add_field(name="Статус", value=data['status'])
                embed.add_field(name="Сумма", value=f"{data['amount']} {data['currency']}")
                embed.add_field(name="Автор", value=data['author']['username'])

                # Отправляем embed в указанный канал
                report_channel = client.get_channel(DISCORD_CHANNEL_ID)
                if report_channel:
                    await report_channel.send(embed=embed)

                # Обновляем embed-сообщение о состоянии
                await update_status_embed(report_disclose_id, "Найден новый отчет и отправлен в канал.")

                # Увеличиваем ID на единицу и записываем в файл
                report_disclose_id += 1
                write_current_id(file_path, report_disclose_id)
            else:
                await update_status_embed(report_disclose_id, "Неожиданный формат ответа.")
                print(f"Неожиданный формат ответа для ID {report_disclose_id}")
        elif response.status_code == 404:
            await update_status_embed(report_disclose_id, "Отчет не найден.")
            print(f"Report ID {report_disclose_id} не найден. Проверяем снова через 30 секунд.")
        else:
            await update_status_embed(report_disclose_id, f"Ошибка {response.status_code}.")
            print(f"Ошибка при запросе ID {report_disclose_id}: {response.status_code}")

        # Ожидание 30 секунд перед следующим запросом
        await asyncio.sleep(30)

# Запуск бота
client.run(DISCORD_BOT_TOKEN)
