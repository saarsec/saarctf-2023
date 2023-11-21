import hashlib
import secrets
import string

ADMIN_PASSWORD: str = ''.join(secrets.choice(string.ascii_letters) for _ in range(16))
USERS: dict[str, str] = {
    'default': 'user default on nopass -@all +NEWUSER +LRANGE +http.GET +http.POST +AUTH +PING +LOLWUT ~newest:* ~country:* ~/*',
    'admin': 'user admin on #' + hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest() + ' +@all ~*'
}

try:
    with open('users.acl', 'r') as f:
        lines = f.read().split('\n')
except FileNotFoundError:
    lines = []

for i, line in enumerate(lines):
    if line.startswith('user '):
        username = line.split(' ')[1]
        if username in USERS:
            lines[i] = USERS[username]
            del USERS[username]
for user in USERS.values():
    lines.append(user)

with open('users.acl', 'w') as f:
    f.write('\n'.join(lines))
with open('admin-password.txt', 'w') as f:
    f.write(ADMIN_PASSWORD + '\n')
print(f'New admin password: >>>  {ADMIN_PASSWORD}  <<<')
