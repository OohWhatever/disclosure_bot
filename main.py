import discord
import requests
import json
import asyncio
from discord import Embed

# Токен вашего бота и ID канала, куда будут отправляться сообщения
DISCORD_BOT_TOKEN = ''
DISCORD_CHANNEL_ID = 1
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

# Обработчик события готовности бота
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await check_reports()

# Функция для проверки новых отчетов
async def check_reports():
    file_path = 'current_report_id.txt'
    report_disclose_id = read_current_id(file_path)

    while True:
        response = get_report_data(report_disclose_id)
        if response.status_code == 200:
            data = response.json()
            if 'name' in data:

                # Создаем embed-сообщение
                embed = Embed(title=f"Найден новый отчет! ID: {report_disclose_id}",
                              description=f"**Заголовок**: {data['name']}\n**Ссылка**: https://bugbounty.standoff365.com/disclosed-reports/{report_disclose_id}",
                              color=0x00ff00)
                embed.add_field(name="Критичность", value=data['severity'])
                embed.add_field(name="Статус", value=data['status'])
                embed.add_field(name="Сумма", value=f"{data['amount']} {data['currency']}")
                embed.add_field(name="Автор", value=data['author']['username'])

                # Отправляем embed в указанный канал
                channel = client.get_channel(DISCORD_CHANNEL_ID)
                await channel.send(embed=embed)

                # Увеличиваем ID на единицу и записываем в файл
                report_disclose_id += 1
                write_current_id(file_path, report_disclose_id)
            else:
                print(f"Неожиданный формат ответа для ID {report_disclose_id}")
        elif response.status_code == 404:
            print(f"Report ID {report_disclose_id} не найден. Проверяем снова через 30 секунд.")
        else:
            print(f"Ошибка при запросе ID {report_disclose_id}: {response.status_code}")

        # Ожидание 30 секунд перед следующим запросом
        await asyncio.sleep(30)

# Запуск бота
client.run(DISCORD_BOT_TOKEN)
