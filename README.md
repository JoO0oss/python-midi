# python-midi
Primitive midi interface intended only for simple projects.

<br>

## Simple use
A few basic things:
- notes are supplied as `MidiCompoundNote`s, it has 3 attributes
- `is_pressed` (Boolean), whether the note in this event is now pressed or now unpressed after the event
- `note` (string), what pitch on the keyboard it occupies.
- `velocity` (integer), how "quickly" the note was pressed, ranges from 0 (soft) to 127 (loud).

Write a function that can do things with a MidiCompoundNote as it comes in, eg

```py
def my_func(compound_note: MidiCompoundNote):
    if compound_note.is_pressed:
        print(compound_note.note)
```

And you can also have it execute code when you press the top piano key (C7, by default) to stop the program, eg

```py
def my_stop_func():
    print("Program exiting.")
```

These are then used with the `midi_stream()` function:

```py
if __name__ == "__main__":
    midi_stream(my_func, my_stop_func)
```

## Extra constants

You can change these to suit your hardware, for example, `KEYBOARD_EXIT` can be changed to `"C8"` if your keyboard finishes an octave higher than mine.

- `DEVICE_NAME = "Digital Keyboard"` **for the love of God do not set this to anything other than another constant.** `DEVICE_NAME` is just put into a shell command to run `aseqdump -p "Digital Keyboard"`, from `subprocess.Popen(f'aseqdump -p "{DEVICE_NAME}"', stdout=subprocess.PIPE, shell=True)`
- `KEYBOARD_EXIT = "C7"` This is just whichever note you want to be pressed to kill the midi reader. Can be any note. If it's a note you cannot press, or it's not in a valid form (eg "" and "C_5" are not valid notes), then it will just not trigger, so you can use that to disable the exit key.
- `DISCONNECT_WARNING = 20` this doesn't really change anything, it just means if you get nothing back for a little bit for any reason (be that hardware issues or unforeseen software issues), then there's a tiny grace period where it can get back on track again.

## Other features

calling `stop_midi_stream()` will end the program from within the code without having to press the exit key.

## Example

```py
import midi_reader

midi_reader.KEYBOARD_EXIT = "C2"  # The bottom note on my piano

def my_func(compound_note: MidiCompoundNote):
    if compound_note.is_pressed:
        print(compound_note.note)

    if compound_note.velocity > 100:
        # If any note is pressed particularly heavily, stop the program.
        midi_reader.stop_midi_stream()

my_stop_func = lambda: None

midi_reader.midi_stream(my_func, my_stop_func)
```
