from pwn import *

p = remote("127.0.0.1", 30000)
context.log_level = "debug"

def recv_hello():
    p.recvuntil("Goodbye\n")


def recv_menu():
    p.recvuntil("message\n")


def create_task_dummy():
    p.sendline("Check my tasks")
    p.recvuntil("details\n")
    p.sendline("create task")
    p.recvline()
    p.sendline("asdf")
    p.recvline()
    p.sendline("asdf")
    p.recvline()
    p.sendline("asdf")
    p.recvline()
    p.sendline("asdf")
    p.recvline()
    p.sendline("asdf")
    p.recvline()
    p.sendline("3")
    recv_menu()



def dummy_login():
    recv_hello()
    p.sendline("login")
    p.recvline()
    p.sendline("a")
    p.recvline()
    p.sendline("a")
    p.recvline()
    p.sendline("a")
    recv_menu()


def main():
    dummy_login()
    create_task_dummy()
    p.interactive()


if __name__ == "__main__":
    main()
