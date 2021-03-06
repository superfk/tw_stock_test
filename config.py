import json, datetime

def read_system_config(path='config.json'):
    with open(path, 'r', encoding= 'utf-8') as f:
        data = json.load(f)
    return data

def write_system_config(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_stocks(path='config.json'):
    config = read_system_config(path)
    stocksSelection = config['stocks']
    stocks = config[f'stocks_{stocksSelection}'].split(',')
    stocks = [x.strip() for x in stocks]
    return stocks

def get_db_folder(path='config.json'):
    config = read_system_config(path)
    db_folder = config['db_folder']
    return db_folder

def get_delay(path='config.json'):
    config = read_system_config(path)
    delay = config['delay']
    return delay

def get_dates(path='config.json'):
    config = read_system_config(path)
    date_start = config['date_start']
    if date_start == 'now':
        date_start = datetime.datetime.now().date()
    else:
        date_start = datetime.datetime.strptime(date_start, r'%Y-%m-%d').date()
    date_end = config['date_end']
    if date_end == 'now':
        date_end = datetime.datetime.now().date()
    else:
        date_end = datetime.datetime.strptime(date_end, r'%Y-%m-%d').date()
    return {'start': date_start, 'end':date_end}

def get_country(path='config.json'):
    config = read_system_config(path)
    country = config['country']
    return country

if __name__ == "__main__":
    stocks = get_stocks()
    print(stocks)