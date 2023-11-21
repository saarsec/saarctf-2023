import os
import time

import redis

FILES: list[tuple[str, str, bytes]] = []
DIR = 'redisbbq-frontend'
with open('admin-password.txt', 'r') as f:
    ADMIN_PASSWORD = f.read().strip()


def get_mime(filename: str) -> str:
    if filename.endswith('.html'):
        return 'text/html; charset=utf-8'
    if filename.endswith('.css'):
        return 'text/css; charset=utf-8'
    if filename.endswith('.js'):
        return 'application/javascript; charset=utf-8'
    if filename.endswith('.ico'):
        return 'image/x-icon'
    if filename.endswith('.map'):
        return 'application/json; charset=utf-8'
    return 'text/plain'


def read_folder(dir: str, base: str = '') -> None:
    global FILES
    for f in os.listdir(dir):
        if os.path.isdir(f'{dir}/{f}'):
            read_folder(f'{dir}/{f}', f'{base}/{f}')
        else:
            with open(f'{dir}/{f}', 'rb') as fd:
                content = fd.read()
                FILES.append((f'{base}/{f}', get_mime(f), content))
                if f == 'index.html':
                    FILES.append((f'{base}/', get_mime(f), content))


def add_headers_for_file(content: bytes, mime: str) -> bytes:
    headers = {'Content-Type': mime, 'Connection': 'close', 'Content-Length': len(content)}
    if mime.startswith('image/'):
        headers['Cache-Control'] = 'public, max-age=604800, immutable'
    return '\r\n'.join(f'{k}: {v}' for k, v in headers.items()).encode() + b'\r\n\r\n' + content


def init_redis(ip: str, port: int) -> None:
    client = redis.Redis(ip, port, single_connection_client=True)
    client.execute_command('AUTH', 'admin', ADMIN_PASSWORD)
    for path, mime, content in FILES:
        client.set(path, add_headers_for_file(content, mime))
    print(f'Added {len(FILES)} files to redis')
    client.close()


if __name__ == '__main__':
    read_folder(DIR)
    try:
        init_redis('127.0.0.1', 12345)
    except redis.connection.ConnectionError:
        # give server some more time to start
        time.sleep(2)
        init_redis('127.0.0.1', 12345)
