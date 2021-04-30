"""
Create tk object
"""
# --------------------------------------------------------------------------------------------------------------------------------------

# Library
import tkinter as tk


# --------------------------------------------------------------------------------------------------------------------------------------

# Create buttons
def create_buttons(parent, location_x, location_y, backgroundcolor, name, cmdtrig):
    button = tk.Button(parent, bg=backgroundcolor, text=name, relief=tk.RAISED, borderwidth=2, command=cmdtrig)
    button.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)


# Create labels
def create_label(parent, location_x, location_y, name="NO-NAME-SET"):
    label = tk.Label(parent, text=name)
    label.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)


# Create labels
def create_textbox(parent, location_x, location_y, value=''):
    textbox = tk.Entry(parent, bg="white", fg="black", borderwidth=2)
    textbox.insert(tk.END, value)
    textbox.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)

    return textbox


# Create labels
def create_textbox_custom(parent, location_x, location_y, width, value=''):
    textbox = tk.Entry(parent, width=width, bg="white", fg="black", borderwidth=2)
    textbox.insert(tk.END, value)
    textbox.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)

    return textbox


# Create scale bar
def create_scale(parent, location_x, location_y, start, end, resolution, typeorient, default, barlen, color,
                 cmdtrig):
    scale = tk.Scale(parent, resolution=resolution, from_=start, to=end, orient=typeorient, length=barlen, fg=color,
                     command=cmdtrig)
    scale.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, padx=20, pady=20)
    scale.set(default)


# Create drop box
def create_drop(parent, location_x, location_y, variable, options):
    drop_button = tk.OptionMenu(parent, variable, *options)
    drop_button.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, padx=20, pady=20)


# create EQ scale
def create_EQ_scale(parent, location_x, location_y, start, end, resolution, orient, default, barlen, color,
                    channel_number, cmdtrig):
    scale = tk.Scale(parent, resolution=resolution, from_=start, to=end, orient=orient, length=barlen, fg=color,
                     command=lambda func: cmdtrig(channel_number, func))
    scale.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, padx=20, pady=4)
    scale.set(default)


def create_arrow(parent, location_x, location_y):
    arr = tk.Label(parent, text="\N{RIGHTWARDS BLACK ARROW}")
    arr.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=20, padx=10)
