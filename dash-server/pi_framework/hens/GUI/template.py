from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
from tkinter import filedialog
from os import path
from tkinter import Menu

window = Tk()

window.title("Welcome to LikeGeeks app")
window.geometry('350x200')

tab_control = Notebook(window)
tab1 = Frame(tab_control)
tab2 = Frame(tab_control)
tab_control.add(tab1, text='First')
tab_control.add(tab2, text='Second')


combo = Combobox(tab1)
combo['values'] = (1, 2, 3, 4, 5, "Text")
combo.current(1)  # set the selected item
combo.grid(column=0, row=0)

lbl = Label(tab1, text="Hello")
lbl.grid(column=1, row=0)

txt = Entry(tab1, width=10, state='disabled')
txt.grid(column=2, row=0)
txt.focus()


def clicked():
    messagebox.showwarning('Message title', str(selected.get()))
    print(selected.get())

btn = Button(tab1, text="Click Me", command=clicked)
btn.grid(column=3, row=0)

chk_state = BooleanVar()
chk_state.set(True)  # set check state
chk = Checkbutton(tab1, text='Choose', var=chk_state)
chk.grid(column=0, row=1)


selected = IntVar()

rad1 = Radiobutton(tab1, text='First', value=1, variable=selected)
rad2 = Radiobutton(tab1, text='Second', value=2, variable=selected)
rad3 = Radiobutton(tab1, text='Third', value=3, variable=selected)

rad1.grid(column=0, row=2)
rad2.grid(column=0, row=3)
rad3.grid(column=0, row=4)

spin = Spinbox(tab1, from_=0, to=100, width=5)
spin.grid(column=0, row=5)

spin2 = Spinbox(tab1, values=(3, 8, 11), width=5)
spin2.grid(column=0, row=6)

# file = filedialog.askopenfilename()
# file = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("all files", "*.*")))
# dir = filedialog.askdirectory()
# file = filedialog.askopenfilename(initialdir= path.dirname(__file__))


menu = Menu(window)
new_item = Menu(menu, tearoff=0)
new_item.add_command(label='New')
new_item.add_separator()
new_item.add_command(label='Edit')
menu.add_cascade(label='File', menu=new_item)
window.config(menu=menu)

tab_control.pack(expand=1, fill='both')

window.mainloop()
