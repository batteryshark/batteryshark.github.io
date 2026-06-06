import sys


BOSHY_KEY = b"BLOB"
STATE_SIZE = 256


def build_key_schedule(key):
    state = list(range(STATE_SIZE))
    key_stream = [0] * STATE_SIZE
    key_index = 0

    if key:
        for index in range(STATE_SIZE):
            if key_index == len(key):
                key_index = 0
            key_stream[index] = key[key_index]
            key_index += 1

    swap_index = 0
    for index in range(STATE_SIZE):
        swap_index = (key_stream[index] + state[index] + swap_index) % STATE_SIZE
        state[index], state[swap_index] = state[swap_index], state[index]

    return state


def convert(data, key):
    state = build_key_schedule(key)
    swap_index = 0
    state_index = 0
    output = bytearray()

    for value in data:
        state_index = (state_index + 1) % STATE_SIZE
        swap_index = (swap_index + state[state_index]) % STATE_SIZE
        state[state_index], state[swap_index] = state[swap_index], state[state_index]
        stream_index = (state[swap_index] + state[state_index]) % STATE_SIZE
        output.append(value ^ state[stream_index])

    return bytes(output)


def main():
    with open(sys.argv[1], "rb") as save_file:
        data = save_file.read()

    sys.stdout.buffer.write(convert(data, BOSHY_KEY))


if __name__ == "__main__":
    main()
