import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify, redirect, url_for, render_template
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на случайный секретный ключ

# Google Sheets and Google Drive API credentials
SCOPE = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'creds.json'
SPREADSHEET_ID = '1gzx4s13NrB71ifEukz2_fwgmiwI2TOARgifeKVpdSXE'
RESULTS_SHEET_NAME = 'Результаты'  # Имя листа для результатов
PARTICIPANTS_SHEET_NAME = 'Участники'  # Имя листа для участников
IP_SHEET_NAME = 'IP-просмотр'  # Имя листа для IP-адресов
IP_vote_SHEET_NAME = 'IP-голосующих'  # Имя листа для IP-адресов

# Authorization
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
gc = gspread.authorize(credentials)

# Open Google Sheet and get data from cells
participants_worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(PARTICIPANTS_SHEET_NAME)
results_worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(RESULTS_SHEET_NAME)
ip_worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(IP_SHEET_NAME)
ip_vote_worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(IP_vote_SHEET_NAME)

# Функция записи голоса
def recordVote(participant, ip_address):

    ip_vote_data = ip_vote_worksheet.get_all_values()
    for row_index, row in enumerate(ip_vote_data[1:]):  # Проходим по строкам, начиная со второй (первая - заголовок)
        if row[0] == ip_address:  # Проверяем IP в столбце
            ip_vote_worksheet.append_row([ip_address])
            return redirect(url_for('double_vote'))  # Перенаправляем на дублирование

    count = 0        
    # Если IP не найден, добавляем его и записываем голос
    ip_vote_worksheet.append_row([ip_address])
    votes_data = results_worksheet.get_all_values()
    for row_index, row in enumerate(votes_data[1:]):  # Проходим по строкам, начиная со второй (первая - заголовок)
        if row[0] == participant:
            votes = int(row[1]) + 1
            results_worksheet.update_cell(row_index + 2, 2, votes)  # Обновляем значение в ячейке
            count = 1

    if count == 0:
        # Если участника нет в таблице, добавляем его
        results_worksheet.append_row([participant, 1])

    ip_data = ip_worksheet.get_all_values()
    for row_index, row in enumerate(ip_data[1:]):  # Проходим по строкам, начиная со второй (первая - заголовок)
        if row[0] == ip_address :  # Проверяем IP в столбце D
            return redirect(url_for('get_results'))  # Перенаправляем на результаты
            
    return redirect(url_for('thank_you'))  # Перенаправляем на "Спасибо.."
            


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip_address = request.remote_addr
    if request.method == 'POST':
        participant = request.form.get('participant')
        print(f"Participant: {participant}, IP: {ip_address}")
        return recordVote(participant, ip_address)  # Вызываем функцию записи голоса

    # Получаем данные участников из листа "Участники"
    data = participants_worksheet.col_values(1)[1:]  # Берем значения из столбца A, начиная со второй строки
    return render_template('voting.html', participants=data)

# Определение маршрута '/vote'
@app.route('/vote', methods=['POST'])
def vote():
    participant = request.form.get('participant')
    ip_address = request.remote_addr
    print(f"Participant: {participant}, IP: {ip_address}")
    return recordVote(participant, ip_address)


@app.route('/results')
def get_results():
    results = results_worksheet.get_all_values()
    formatted_results = []
    for row in results[1:]:
        formatted_results.append({'name': row[0], 'votes': int(row[1])})
    return render_template('results.html', results=formatted_results)  # Возвращаем HTML-шаблон

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/double_vote')
def double_vote():
    return render_template('double_vote.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)