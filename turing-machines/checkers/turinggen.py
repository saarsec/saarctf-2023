import json
import random
import string
import struct
from typing import List, Optional, Dict


def random_str(length) -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


# b >= ' ' && b <= '~' && b != '"' && b != '\\'
CHAR_BYTES = set(i for i in range(ord(' '), ord('~') + 1) if i != ord('"') and i != ord('\\'))
SAFE_BYTES = list(range(0, ord('0'))) + \
             list(range(ord('9') + 1, ord('A'))) + \
             list(range(ord('G'), ord('a'))) + \
             list(range(ord('g'), 256))
SAFE_STRING = [i for i in SAFE_BYTES if ord(' ') <= i <= ord('~')]
UNSAFE_STRING = [i for i in range(ord(' '), ord('~') + 1)]


def random_tape() -> bytes:
    tape = b''
    for _ in range(random.randint(3, 12)):
        r = random.randint(0, 100)
        if r < 80:
            for _ in range(8):
                if tape and tape[-1] not in CHAR_BYTES:
                    tape += bytes([random.choice(SAFE_BYTES)])
                else:
                    tape += bytes([random.randint(0, 255)])
        elif r < 90:
            for _ in range(random.randint(7, 18)):
                if tape and tape[-1] not in CHAR_BYTES:
                    tape += bytes([random.choice(SAFE_STRING)])
                else:
                    tape += bytes([random.choice(UNSAFE_STRING)])
            tape += b'\x00'
        elif r < 95:
            tape += b'\x00\x00\x00\x00'
        else:
            tape += b'\x00\x00\x00\x00\x00\x00\x00\x00'
    return tape


class TuringMachine:
    def __init__(self, name: str):
        self.name = name
        self.states: List[Dict] = []
        self.initial_tape: bytes = random_tape()
        self.tape: List[int] = list(self.initial_tape)
        self.position = 0
        self.final_state: Optional[str] = None
        self.register_values = [0] * 16

    def add_state(self, name: str, actions: List):
        self.states.append({'name': name, 'actions': actions or []})

    def json(self) -> str:
        return json.dumps({'name': self.name, 'states': self.states})

    def json_states(self) -> str:
        return json.dumps(self.states)

    def final_tape(self) -> bytes:
        return bytes(self.tape)

    def write_constant(self, prefix, final_h, final_s, value):
        """
        Write an 8b constant to tape. Then move the head by <final_h> bytes and go to state <final_s>
        :param prefix: Name of the states: <prefix>0-<prefix>7
        :param final_h:
        :param final_s:
        :param value:
        :return:
        """
        for i in range(7):
            v = value & 0xff
            value = value >> 8
            self.add_state(f'{prefix}{i}', [{'a': [f'h={v}'], 'h': 1, 's': f'{prefix}{i + 1}'}])
            self.tape[self.position + i] = v
        value &= 0xff
        self.add_state(f'{prefix}7', [{'a': [f'h={value}'], 'h': final_h - 7, 's': final_s}])
        self.tape[self.position + 7] = value
        self.position += final_h

    def read_into_r07(self, prefix, final_h, final_s):
        """
        Copy 8 bytes from tape to registers r0..r7. Then move the head by <final_h> bytes and go to state <final_s>
        :param prefix: Name of the states: <prefix>0-<prefix>7
        :param final_h:
        :param final_s:
        :return:
        """
        for i in range(7):
            self.add_state(f'{prefix}{i}', [{'a': [f'r{i}=h'], 'h': 1, 's': f'{prefix}{i + 1}'}])
        self.add_state(f'{prefix}7', [{'a': [f'r7=h'], 'h': final_h - 7, 's': final_s}])
        self.register_values = self.tape[self.position:self.position+8] + self.register_values[8:]
        self.position += final_h

    def read_into_r8f(self, prefix, final_h, final_s):
        """
        Copy 8 bytes from tape to registers r8..rf. Then move the head by <final_h> bytes and go to state <final_s>
        :param prefix: Name of the states: <prefix>0-<prefix>7
        :param final_h:
        :param final_s:
        :return:
        """
        for i in range(7):
            self.add_state(f'{prefix}{i}', [{'a': [f'r{hex(i + 8)[2:]}=h'], 'h': 1, 's': f'{prefix}{i + 1}'}])
        self.add_state(f'{prefix}7', [{'a': [f'rf=h'], 'h': final_h - 7, 's': final_s}])
        self.register_values = self.register_values[:8] + self.tape[self.position:self.position+8]
        self.position += final_h

    def write_r07(self, prefix, final_h, final_s):
        """
        Copy 8 bytes from registers r0..r7 to tape. Then move the head by <final_h> bytes and go to state <final_s>
        :param prefix: Name of the states: <prefix>0-<prefix>7
        :param final_h:
        :param final_s:
        :return:
        """
        for i in range(7):
            self.add_state(f'{prefix}{i}', [{'a': [f'h=r{i}'], 'h': 1, 's': f'{prefix}{i + 1}'}])
        self.add_state(f'{prefix}7', [{'a': [f'h=r7'], 'h': final_h - 7, 's': final_s}])
        self.tape = self.tape[:self.position] + self.register_values[:8] + self.tape[self.position + 8:]
        self.position += final_h

    def write_r8f(self, prefix, final_h, final_s):
        """
        Copy 8 bytes from registers r8..rf to tape. Then move the head by <final_h> bytes and go to state <final_s>
        :param prefix: Name of the states: <prefix>0-<prefix>7
        :param final_h:
        :param final_s:
        :return:
        """
        for i in range(7):
            self.add_state(f'{prefix}{i}', [{'a': [f'h=r{hex(i + 8)[2:]}'], 'h': 1, 's': f'{prefix}{i + 1}'}])
        self.add_state(f'{prefix}7', [{'a': [f'h=rf'], 'h': final_h - 7, 's': final_s}])
        self.tape = self.tape[:self.position] + self.register_values[8:16] + self.tape[self.position + 8:]
        self.position += final_h

    def sub(self, prefix, final_h, final_s, value, bytesize=8):
        """
        Subtract value from the 8byte little-endian value under head
        :param prefix:
        :param final_h:
        :param final_s:
        :param value:
        :return:
        """
        initial_value = value
        for i in range(bytesize - 1):
            v = value & 0xff
            value = value >> 8
            self.add_state(f'{prefix}{i}', [
                {'c': f'h<{v}', 'a': [f'h=h-{v}'], 'h': 1, 's': f'{prefix}{i + 1}_1'},
                {'c': f'h>={v}', 'a': [f'h=h-{v}'], 'h': 1, 's': f'{prefix}{i + 1}'},
            ])
            self.add_state(f'{prefix}{i}_1', [
                {'c': f'h<{v + 1}', 'a': [f'h=h-{v + 1}'], 'h': 1, 's': f'{prefix}{i + 1}_1'},
                {'c': f'h>={v + 1}', 'a': [f'h=h-{v + 1}'], 'h': 1, 's': f'{prefix}{i + 1}'},
            ])
        v = value & 0xff
        self.add_state(f'{prefix}{bytesize - 1}', [
            {'a': [f'h=h-{v}'], 'h': final_h + 1 - bytesize, 's': final_s},
        ])
        self.add_state(f'{prefix}{bytesize - 1}_1', [
            {'a': [f'h=h-{v + 1}'], 'h': final_h + 1 - bytesize, 's': final_s},
        ])
        x, = struct.unpack('<Q', bytes(self.tape[self.position:self.position + bytesize] + [0] * (8 - bytesize)))
        x = struct.pack('<Q', (x - initial_value) & 0xffffffffffffffff)[:bytesize]
        self.tape = self.tape[:self.position] + list(x) + self.tape[self.position + bytesize:]
        self.position += final_h

    def add(self, prefix, final_h, final_s, value, bytesize=8):
        """
        Add value from the 8byte little-endian value under head
        :param prefix:
        :param final_h:
        :param final_s:
        :param value:
        :return:
        """
        initial_value = value
        for i in range(bytesize - 1):
            v = value & 0xff
            value = value >> 8
            self.add_state(f'{prefix}{i}', [
                {'c': f'h>{0xff - v}', 'a': [f'h=h+{v}'], 'h': 1, 's': f'{prefix}{i + 1}_1'},
                {'c': f'h<={0xff - v}', 'a': [f'h=h+{v}'], 'h': 1, 's': f'{prefix}{i + 1}'},
            ])
            self.add_state(f'{prefix}{i}_1', [
                {'c': f'h>{0xfe - v}', 'a': [f'h=h+{v + 1}'], 'h': 1, 's': f'{prefix}{i + 1}_1'},
                {'c': f'h<={0xfe - v}', 'a': [f'h=h+{v + 1}'], 'h': 1, 's': f'{prefix}{i + 1}'},
            ])
        v = value & 0xff
        self.add_state(f'{prefix}{bytesize - 1}', [
            {'a': [f'h=h+{v}'], 'h': final_h + 1 - bytesize, 's': final_s},
        ])
        self.add_state(f'{prefix}{bytesize - 1}_1', [
            {'a': [f'h=h+{v + 1}'], 'h': final_h + 1 - bytesize, 's': final_s},
        ])
        x, = struct.unpack('<Q', bytes(self.tape[self.position:self.position + bytesize] + [0] * (8 - bytesize)))
        x = struct.pack('<Q', (x + initial_value) & 0xffffffffffffffff)[:bytesize]
        self.tape = self.tape[:self.position] + list(x) + self.tape[self.position + bytesize:]
        self.position += final_h

    def strlen(self, prefix, final_h, final_s):
        if 0 not in self.tape[self.position:] or self.position == 0:
            print('... skip strlen ...')
            self.add_state(f'{prefix}0', [{'h': final_h, 's': final_s}])
            self.position += final_h
            return

        self.add_state(f'{prefix}0', [{'a': ['r0=0'], 's': f'{prefix}1'}])
        self.add_state(f'{prefix}1', [
            {'c': 'h==0', 'a': ['r1=r0'], 'h': -1, 's': f'{prefix}2'},
            {'c': 'h!=0', 'a': ['r0=r0+1'], 'h': 1, 's': f'{prefix}1'}
        ])
        self.add_state(f'{prefix}2', [
            {'c': 'r1>0', 'a': ['r1=r1-1'], 'h': -1, 's': f'{prefix}2'},
            {'c': 'r1==0', 'a': ['h=r0'], 'h': 1 + final_h, 's': final_s}
        ])
        strlen = 0
        for x in self.tape[self.position:]:
            if x == 0:
                break
            else:
                strlen += 1
        self.register_values[0] = strlen
        self.register_values[1] = 0
        self.tape[self.position - 1] = strlen
        self.position += final_h


def generate_random_machine(name: str) -> TuringMachine:
    m = TuringMachine(name)
    random_steps = []  # (position, prefix, method, params)
    written_regs = []
    for _ in range(random.randint(7, 24)):
    #for _ in range(1):
        prfx = random_str(random.randint(8, 14))
        pos = random.randint(0, len(m.tape) - 8)
        r = random.randint(0, 7)
        if r == 0:
            random_steps.append((pos, prfx, m.write_constant, [random.randint(0, 0x7fffffffffffffff)]))
        elif r == 1:
            random_steps.append((pos, prfx, m.sub, [random.randint(0, 0x7fffffffffffffff), 8]))
        elif r == 2:
            random_steps.append((pos, prfx, m.sub, [random.randint(0, 0x7fffffff), 4]))
        elif r == 3:
            random_steps.append((pos, prfx, m.add, [random.randint(0, 0x7fffffffffffffff), 8]))
        elif r == 4:
            random_steps.append((pos, prfx, m.add, [random.randint(0, 0x7fffffff), 4]))
        elif r == 5:
            if random.randint(0, 100) < 50:
                random_steps.append((pos, prfx, m.read_into_r07, []))
                written_regs.append(m.write_r07)
            else:
                random_steps.append((pos, prfx, m.read_into_r8f, []))
                written_regs.append(m.write_r8f)
        elif r == 6:
            random_steps.append((pos, prfx, m.write_r07 if len(written_regs) == 0 else random.choice(written_regs), []))
        elif r == 7:
            random_steps.append((pos // 2, prfx, m.strlen, []))
    # random steps to states
    finish_name = random_str(random.randint(8, 14))
    m.add_state('initial', [{'a': [], 'h': random_steps[0][0], 's': random_steps[0][1] + '0'}])
    m.position = random_steps[0][0]
    for i, (pos, prefix, f, params) in enumerate(random_steps):
        print(f'- {i}: {f.__name__}{params}  position={pos}  prefix={prefix}')
        nextpos = random_steps[i+1][0] if i + 1 < len(random_steps) else m.position
        nextstate = random_steps[i+1][1]+'0' if i + 1 < len(random_steps) else finish_name
        f(prefix, nextpos - m.position, nextstate, *params)
    m.add_state(finish_name, [])
    m.final_state = finish_name
    return m


def check_cpp_code(machine: TuringMachine, code: str):
    for state in machine.states:
        assert f'return "{state["name"]}";' in code
    for c in [
        'class CompiledTuringMachine : public TuringMachine',
        'CompiledTuringMachine(uint8_t *tapeStart, uint8_t *tapeEnd) : TuringMachine(tapeStart, tapeEnd)',
        'bool run(int steps) override',
        'switch (state)'
    ]:
        assert c in code, 'Invalid code'
