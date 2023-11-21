import operator
import random

from gamelib import *
from pwn import remote, context

# context.log_level = 'debug'

# See the "SampleServiceInterface" from gamelib for a bigger example
# See https://gitlab.saarsec.rocks/saarctf/gamelib/-/blob/master/docs/howto_checkers.md for documentation.

PORT = 24929

PASSWORD_KEY = "password"

# List of common German female names, generated from the name-database at https://www.heise.de/ct/ftp/07/17/182/ with the following command:
# grep -xE '(F|1F|\?F|\?)\s+[A-Za-z]{4,}\s+.*' 0717-182/nam_dict.txt|grep -xE '.{43}[456789ABCD].*'|cut -d' ' -f3| xargs
NAMES = "Adele Adelheid Agnes Alexandra Alice Aloisia Amalia Andrea Angela Angelika Anita Anja Anna Annelies Anneliese Annemarie Anni Antonia Astrid Auguste Aurelia Barbara Beate Beatrix Bernadette Berta Bettina Bianca Birgit Brigitta Brigitte Brunhilde Carina Carmen Caroline Charlotte Christa Christiane Christina Christine Claudia Cornelia Dagmar Daniela Doris Dorothea Edeltraud Edith Eleonore Elfi Elfriede Elisabeth Elke Elsa Elvira Emilie Emma Erika Erna Ernestine Eveline Evelyn Evelyne Franziska Frieda Friederike Gabi Gabriela Gabriele Gerda Gerlinde Gerti Gertraud Gertraude Gertrud Gertrude Gisela Grete Gudrun Hannelore Hedwig Heide Heidelinde Heidemarie Heidi Heidrun Heike Helene Helga Henriette Hermine Herta Hertha Hilda Hilde Hildegard Ilse Ines Inge Ingeborg Ingrid Irene Iris Irma Irmgard Irmtraud Isabella Isolde Jasmine Johanna Josefa Josefine Judith Julia Juliana Juliane Jutta Karin Karoline Katharina Kathrin Katrin Kerstin Klara Klaudia Kornelia Leopoldine Lieselotte Lisa Liselotte Lotte Lucia Luise Lydia Magdalena Manuela Margareta Margarete Margaretha Margarethe Margit Margot Margret Marianne Marie Marina Marion Marlene Marlies Martha Martina Mathilde Melanie Melitta Michaela Monika Natascha Nicole Nina Ottilie Patricia Paula Pauline Petra Regina Renate Rita Romana Rosa Rosalia Rosemarie Rosi Rosina Rosmarie Roswitha Ruth Sabine Sabrina Sandra Sieglinde Sigrid Silke Silvia Simone Sonja Sophie Stefanie Stephanie Susanna Susanne Sylvia Tanja Therese Theresia Traude Trude Ulrike Ursula Vera Verena Veronika Viktoria Walpurga Waltraud Wilhelmine Wilma Yvonne".split()


class SaaSSaaSSaaSSaaSInterface(ServiceInterface):
    name = 'SaaSSaaSSaaSSaaS'
    flag_id_types = ['alphanum16']

    def check_integrity(self, team: Team, tick: int):
        # pwntools "Could not connect" exception is accepted as OFFLINE
        try:
            conn = remote(team.ip, PORT, timeout=TIMEOUT, ssl=True)
        except TimeoutError:
            raise OfflineException("Could not connect")
        try:
            menu = conn.recvuntil(b'Your choice')
            try:
                menu_text = menu.decode('ascii')
            except UnicodeDecodeError:
                raise MumbleException("Service returned non-ascii data")
            # check for conditions - if an assert fails the service status is MUMBLE
            expected_menu_items = ['1 - Run Program', '2 - Create new public program', '3 - Create new private script']
            assert all(item in menu_text for item in expected_menu_items), 'Main Menu Missing!'
        finally:
            # closing resources is important
            conn.close()

    def store_flags(self, team: Team, tick: int):
        flag_type = tick % 2  # Private programs on even, public programs on odd ticks
        flag = self.get_flag(team, tick, flag_type)
        program_name = self.get_flag_id(team, tick, 0)

        if flag_type == 0:
            self._store_private_flag(team, tick, flag, program_name)
        else:
            self._store_public_flag(team, tick, flag, program_name)

    def _store_private_flag(self, team: Team, tick: int, flag: str, program_name: str):
        # have we already stored this flag (== did we receive a password for it)?
        if self.load(team, tick, PASSWORD_KEY) is not None:
            print(f"Flag already stored (= we recorded a password for it)")
            return
        try:
            conn = remote(team.ip, PORT, timeout=TIMEOUT, ssl=True)
        except TimeoutError:
            raise OfflineException("Could not connect")
        try:
            conn.recvuntil(b'Your choice')
            print("Selecting private program")
            conn.sendline(b'3')
            conn.recvuntil(b'Please enter a name for your program:')
            print(f"Sending program name {program_name}")
            conn.sendline(program_name.encode())
            conn.recvuntil(b'Your password is:')
            password = conn.recvline().decode().strip()
            print(f"Received password {password}")
            conn.recvuntil(b'Terminate your input with a blank line')
            program = generate_private_program(flag)
            print("Sending program...")
            for line in program.splitlines():
                if line.strip():  # send all non-empty lines
                    conn.sendline(line.encode())
                    print(line)
            conn.sendline()  # send blank line to terminate upload
            conn.recvall()
            print("Program sent!")
            # Store password (also signals that we've stored this flag already)
            self.store(team, tick, PASSWORD_KEY, password)
        finally:
            conn.close()

    def _store_public_flag(self, team: Team, tick: int, flag: str, program_name: str):
        # have we already stored this flag (== did we receive a password for it)?
        if self.load(team, tick, PASSWORD_KEY) is not None:
            print(f"Flag already stored (= we recorded a password for it)")
            return
        try:
            conn = remote(team.ip, PORT, timeout=TIMEOUT, ssl=True)
        except TimeoutError:
            raise OfflineException("Could not connect")
        try:
            conn.recvuntil(b'Your choice')
            print("Selecting public program")
            conn.sendline(b'2')
            conn.recvuntil(b'Please enter a name for your program:')
            print(f"Sending program name {program_name}")
            conn.sendline(program_name.encode())
            password = usernames.generate_password()
            print(f"Generated password {password}")
            conn.recvuntil(b'Terminate your input with a blank line')
            program = generate_public_program(flag, password)
            print("Sending program...")
            for line in program.splitlines():
                if line.strip():  # send all non-empty lines
                    conn.sendline(line.encode())
                    print(line)
            conn.sendline()  # send blank line to terminate upload
            conn.recvall()
            print("Program sent!")
            # Store password (also signals that we've stored this flag already)
            self.store(team, tick, PASSWORD_KEY, password)
        finally:
            conn.close()

    def retrieve_flags(self, team: Team, tick: int):
        flag_type = tick % 2  # Private programs on even, public programs on odd ticks
        flag = self.get_flag(team, tick, flag_type)
        program_name = self.get_flag_id(team, tick, 0)
        try:
            conn = remote(team.ip, PORT, timeout=TIMEOUT, ssl=True)
        except TimeoutError:
            raise OfflineException("Could not connect")
        password = self.load(team, tick, PASSWORD_KEY)
        try:
            conn.recvuntil(b'Your choice')
            print("Selecting run")
            conn.sendline(b'1')
            conn.recvuntil(b'Please enter the name of the program you\'d like to run:')
            print(f"Sending program name {program_name}")
            conn.sendline(program_name.encode())
            response = conn.recvuntil([b'Error, no such program!', b'Running', b'Please enter the password: '])
            if b'Error, no such program!' in response:
                raise FlagMissingException(f"Could not retrieve flag for flag_id {program_name}")

            # The following is a little hack: We *always* send the stored password
            # 1. For private programs, the front-end will next ask for the password
            # 2. For public programs, the program itself will ask for it
            print(f"Sending password {password}")
            conn.sendline(password)
            data = conn.recvall()
            print(f"Received output: {data.decode()}")
        finally:
            conn.close()
        if flag not in data.decode():
            # verbose error logging is always a good idea
            print('GOT:', data)
            # flag not found? Raise FlagMissingException
            raise FlagMissingException('Flag not found')


def generate_arith_inv_expr(val, nest_prob=0.5):
    # python-operators and their saarlang-inverse
    ops = [
        (operator.add, 'nimm ford'),
        (operator.sub, 'babbe an'),
        (operator.xor, 'verkrumbele'),
    ]
    mask = random.randint(1, 0xffff)
    # choose a random operator
    op, inv = random.choice(ops)
    # apply random operator and mask
    masked = (op(val, mask)) & 0xffff

    ## with a given probability, replace masked value with another expression
    if random.random() < nest_prob:
        masked = generate_arith_inv_expr(masked, nest_prob / 2)
    if random.random() < nest_prob:
        mask = generate_arith_inv_expr(mask, nest_prob / 2)

    # generate inverse statement in saarlang
    return f"({masked} {inv} {mask})"


def generate_arith_inv_prg(val, name_pool):
    variable_name = random.choice(sorted(name_pool))
    name_pool.discard(variable_name)
    value_expr = generate_arith_inv_expr(val)
    prg = f"Mach 's {variable_name} {value_expr}.\n"
    expr = f"'s {variable_name}"
    return expr, prg,


def find_constants(expr):
    return re.findall(r'\b\d+\b', expr)


def generate_arith_inv_expr_with_args(val, name_pool):
    expr = generate_arith_inv_expr(val)
    consts = sorted(set(find_constants(expr)))

    n_args = random.randint(0, len(consts))
    const_args = random.sample(consts, n_args)
    args = []
    for const in const_args:
        variable_name = random.choice(sorted(name_pool))
        name_pool.discard(variable_name)
        args.append((variable_name, const))
        expr = re.sub(fr"\b{const}\b", f"'s {variable_name}", expr)
    return expr, args


def generate_function_with_args(val, name_pool):
    function_name = random.choice(sorted(name_pool))
    name_pool.discard(function_name)
    value_expr, value_args = generate_arith_inv_expr_with_args(val, name_pool)
    params = " ".join(f"holle 's {name} unn dann" for name, _ in value_args)
    prg = f"""Vergliggere 's {function_name} {params} mach allemohl
     Tappe hemm unn holle {value_expr}.
Aweil is awwer Schluss!
"""
    args = " ".join(f"holle {value} unn dann" for _, value in value_args)
    return f"{args} geh uff Trulla bei 's {function_name}", prg


GENERATORS = [generate_arith_inv_prg, generate_function_with_args]


def generate_string_expr(value: str, name_pool: set[str]) -> [str, str]:
    variable_name = random.choice(sorted(name_pool))
    name_pool.discard(variable_name)

    definitions = []

    program = f"Mach 's {variable_name} \"\".\n"
    for c in value:
        gen_func = random.choice(GENERATORS)
        expr, new_program = gen_func(ord(c), name_pool)
        # add new lines to program
        definitions.append(new_program)
        # append to global variables
        program += f"Mach 's {variable_name} 's {variable_name} babbe an {expr}.\n"

    # combine definitions in a random order, then append the join/output-part
    random.shuffle(definitions)
    program = "\n".join(definitions) + program

    return f"'s {variable_name}", program


def generate_private_program(flag: str) -> str:
    name_pool = set(NAMES)
    flag_expr, program = generate_string_expr(flag, name_pool)
    program += f"Brundse {flag_expr}!\n"

    return program


def generate_readline(name_pool: set[str]) -> [str, str]:
    function_name = random.choice(sorted(name_pool))
    name_pool.discard(function_name)
    return_variable_name = random.choice(sorted(name_pool))
    name_pool.discard(return_variable_name)
    read_variable_name = random.choice(sorted(name_pool))
    name_pool.discard(read_variable_name)
    readline_prg = f"""Vergliggere 's {function_name} mach allemohl
    Mach 's {return_variable_name} ""
    Schnäge 's {read_variable_name}.
    Solang 's {read_variable_name} iss besser als 31 mach allemohl
        Mach 's {return_variable_name} 's {return_variable_name} babbe an 's {read_variable_name}.
        Schnäge 's {read_variable_name}.
    Aweil is awwer schluss.
    Tappe hemm unn holle 's {return_variable_name}.
Aweil is awwer Schluss!
"""
    return f"geh uff Trulla bei 's {function_name}", readline_prg


def generate_public_program(flag: str, password: str) -> str:
    name_pool = set(NAMES)
    flag_expr, flag_program = generate_string_expr(flag, name_pool)
    password_expr, password_program = generate_string_expr(password, name_pool)
    input_expr, input_program = generate_readline(name_pool)
    program = password_program
    program += input_program
    program += flag_program
    program += f"""Brundse "[saarsec secure vault] Please enter password: "
Wenn {input_expr} iss {password_expr} mach allemohl
    Brundse {flag_expr}
Aweil is awwer Schluss!
"""

    return program


if __name__ == '__main__':
    import sys

    # USAGE: python3 interface.py                      # test against localhost
    # USAGE: python3 interface.py 1.2.3.4              # test against IP
    # USAGE: python3 interface.py 1.2.3.4 retrieve     # retrieve last 10 ticks (for exploits relying on checker interaction)
    # (or use gamelib/run-checkers to test against docker container)
    team = Team(1, 'TestTeam', sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1')
    service = SaaSSaaSSaaSSaaSInterface(1)

    if len(sys.argv) > 2 and sys.argv[2] == 'retrieve':
        for tick in range(1, 10):
            try:
                service.retrieve_flags(team, tick)
            except:
                pass
        sys.exit(0)

    for tick in range(1, 4):
        print(f'\n\n=== TICK {tick} ===')
        service.check_integrity(team, tick)
        service.store_flags(team, tick)
        service.retrieve_flags(team, tick)
