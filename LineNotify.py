import requests
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

token = config['credential']['TOKEN']


def send_line_notify(notification_message):
    line_notify_token = token
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': notification_message}
    r = requests.post(line_notify_api, headers=headers, data=data)
    print('status: ', r.status_code)
    print('response: ', r.content)
if __name__ == '__main__':
    send_line_notify('呱！')