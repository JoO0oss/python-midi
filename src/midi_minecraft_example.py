import pynput
import midi_reader
import threading
import time

mouse = pynput.mouse.Controller()
keyboard = pynput.keyboard.Controller()
Button = pynput.mouse.Button
Key = pynput.keyboard.Key

# THESE ARE THE KEYBOARD NOTES TO DO ACTIONS IN MINECRAFT.
# Change these to whatever you want.
note_to_action = {
    "C#3": "forwards",
    "C3": "backwards",
    "B2": "left",
    "D3": "right",
    "E3": "jump",
    "G2": "sneak",
    "A2": "sprint",

    "G3": "inventory",
    "A3": "perspective",
    "B3": "throw_item",
    "D2": "escape",

    "B4": "mine",
    "D5": "place",
    "G4": "pick",

    "C#5": "mouse_move_up",
    "C5": "mouse_move_down",
    "A4": "mouse_move_left",
    "E5": "mouse_move_right",
    "A#4": "scroll_up",
    "D#5": "scroll_down",
    "C#6": "sensitivty_0",
    "D#6": "sensitivty_1",
    "F#6": "sensitivty_2",
    "G#6": "sensitivty_3",
    "A#6": "sensitivty_4",

    "G5": "hotbar_1",
    "A5": "hotbar_2",
    "B5": "hotbar_3",
    "C6": "hotbar_4",
    "D6": "hotbar_5",
    "E6": "hotbar_6",
    "F6": "hotbar_7",
    "G6": "hotbar_8",
    "A6": "hotbar_9",

    "C2": "debug",
    "C7": "leave",
}

action_to_note = {value: key for key, value in note_to_action.items()}
mouse_movement_notes = [action_to_note[mousemov] for mousemov in ("mouse_move_up", "mouse_move_down", "mouse_move_left", "mouse_move_right")]
# mouse_movements is a list of keyboard notes that are used to move the mouse.

# Below 55 is SOFT, between 55 and 100 is MEDIUM, and above 100 is LOUD.
SLOW_VELOCITY = 55
FAST_VELOCITY = 100

# These are more programmer friendly dynamics.
SOFT = 1
MEDIUM = 2
LOUD = 3

# How often to poll for notes being queued up.
TICK_RATE = 100

MOUSE_SPEEDS = [3, 8, 16, 25, 40]
MIN_MOUSE_SPEED = 2
MAX_MOUSE_SPEED = 100

KEY_WARN = True  # Warn the user if they unpress a note that was not already pressed.
mouse_speed = MOUSE_SPEEDS[2]  # Use the middle speed as default.
run = True
show_keys = False
note_press_event: list = []
pressed_notes: dict = {}  # Note_name (str) : weight (int)

# THESE THE ARE FUNCTIONS TO RUN THAT DO STUFF IN MINECRAFT.
# I use a slightly weird set of controls, so you will want to change these.
# Make sure to modify unact as well.
class act:
    def forwards(note):
        if note.weight >= LOUD:  # There is also a specific sprint button.
            act.sprint(note)
        keyboard.press("w")

    def backwards(note):
        if note.weight >= LOUD:  # There is also a specific sneak button.
            act.sneak(note)
        keyboard.press("s")

    def left(note):
        keyboard.press("a")
    def right(note):
        keyboard.press("d")
    def jump(note):
        keyboard.press(Key.space)
    def sprint(note):
        keyboard.press(Key.ctrl)
    def sneak(note):
        keyboard.press(Key.shift)
    
    def inventory(note):
        keyboard.press("r")
    def perspective(note):
        keyboard.press("t")  # Most will use Key.f5 here.
    def throw_item(note):
        keyboard.press("y")    
    def escape(note):
        keyboard.press(Key.esc)

    def mine(note):
        mouse.press(Button.left)
    def place(note):
        mouse.press(Button.right)
    def pick(note):
        mouse.press(Button.middle)

    def mouse_move_up(note):
        pass
    def mouse_move_down(note):
        pass
    def mouse_move_left(note):
        pass
    def mouse_move_right(note):
        pass
    def scroll_up(note):
        mouse.scroll(0, 1)
    def scroll_down(note):
        mouse.scroll(0, -1)
    def sensitivty_0(note):
        global mouse_speed
        mouse_speed = MOUSE_SPEEDS[0]
    def sensitivty_1(note):
        global mouse_speed
        mouse_speed = MOUSE_SPEEDS[1]
    def sensitivty_2(note):
        global mouse_speed
        mouse_speed = MOUSE_SPEEDS[2]
    def sensitivty_3(note):
        global mouse_speed
        mouse_speed = MOUSE_SPEEDS[3]
    def sensitivty_4(note):
        global mouse_speed
        mouse_speed = MOUSE_SPEEDS[4]

    def hotbar_1(note):
        keyboard.press("1")
    def hotbar_2(note):
        keyboard.press("2")
    def hotbar_3(note):
        keyboard.press("3")
    def hotbar_4(note):
        keyboard.press("4")
    def hotbar_5(note):
        keyboard.press("5")
    def hotbar_6(note):
        keyboard.press("6")
    def hotbar_7(note):
        keyboard.press("7")
    def hotbar_8(note):
        keyboard.press("8")
    def hotbar_9(note):
        keyboard.press("9")

    def debug(note):
        # You want this to toggle on press, not act while held.
        global show_keys
        if show_keys:
            print("Stopped debugging keys.")
        else:
            print("Started debugging keys.")
        show_keys = not show_keys

    def no_action(note):
        # A default action for pressing a note that is not bound to a function.
        pass

class unact:
    def forwards(note):
        keyboard.release("w")
        if "sprint" not in pressed_notes:
            # Also make sure to stop sprinting, but only if the user isn't manually sprinting.
            unact.sprint(note)
    
    def backwards(note):
        keyboard.release("s")
        if "sneak" not in pressed_notes:
            # Also make sure to stop sneaking, but only if the user isn't manually sneaking.
            unact.sneak(note)
    
    def left(note):
        keyboard.release("a")
    def right(note):
        keyboard.release("d")
    def jump(note):
        keyboard.release(Key.space)
    def sprint(note):
        keyboard.release(Key.ctrl)
    def sneak(note):
        keyboard.release(Key.shift)

    def inventory(note):
        keyboard.release("r")
    def perspective(note):
        keyboard.release("t")
    def throw_item(note):
        keyboard.release("y")
    def escape(note):
        keyboard.release(Key.esc)

    def mine(note):
        mouse.release(Button.left)
    def place(note):
        mouse.release(Button.right)
    def pick(note):
        mouse.release(Button.middle)
    
    def mouse_move_up(note):
        pass
    def mouse_move_down(note):
        pass
    def mouse_move_left(note):
        pass
    def mouse_move_right(note):
        pass
    def scroll_up(note):
        pass
    def scroll_down(note):
        pass
    def sensitivty_0(note):
        pass
    def sensitivty_1(note):
        pass
    def sensitivty_2(note):
        pass
    def sensitivty_3(note):
        pass
    def sensitivty_4(note):
        pass

    def hotbar_1(note):
        keyboard.release("1")
    def hotbar_2(note):
        keyboard.release("2")
    def hotbar_3(note):
        keyboard.release("3")
    def hotbar_4(note):
        keyboard.release("4")
    def hotbar_5(note):
        keyboard.release("5")
    def hotbar_6(note):
        keyboard.release("6")
    def hotbar_7(note):
        keyboard.release("7")
    def hotbar_8(note):
        keyboard.release("8")
    def hotbar_9(note):
        keyboard.release("9")

    def debug(note):
        # Since it's a toggle, releasing the key does nothing.
        pass

    def no_action(note):
        pass


def schedule_note(cnote: midi_reader.MidiCompoundNote):
    # Use this to avoid having multiple threads trying to press keyboard keys simultaneously.
    note_press_event.append(cnote)

    if show_keys and cnote.is_pressed:
        # Output each key-down event if the user wants to debug.
        print(f"{cnote.note}\t({cnote.velocity})")


def stop_func():
    global run
    run = False

def convert_vel(vel: int) -> str:
    if vel <= SLOW_VELOCITY:
        return SOFT
    elif vel < FAST_VELOCITY:
        return MEDIUM
    else:
        return LOUD

def press_note(cnote: midi_reader.MidiCompoundNote):
    global pressed_notes

    weight = convert_vel(cnote.velocity)
    cnote.weight = weight
    # This is bad Python, but put the weight value into this instance of the note class.

    if cnote.note in note_to_action:
        action_name = note_to_action[cnote.note]
    else:
        action_name = "no_action"

    if cnote.is_pressed:
        pressed_notes[cnote.note] = weight

        act.__dict__[action_name](cnote)

    else:
        unact.__dict__[action_name](cnote)

        try:
            del pressed_notes[cnote.note]
        except KeyError:
            if KEY_WARN:
                print(f"Warning: {cnote.note} was not in pressed_notes dictionary to remove.")

def loop():
    global run
    global mouse_speed
    
    while run:
        while note_press_event:
            cnote = note_press_event.pop(0)
            press_note(cnote)

        mouse_delta_x = 0
        mouse_delta_y = 0

        for cur_note in pressed_notes:
            if cur_note in mouse_movement_notes:
                weight = pressed_notes[cur_note]
                if cur_note == action_to_note["mouse_move_up"]:
                    mouse_delta_y -= mouse_speed * weight  # Remember that greater y means further down the screen.

                if cur_note == action_to_note["mouse_move_down"]:
                    mouse_delta_y += mouse_speed * weight

                if cur_note == action_to_note["mouse_move_left"]:
                    mouse_delta_x -= mouse_speed * weight

                if cur_note == action_to_note["mouse_move_right"]:
                    mouse_delta_x += mouse_speed * weight

        mouse.move(mouse_delta_x, mouse_delta_y)

        time.sleep(1 / TICK_RATE)

def main():
    print("Hello!")

    # Put the midi reading into a thread, so loop() can continuously try to move the mouse.
    midi_thread = threading.Thread(target=midi_reader.midi_stream, args=(schedule_note, stop_func))
    midi_thread.start()
    try:
        loop()
    finally:
        midi_reader.stop_midi_stream()

    midi_thread.join()

    print("Goodbye!")


if __name__ == "__main__":
    main()
