from enum import Enum
import math

FILEPATH = "./test.gcode"
VERBOSE = True
unknown_directives: set[str] = set()


class Directives(Enum):
    HOME_ALL_AXES = "G28"
    LINEAR_MOVE = "G1"
    EMPTY_LINEAR_MOVE = "G0"
    RESET_EXTRUDER = "G92"
    DISABLE_ALL_STEPPERS = "M84"
    FAN_OFF = "M107"
    SETUP_ACCELERATION = "M204"
    SETUP_JERK = "M205"
    SETUP_MAX_ACCELERATION = "M201"
    SETUP_MAX_FEEDRATE = "M203"
    RESET_FEEDRATE = "M220"
    RESET_FLOWRATE = "M221"
    ABSOLUTE_POSITIONING = "G90"
    RELATIVE_POSITIONING = "G91"
    TURN_OFF_HOTEND = "M104"
    TURN_OFF_BED = "M140"
    TURN_OFF_FAN = "M106"
    REPORT_TEMPERATURES = "M105"
    WAIT_FOR_TEMPERATURES = "M109"
    WAIT_FOR_BED_TEMPERATURE = "M190"
    E_ABSOLUTE = "M82"

class MoveModes(Enum):
    RELATIVE = "relative"
    ABSOLUTE = "absolute"

IGNORED_DIRECTIVES = {
    Directives.RESET_EXTRUDER.value,
    Directives.DISABLE_ALL_STEPPERS.value,
    Directives.RESET_FEEDRATE.value,
    Directives.RESET_FLOWRATE.value,
    Directives.FAN_OFF.value,
    Directives.SETUP_ACCELERATION.value,
    Directives.SETUP_JERK.value,
    Directives.SETUP_MAX_ACCELERATION.value,
    Directives.SETUP_MAX_FEEDRATE.value,
    Directives.TURN_OFF_BED.value,
    Directives.TURN_OFF_FAN.value,
    Directives.TURN_OFF_HOTEND.value,
    Directives.REPORT_TEMPERATURES.value,
    Directives.WAIT_FOR_TEMPERATURES.value,
    Directives.WAIT_FOR_BED_TEMPERATURE.value,
    Directives.E_ABSOLUTE.value,
}


class State:
    x: float
    y: float
    z: float
    f: float | None
    layer: int
    seconds_passed: float
    move_mode: MoveModes

    time_uses = list[float]

    def __repr__(self):
        return f"""
===========================
[positions]
(
  x: {self.x},
  y: {self.y},
  z: {self.z}
)
[f]: {self.f},
[layer]: {self.layer},
[sec_passed]: {self.seconds_passed},
===========================
        """

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.f = None
        self.seconds_passed = 0.0
        self.layer = 0
        self.move_mode = MoveModes.ABSOLUTE

    def home(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def layer_changed(self, increased: bool):
        self.layer += 1 if increased else -1
        print("layer changed: %d" % self.layer)

    def change_move_mode(self, new: MoveModes):
        self.move_mode = new

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
        absolute = self.move_mode == MoveModes.ABSOLUTE
        if x is not None:
            self.x = x if absolute else previous_x + x
        if y is not None:
            self.y = y if absolute else previous_y + y
        if z is not None:
            self.z = z if absolute else previous_z + z
            if previous_z != self.z:
                self.layer_changed(self.z > previous_z)
        if f is not None:
            self.f = f

        if self.f is None and previous_f is None:
            raise Exception("no feed rate specified")
        elif self.f is None and previous_f is not None:
            mm_per_second = previous_f / 60
        elif self.f is not None:
            mm_per_second = self.f / 60
        else:
            raise Exception("mm_per_second cant be calculated without feed rate")

        segment_length = math.sqrt(
            (self.x - previous_x) ** 2
            + (self.y - previous_y) ** 2
            + (self.z - previous_z) ** 2
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
            line = line.strip()  # remove comment margins
            if line == "":
                continue
            line = line.split(";")[0]  # remove comments
            line = line.strip()  # remove comment margins
            line = line.split()  # split to directives
            if len(line):
                lines.append(line)

    for line in lines:
        handle_line(line, positions)

    if len(unknown_directives):
        print("UNKNOWN DIRECTIVES:")
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


def handle_line(line: list[str], state: State):
    directive = line[0]
    if directive == Directives.HOME_ALL_AXES.value:
        state.home()
    elif directive in {
        Directives.LINEAR_MOVE.value,
        Directives.EMPTY_LINEAR_MOVE.value,
    }:
        xyzf = parse_to_xyzf(line[1:])
        state.move(*xyzf)
    elif directive == Directives.ABSOLUTE_POSITIONING.value:
        state.change_move_mode(MoveModes.ABSOLUTE)
    elif directive == Directives.RELATIVE_POSITIONING.value:
        state.change_move_mode(MoveModes.RELATIVE)
    elif directive in IGNORED_DIRECTIVES:
        pass
    else:
        unknown_directives.add(directive)


if __name__ == "__main__":
    main()
