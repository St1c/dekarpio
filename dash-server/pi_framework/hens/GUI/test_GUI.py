import tkinter as tk

def populate(frame):
    '''Put in some fake data'''
    for row in range(100):
        tk.Label(frame, text="%s" % row, width=3, borderwidth="1",
                 relief="solid").grid(row=row, column=0)
        t="this is the second column for row %s" %row
        tk.Label(frame, text=t).grid(row=row, column=1)

def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))

root = tk.Tk()
canvas = tk.Canvas(root, borderwidth=0, background="#ffffff")
frame = tk.Frame(canvas, background="#ffffff")
vsb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=vsb.set)

vsb.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=False)
canvas.create_window((4,4), window=frame)

frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

populate(frame)

root.mainloop()
#
#
# import tkinter as tk
# import tkinter.ttk as ttk
#
#
# class Example(tk.Tk):
#     def __init__(self):
#         tk.Tk.__init__(self)
#         self.canvas = tk.Canvas(self, borderwidth=0)
#         self.frame = tk.Frame(self.canvas)
#
#         self.vsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
#         self.vsb.grid(row=1, column=0, sticky="nsew")
#
#         self.canvas.configure(xscrollcommand=self.vsb.set)
#         self.canvas.grid(row=0, column=0, sticky="nsew")
#         self.canvas.create_window((3,2), window=self.frame, anchor="nw", tags="self.frame")
#
#         self.frame.bind("<Configure>", self.frame_configure)
#         self.populate()
#
#     def populate(self):
#         tabs = ttk.Notebook(self.frame, width=100, height=100)
#         for tab in range(50):
#             tabs.add(ttk.Frame(tabs), text=" Tab {}  ".format(tab))
#         tabs.grid(row=0, column=0, sticky="ew")
#
#
#     def frame_configure(self, event):
#         self.canvas.configure(scrollregion=self.canvas.bbox("all"))
#
# if __name__ == "__main__":
#     app = Example()
#     app.mainloop()