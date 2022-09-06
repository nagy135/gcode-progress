FILEPATH='./test.gcode'

def main():
    lines: list[str] = []
    with open(FILEPATH, 'r') as f:
        for line in f:
            lines.append(line.strip())

if __name__ == '__main__':
    main()
