import json

def read_system_config(path='config.json'):
    with open(path, 'r', encoding= 'utf-8') as f:
        data = json.load(f)
    return data

def write_system_config(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_stocks(path='config.json'):
    config = read_system_config(path)
    stocks = config['stocks'].split(',')
    stocks = [int(x.strip()) for x in stocks]
    return stocks

def get_db_folder(path='config.json'):
    config = read_system_config(path)
    db_folder = config['db_folder']
    return db_folder

def get_delay(path='config.json'):
    config = read_system_config(path)
    delay = config['delay']
    return delay

if __name__ == "__main__":
    config = read_system_config()
    print(config)
    stocks = config['stocks'].split(',')
    stocks = [int(x.strip()) for x in stocks]
    print(stocks)