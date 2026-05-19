import urllib.request
import subprocess
import platform

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_html(url):
    global headers
    try:
        if isinstance(url, str):
            url = urllib.parse.quote(url, safe='/:?=&')
        encoded_headers = {}
        for key, value in headers.items():
            if isinstance(value, str):
                encoded_headers[key] = value.encode('utf-8').decode('latin-1')
            else:
                encoded_headers[key] = value
        
        req = urllib.request.Request(url, headers=encoded_headers)
        response = urllib.request.urlopen(req)
        html_bytes = response.read()
        try:
            html = html_bytes.decode('utf-8')
        except UnicodeDecodeError:
            html = html_bytes.decode('gbk')
        return html
    except Exception as e:
        return f'[A] {e}'


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    count_param = '4'
    command = ['ping', param, count_param, host]
    try:
        response = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return response.stdout

    except Exception as e:
        return f'[A] {e}'