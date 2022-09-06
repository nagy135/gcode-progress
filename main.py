from enum import Enum
import math

FILEPATH = "./test.gcode"
VERBOSE = True
unknown_directives: set[str] = set()

class Directives(Enum):
    HOME_ALL_AXES = "G28"
    LINEAR_MOVE = "G1"
    RESET_EXTRUDER = "G92"

IGNORED_DIRECTIVES = {
    Directives.RESET_EXTRUDER.value
}


class State:
    x: float
    y: float
    z: float
    f: float | None
    layer: int
    seconds_passed: float

    time_uses = list[float]

    def __repr__(self):

        return '''
===========================
[positions]
(
  x: {},
  y: {},
  z: {}
)
[f]: {},
[layer]: {},
[sec_passed]: {},
===========================
        '''.format(
            self.x,
            self.y,
            self.z,
            self.f,
            self.layer,
            self.seconds_passed,
        )

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.f = None
        self.seconds_passed = 0.0
        self.layer = 0

    def home(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def layer_changed(self, increased: bool):
        self.layer += 1 if increased else -1
        print('layer changed: %d' % self.layer)

    def move(
        self,
        x: float | None,
        y: float | None,
        z: float | None,
        f: float | None,
    ):
        previous_x = self.x
        previous_y = self.y
        previous_z = self.z
        previous_f = self.f
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if z is not None:
            self.z = z
            if previous_z != self.z:
                self.layer_changed(self.z > previous_z)
        if f is not None:
            self.f = f

        if self.f is None and previous_f is None:
            raise Exception('no feed rate specified')
        elif self.f is None and previous_f is not None:
            mm_per_second = previous_f / 60
        elif self.f is not None:
            mm_per_second = self.f / 60
        else:
            raise Exception('mm_per_second cant be calculated without feed rate')

        segment_length = math.sqrt(
            (self.x - previous_x)**2 +
            (self.y - previous_y)**2 +
            (self.z - previous_z)**2
        )

        move_time = segment_length / mm_per_second
        self.seconds_passed += move_time

        if VERBOSE:
            print(self)


def main():
    positions = State()
    lines: list[list[str]] = []
    with open(FILEPATH, "r") as f:
        for line in f:
            line = line.split(";")[0]  # remove comments
            line = line.strip()  # remove comment margins
            line = line.split()  # split to directives
            lines.append(line)

    for line in lines:
        handle_line(line, positions)

    if len(unknown_directives):
        print('UNKNOWN DIRECTIVES:')
        print(unknown_directives)


def parse_to_xyzf(line: list[str]) -> list[float | None]:
    x = None
    y = None
    z = None
    f = None
    for item in line:
        coordinate = item[0].lower()
        if coordinate == "x":
            x = float(item[1:])
        elif coordinate == "y":
            y = float(item[1:])
        elif coordinate == "z":
            z = float(item[1:])
        elif coordinate == "f":
            f = float(item[1:])
    return [x, y, z, f]


def handle_line(line: list[str], position: State):
    directive = line[0]
    if directive == Directives.HOME_ALL_AXES.value:
        position.home()
    elif directive == Directives.LINEAR_MOVE.value:
        xyzf = parse_to_xyzf(line[1:])
        position.move(*xyzf)
    elif directive in IGNORED_DIRECTIVES:
        pass
    else:
        print('UNRECOGNIZED', directive)
        unknown_directives.add(directive)


if __name__ == "__main__":
    main()
