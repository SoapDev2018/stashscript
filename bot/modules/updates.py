from bot.helpers import db_ops
from bot import updater
from telegram.ext.callbackcontext import CallbackContext
import requests
import subprocess
import shlex


def update_prices(_: CallbackContext) -> None:
    print('Updating prices now...')
    inr_price_request = requests.get(
        'https://api.exchangerate.host/latest?base=USD')
    if inr_price_request.status_code != 200:
        print('Failed to fetch data from exchangerate.host, will retry later')
    else:
        inr_price_json = inr_price_request.json()
        if inr_price_json['success'] != True:
            print('Failure in fetching data from exchangerate.host, will retry later')
        else:
            inr_price = inr_price_json['rates']['INR']

    _price_headers = {
        'Host': 'production.api.coindesk.com',
        'Connection': 'keep-alive',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Microsoft Edge";v="90"',
        'Accept': 'application/json, text/plain, */*',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36 Edg/90.0.818.66',
        'Origin': 'https://www.coindesk.com',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.coindesk.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    bat_price_request = requests.get(
        'https://production.api.coindesk.com/v2/price/ticker/sparkline?assets=BAT', headers=_price_headers)
    if bat_price_request.status_code != 200:
        print('Failed to fetch data from coindesk.com, will retry later')
    else:
        bat_price_json = bat_price_request.json()
        if bat_price_json['message'] != 'OK':
            print('Failure in fetching data from coindesk.com, will retry later')
        else:
            bat_price = bat_price_json['data']['BAT']['sparkline'][-1][1]

    usdt_price_request = requests.get(
        'https://production.api.coindesk.com/v2/price/ticker/sparkline?assets=USDT', headers=_price_headers)
    if usdt_price_request.status_code != 200:
        print('Failed to fetch data from coindesk.com, will retry later')
    else:
        usdt_price_json = usdt_price_request.json()
        if usdt_price_json['message'] != 'OK':
            print('Failure in fetching data from coindesk.com, will retry later')
        else:
            usdt_price = usdt_price_json['data']['USDT']['sparkline'][-1][1]

    db_ops.set_price_rates(bat_price, inr_price, usdt_price)


def update_drive_sizes(_: CallbackContext) -> None:
    print('Updating drive sizes now...')
    drive_update_list = list()
    drive_ids = db_ops.get_global_drive_ids()
    for _id in drive_ids:
        _id = _id[0]
        rclone_size_cmd = f"""rclone size GD: --drive-team-drive \"{_id}\""""
        process = subprocess.Popen(shlex.split(
            rclone_size_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = process.communicate()[0]
        stderr = process.communicate()[1]

        if not len(stderr.decode('utf-8')) == 0:
            print("Error occured", stderr.decode('utf-8'))
        else:
            drive_size = stdout.decode('utf-8').split('\n')[1].split()[2]
            drive_size_dict = {
                'drive_id': _id,
                'drive_size': drive_size,
            }
            drive_update_list.append(drive_size_dict)
    db_ops.set_drive_sizes(drive_update_list)


j = updater.job_queue
j.run_repeating(update_prices, 600, 5)
j.run_repeating(update_drive_sizes, 86400, 600)
