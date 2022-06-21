import subprocess
from typing import Callable, Optional, Tuple, Union

# Use "aseqdump -l" to get the list of devices.
DEVICE_NAME = "Digital Keyboard"  # DO NOT LET THIS BE SET TO AN UNSANITISED VALUE!

KEYBOARD_EXIT = "C7"  # This is the top of my keyboard, pass in a different arguement to interpret_console if you want a different key.
DISCONNECT_WARNING = 20  # The number of failed reads before a disconnect warning is issued.

consecutive_empty_reads = 0  # Used to detect when the device is disconnected

ConsoleFlag = str  # Just a typehint, a ConsoleFlag is a string with one of the values below.
CONSOLE_DONT_PRINT = "_silent"
CONSOLE_EXIT = "_exit"
CONSOLE_ERROR = "_error"
NO_VELOCITY = -1  # For when a note is released/unpressed.
NOTE_LETTERS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# These don't include flats, flats should be converted to their respective just intonation sharps.


class MidiCompoundNote:
    """3 values.
    is_pressed: bool - True if the note is being pressed,
    note: str - the note name (eg "C4"),
    velocity: int - the velocity of the note. (-1 if the note is unpressed).
    """
    def __init__(self, is_pressed: bool, note: str, velocity: int):
        self.is_pressed = is_pressed
        self.note = note
        self.velocity = velocity

    def __str__(self):
        return f"{self.note} v={self.velocity}"
    
    def __repr__(self):
        return f'MidiCompoundNote({self.is_pressed}, "{self.note}", {self.velocity})'

    def __getitem__(self, index: int):
        return (self.is_pressed, self.note, self.velocity)[index]
    
    def __iter__(self):
        return (self.is_pressed, self.note, self.velocity)

def midi_to_note(midi_note: int) -> str:
    """Convert a MIDI note number to a note name.
    
    Arguments:
        midi_note: The MIDI note number to convert.
    
    Returns:
        The note name (eg of the form "C4").
    """
    octave_int = midi_note // 12
    note_int = midi_note % 12
    return f"{NOTE_LETTERS[note_int]}{octave_int-1}"


def note_to_midi(note: str) -> int:
    """Convert a note name to a MIDI note number.
    
    Arguments:
        note: The note name to convert.
    
    Returns:
        The MIDI note number.
    """
    is_natural = note[1] != "#"  # Whether the note is a x. natural or x. sharp.

    note_letter = note[0] if is_natural else note[0:2]
    note_octave = int(note[1:]) if is_natural else int(note[2:])
    note_index = NOTE_LETTERS.index(note_letter)
    return (note_octave + 1) * 12 + note_index


def interpret_console(line: str, keyboard_exit_key: Optional[str] = None) -> Union[MidiCompoundNote, ConsoleFlag]:
    """Turn console output into a list of arguments.
    
    Arguments:
        line: The console line to interpret.
    
    Returns:
        A list of arguments.
        If the line is not a valid command, returns a string with a console flagging message.

    Raises:
        RuntimeError: If the line does conform to the expected format.
    """
    global consecutive_empty_reads

    if keyboard_exit_key is None:
        keyboard_exit_key = KEYBOARD_EXIT

    if line == b"":
        consecutive_empty_reads += 1

        if consecutive_empty_reads > DISCONNECT_WARNING:
            print("The device is not responding. Please check the device is connected.")
            return CONSOLE_ERROR
        return CONSOLE_DONT_PRINT
    else:
        consecutive_empty_reads = 0

    line = line.decode('utf-8').strip().lower()  # Clean up the line a bit

    if "unsubscribed" in line:
        return CONSOLE_EXIT

    # Avoid outputting repeated, unuseful lines.
    if "clock" in line  or  "active sensing" in line:
        return CONSOLE_DONT_PRINT

    # Separate peices of information are separated by a ", " or a sequences of spaces length 2 or more.
    args = line.replace("  ", ", ").split(", ")
    # .split will leave lots of "", "", ""..., and it also means gaps of odd length leave strings with a single space, so strip args, and remove empty strings.
    args = [arg.strip() for arg in args if arg != ""]

    if ":" not in args[0]:  # This filters out generic information messages (like: waiting for data. press ctrl+c to end.)
        return CONSOLE_DONT_PRINT
    
    del args[2]
    del args[0]

    if args[0] == "note on" and len(args) != 3  or  args[0] == "note off" and len(args) != 2  or  args[0] not in ("note on", "note off"):
        raise RuntimeError(f"Unrecognised argument form from '{line}' -> {args}")

    # If this errors, it's probably because the way aseqdump -p "Device" outputs the data has since changed.
    midi_note = int(args[1][5:])

    is_pressed = args[0] == "note on"
    note = midi_to_note(midi_note)
    velocity = int(args[2][9:]) if is_pressed else NO_VELOCITY

    if note == keyboard_exit_key:
        return CONSOLE_EXIT

    return MidiCompoundNote(is_pressed, note, velocity)


_run = False

def stop_midi_stream():
    global _run
    _run = False


def midi_stream(func: Callable[[MidiCompoundNote], None], stop_func: Callable[[], None], device_name: Optional[str] = None) -> None:
    """Read a stream of data from the console, parse each line into a note data, and pass them to the given function.
    
    Arguments:
        func: The function to call with the parsed data.
        stop_func: This gets called when the user presses the keyboard exit key.
        device_name: The name of the device to read from.
    """
    global _run

    if device_name is None:
        device_name = DEVICE_NAME

    if _run:
        print("Tried to start stream when already running. Aborted.")
        return

    print("Start stream.")

    # BE VERY CAREFUL THAT DEVICE_NAME IS SAFE! Possible injection attacks!
    process = subprocess.Popen(f'aseqdump -p "{DEVICE_NAME}"', stdout=subprocess.PIPE, shell=True)
    _run = True

    with process.stdout as console:
        while _run:
            line = console.readline()  # This blocks until it receives a midi input.
            compound_note = interpret_console(line)

            if compound_note == CONSOLE_DONT_PRINT:
                continue
            if compound_note == CONSOLE_EXIT:
                print("Stream terminated by external device.")
                break
            if compound_note == CONSOLE_ERROR:
                print("Stream broken by device error.")
                break

            func(compound_note)

    if not _run:  # _run was set to False by stop_midi_stream() being called externally.
        print("Stream finished by program.")
    
    _run = False

    stop_func()
    

def test():
    print("Hello!")

    def test_func(compound_note: MidiCompoundNote) -> None:
        if compound_note.is_pressed:
            print(f"{compound_note.note}\t{compound_note.velocity}")
    
    def test_stop_func():
        print("--")

    midi_stream(test_func, test_stop_func)

    print("Goodbye!")


if __name__ == "__main__":
    test()
