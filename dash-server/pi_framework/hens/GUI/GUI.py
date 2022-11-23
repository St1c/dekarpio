from tkinter import *
#from tkinter import messagebox
from tkinter.ttk import *
from tkinter import filedialog
#from os import path
#from tkinter import Menu

#import importlib
import pi_framework.hens.Models.HENS
import pi_framework.hens.Plots.plots

#import Auxiliary.checks

#import numpy as np
#import pandas as pd

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

class App():
    def __init__(self):
        # define class variables
        self.demand = None
        self.path = 'not loaded'
        self.streams_hot = 'not loaded'
        self.streams_cold = 'not loaded'
        self.intervals = 'not loaded'

        self.streamdata = 'not loaded'

        self.tmp = None    # variable to temporarily store information

        self.CCs_number = 1
        self.GCCs_number = 1
        self.mGCCs_number = 1

        self.model = None


        borderwidth = 2

        root = Tk()
        root.title('AIT retroHENS')

        canvas = Canvas(root, width=800, height=600)
        frame = Frame(canvas)

        hsb = Scrollbar(root, orient=VERTICAL, command=canvas.yview)
        hsb.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=hsb.set)
        canvas.pack(side="left", fill="both", expand=True)

        canvas.create_window((4, 4), window=frame, anchor="nw", tags="frame")

        def frame_configure(event):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", frame_configure)

        self.tab_control = Notebook(frame)
        #self.tab_control.grid(row=0, column=0, sticky="ew")

        tab_names = ['input', 'targets', 'hen', 'analysis']
        tab_attr = ['frames', 'labels', 'buttons', 'entries', 'canvases', 'toolbars']

        self.tabs = {}
        for i in tab_names:
            self.tabs[i] = {}
            for j in tab_attr:
                self.tabs[i][j] = {}

        self.load_input_frame('input')
        self.load_targets_frame('targets')
        self.load_HEN_frame('hen')
        self.load_analysis_frame('analysis')

        self.tab_control.pack(expand=0, fill=X)

        root.mainloop()


    def load_input_frame(self, tab_name):
        ########################################################################################################################
        # INPUT FRAME
        frames = self.tabs[tab_name]['frames']
        buttons = self.tabs[tab_name]['buttons']
        labels = self.tabs[tab_name]['labels']
        entries = self.tabs[tab_name]['entries']

        if 'main' in frames.keys():
            print('HELLO BELLO!!!')
            frames['main'].destroy()
        else:
            frames['base'] = Frame(self.tab_control)
            self.tab_control.add(frames['base'], text='Input')

        frames['main'] = Frame(frames['base'])
        frames['main'].pack(fill=X, expand=0)


        #----------------------------------------------------------------------------------------------------------------------#
        # update
        buttons['update'] = Button(frames['main'], text="Update fields", command=self.onclick_update)
        buttons['update'].grid(column=0, row=0, pady=10, columnspan=2)

        #----------------------------------------------------------------------------------------------------------------------#
        # Stream data
        def stream_data_frame(self):
            frames['stream data'] = LabelFrame(frames['main'], text="Stream data")
            frames['stream data'].grid(row=1, column=0)

            # loading stream data
            labels['path'] = self.ParamLabel(frames['stream data'], 'Path:', self.path, 1, 0)
            labels['hot streams'] = self.ParamLabel(frames['stream data'], 'Hot streams:', self.streams_hot, 2, 0)
            labels['cold streams'] = self.ParamLabel(frames['stream data'], 'Cold streams:', self.streams_cold, 3, 0)
            labels['intervals'] = self.ParamLabel(frames['stream data'], 'Intervals:', self.intervals, 4, 0)

            frames['stream table'] = LabelFrame(frames['stream data'], text="Stream Table")
            frames['stream table'].grid(column=0, row=5, pady=10, columnspan=2)

            labels['stream table'] = Label(frames['stream table'], font=('Courier', 10), text=str(self.streamdata))
            labels['stream table'].grid(column=0, row=0)

            buttons['load stream table'] = Button(frames['stream table'], text="Load stream data...", command=onclick_update_streamdata)
            buttons['load stream table'].grid(column=0, row=6, pady=10, columnspan=2)

        def onclick_update_streamdata():
            self.onclick_load_streamdata()

            frames['stream data'].pack_forget()
            frames['stream data'].destroy()

            stream_data_frame(self)

        stream_data_frame(self)

        #----------------------------------------------------------------------------------------------------------------------#
        # Utilities
        frames['utilities'] = LabelFrame(frames['main'], text="Utilities")
        frames['utilities'].grid(row=2, column=0)

        # description
        labels['utilities description'] = Label(frames['utilities'], text="List of all used Utilities")
        labels['utilities description'].grid(column=0, row=0)

        frames['utilities used'] = LabelFrame(frames['utilities'], text="Selected Utilities")
        frames['utilities used'].grid(column=0, row=1)

        #self.load_utilities()
        self.show_utilities(frames['utilities used'], 0, 0)

        buttons['add utility'] = Button(frames['utilities'], text="Add Utility", command=self.add_utility)
        buttons['add utility'].grid(column=0, row=2)

        #----------------------------------------------------------------------------------------------------------------------#
        # Retrofit
        frames['retrofit'] = LabelFrame(frames['main'], text="Retrofit")
        frames['retrofit'].grid(row=3, column=0)

        # description
        labels['retrofit description'] = Label(frames['retrofit'], text="Stream data and the corresponding content will be displayed here")
        labels['retrofit description'].grid(column=0, row=0)

        #----------------------------------------------------------------------------------------------------------------------#
        # general settings
        frames['settings'] = LabelFrame(frames['main'], text="Settings")
        frames['settings'].grid(row=4, column=0)

        # description
        if self.demand is None:
            labels['settings description'] = Label(frames['settings'], text="Stream data and the corresponding content will be displayed here")
            labels['settings description'].pack()
        else:
            for i in self.demand.settings.keys():
                frames['settings '+i] = LabelFrame(frames['settings'], text=str(i))
                frames['settings '+i].pack()
                count=0
                for j in self.demand.settings[i].keys():
                    entries[i + ' ' + j] = self.InputFields(frames['settings '+i], j, str(self.demand.settings[i][j]), count, 0)
                    count += 1

            def onclick_update_settings():
                for i in self.demand.settings.keys():
                    for j in self.demand.settings[i].keys():
                        self.demand.settings[i][j] = float(entries[i + ' ' + j].get())
                print(self.demand.settings)


            buttons['update settings'] = Button(frames['settings'], text='update settings', command=onclick_update_settings)
            buttons['update settings'].pack()

    def load_targets_frame(self, tab_name):
        ########################################################################################################################
        # TARGETS FRAME

        frames = self.tabs[tab_name]['frames']
        buttons = self.tabs[tab_name]['buttons']
        labels = self.tabs[tab_name]['labels']
        entries = self.tabs[tab_name]['entries']
        canvases = self.tabs[tab_name]['canvases']
        toolbars = self.tabs[tab_name]['toolbars']

        if 'main' in frames.keys():
            print('HELLO BELLO!!!')
            frames['main'].destroy()
        else:
            frames['base'] = Frame(self.tab_control)
            self.tab_control.add(frames['base'], text='Targets')

        frames['main'] = Frame(frames['base'])
        frames['main'].pack(fill=X, expand=0)

        #----------------------------------------------------------------------------------------------------------------------#
        # update
        buttons['update'] = Button(frames['main'], text="Update fields", command=self.onclick_update)
        buttons['update'].grid(column=0, row=0, pady=10, columnspan=2)
        # ----------------------------------------------------------------------------------------------------------------------#
        # Summary
        frames['summary'] = LabelFrame(frames['main'], text="Summary")
        frames['summary'].grid(row=1, column=0)
        if self.demand is not None:
            self.ParamLabel(frames['summary'], 'Heat Recovery (kW): ', str(self.demand.targets['Heat Recovery'][0][:]),
                            0, 0)
            self.ParamLabel(frames['summary'], 'Hot Utility (kW): ', str(self.demand.targets['UH'][0][:]), 1, 0)
            self.ParamLabel(frames['summary'], 'Cold Utility (kW): ', str(self.demand.targets['UC'][0][:]), 2, 0)

            self.ParamLabel(frames['summary'], '', '', 3, 0)

            self.ParamLabel(frames['summary'], 'Heat Recovery (kWh, norm): ', str(sum(self.demand.targets['Heat Recovery'][0][:] * self.demand.durations)), 4, 0)
            self.ParamLabel(frames['summary'], 'Hot Utility (kWh, norm): ', str(sum(self.demand.targets['UH'][0][:] * self.demand.durations)), 5, 0)
            self.ParamLabel(frames['summary'], 'Cold Utility (kWh, norm): ', str(sum(self.demand.targets['UC'][0][:] * self.demand.durations)), 6, 0)

            self.ParamLabel(frames['summary'], '', '', 7, 0)

            self.ParamLabel(frames['summary'], 'Heat Recovery (kWh, norm, TAM): ', str(sum(self.demand.targets_TAM['Heat Recovery'][0][:] * self.demand.durations)), 8, 0)
            self.ParamLabel(frames['summary'], 'Hot Utility (kWh, norm, TAM): ', str(sum(self.demand.targets_TAM['UH'][0][:] * self.demand.durations)), 9, 0)
            self.ParamLabel(frames['summary'], 'Cold Utility (kWh, norm, TAM): ', str(sum(self.demand.targets_TAM['UC'][0][:] * self.demand.durations)), 10, 0)

        curve_names = ['CCs', 'GCCs', 'mGCCs']
        #----------------------------------------------------------------------------------------------------------------------#
        # CCs

        def show_CCs(row, curve_name):
            frames[curve_name + ' main'] = LabelFrame(frames['main'], text=curve_name)
            frames[curve_name + ' main'].grid(row=row, column=0)

            frames[curve_name + ' targets'] = Frame(frames[curve_name + ' main'])
            frames[curve_name + ' targets'].grid(row=0, column=0)
            frames[curve_name + ' targets TAM'] = Frame(frames[curve_name + ' main'])
            frames[curve_name + ' targets TAM'].grid(row=0, column=1)

            # plots
            if self.demand is not None:
                figure = Plots.plots.plot_CCs(self.demand, curve_name, 0, 0, self.CCs_number)
                canvases[curve_name + ' canvas'], toolbars[curve_name + ' toolbar'] = self.draw_figure(frames[curve_name + ' targets'], figure)

                figure = Plots.plots.plot_CCs(self.demand, curve_name, 1, 0, 0)
                canvases[curve_name + ' canvas TAM'] = self.draw_figure(frames[curve_name + ' targets TAM'], figure)

                frames[curve_name + ' button frame'] = Frame(frames[curve_name + ' main'])
                frames[curve_name + ' button frame'].grid(row=1, column=0)

                Label(frames[curve_name + ' button frame'], text='Interval: ').grid(row=0, column=0)
                labels[curve_name + ' interval'] = Label(frames[curve_name + ' button frame'], text=str(self.CCs_number))
                labels[curve_name + ' interval'].grid(row=0, column=1, padx=5)

                Button(frames[curve_name + ' button frame'], text='prev interval', command=lambda: self.change_figure(curve_name, -1)).grid(row=0,
                                                                                                               column=2)
                Button(frames[curve_name + ' button frame'], text='next interval', command=lambda: self.change_figure(curve_name, 1)).grid(row=0,
                                                                                                              column=3)
        row = 2
        for i in curve_names:
            show_CCs(row, i)
            row += 1

    def load_HEN_frame(self, tab_name):
        ########################################################################################################################
        # HEN FRAME

        frames = self.tabs[tab_name]['frames']
        buttons = self.tabs[tab_name]['buttons']
        labels = self.tabs[tab_name]['labels']
        entries = self.tabs[tab_name]['entries']
        canvases = self.tabs[tab_name]['canvases']
        toolbars = self.tabs[tab_name]['toolbars']

        if 'main' in frames.keys():
            print('HELLO BELLO!!!')
            frames['main'].destroy()
        else:
            frames['base'] = Frame(self.tab_control)
            self.tab_control.add(frames['base'], text='HEN')

        frames['main'] = Frame(frames['base'])
        frames['main'].pack(fill=X, expand=0)

        #----------------------------------------------------------------------------------------------------------------------#
        # update
        buttons['update'] = Button(frames['main'], text="Update fields", command=self.onclick_update)
        buttons['update'].grid(column=0, row=0, pady=10, columnspan=2)

        # ----------------------------------------------------------------------------------------------------------------------#
        # Optimize
        def show_HEN(row):
                frames['HEN opt'] = LabelFrame(frames['main'], text='optimal HEN')
                frames['HEN opt'].grid(row=row, column=0)

                figure = Plots.plots.plot_HEN(self.demand)
                canvases['HEN opt'], toolbars['HEN opt'] = self.draw_figure(frames['HEN opt'], figure)

        def onclick_optimize():
            self.demand.set_equations()
            self.model = self.demand.opt_model
            show_HEN(2)

        buttons['optimize'] = Button(frames['main'], text="run solver", command=onclick_optimize)
        buttons['optimize'].grid(column=0, row=1, pady=10, columnspan=2)

        #----------------------------------------------------------------------------------------------------------------------#
        # Optimal HEN
        if self.model is not None:
            show_HEN(2)

        #----------------------------------------------------------------------------------------------------------------------#
        # original HEN

        # hen_opt = LabelFrame(hen, text="Optimal HEN")
        # hen_opt.pack(fill="both", expand="yes")
        #
        # # description
        # hen_opt_desc = Label(hen_opt, text="In this frame, the optimized HEN prior will be displayed")
        # hen_opt_desc.pack()

    def load_analysis_frame(self, tab_name):
        ########################################################################################################################
        # ANALYSIS FRAME
        frames = self.tabs[tab_name]['frames']
        buttons = self.tabs[tab_name]['buttons']
        labels = self.tabs[tab_name]['labels']
        entries = self.tabs[tab_name]['entries']
        canvases = self.tabs[tab_name]['canvases']
        toolbars = self.tabs[tab_name]['toolbars']

        if 'main' in frames.keys():
            print('HELLO BELLO!!!')
            frames['main'].destroy()
        else:
            frames['base'] = Frame(self.tab_control)
            self.tab_control.add(frames['base'], text='Analysis')

        frames['main'] = Frame(frames['base'])
        frames['main'].pack(fill=X, expand=0)

        #----------------------------------------------------------------------------------------------------------------------#
        # update
        buttons['update'] = Button(frames['main'], text="Update fields", command=self.onclick_update)
        buttons['update'].pack()

        #----------------------------------------------------------------------------------------------------------------------#
        # cost analysis
        frames['cost analysis'] = LabelFrame(frames['main'], text="Costs")
        frames['cost analysis'].pack(fill=X, expand=0)

        if self.model is not None:
            figure = Plots.plots.plot_Costs(self.demand, self.model)
            canvases['cost analysis'], toolbars['cost analysis'] = self.draw_figure(frames['cost analysis'], figure)

        # cost analysis
        frames['heat recovery analysis'] = LabelFrame(frames['main'], text="Costs")
        frames['heat recovery analysis'].pack(fill=X, expand=0)

        if self.model is not None:
            figure = Plots.plots.plot_HR(self.demand, self.model)
            canvases['heat recovery analysis'], toolbars['heat recovery analysis'] = self.draw_figure(frames['heat recovery analysis'], figure)


    # Functions for all pages
    def onclick_update(self):
        print('update!')
        self.load_input_frame('input')
        self.load_targets_frame('targets')
        self.load_HEN_frame('hen')
        self.load_analysis_frame('analysis')

    def onclick_update_utilities(self):
        ref_frame = self.tabs['input']['frames']['utilities used']
        row = ref_frame.grid_info()['row']
        col = ref_frame.grid_info()['column']

        self.tabs['input']['frames']['utilities used'].grid_forget()
        self.tabs['input']['frames']['utilities used'].destroy()

        self.tabs['input']['frames']['utilities used'] = LabelFrame(master=self.tabs['input']['frames']['utilities'], text="Selected Utilities")
        self.tabs['input']['frames']['utilities used'].grid(row=row, column=col)

        self.show_utilities(self.tabs['input']['frames']['utilities used'], 0, 0)

    # Functions for page: INPUT
    def onclick_load_streamdata(self):
        self.load_streamdata()
        self.load_utilities()   # TODO: will likely be removed

    def load_streamdata(self):
        self.path = filedialog.askopenfilename()
        self.demand = pi_framework.hens.Models.HENS.HENS(self.path)

        self.streams_hot = self.demand.streams_hot
        self.streams_cold = self.demand.streams_cold

        self.intervals = self.demand.intervals

        self.streamdata = self.demand.streamdata

    def load_utilities(self):
        if self.demand == None:
            print('No stream data loaded!')
        else:
            # Hot utilities
            self.demand.conversion_units['UH'] = self.demand.conversion_units['UH'].append({
                'Name': 'Steam HP',
                'Tin': 500,             # Inlet Temperature °C
                'Tout': 450,            # Outlet Temperature °C
                'dTmin': 5,             # minimum temperature difference °C
                'h': 0.2,               # Heat transfer coefficient kW/m²K
                'costs': 252/24,           # specific energy costs per year €/kWh/y
            }, ignore_index=True)
            self.demand.conversion_units['UH'] = self.demand.conversion_units['UH'].append({
                'Name': 'Steam MP',
                'Tin': 400,             # Inlet Temperature °C
                'Tout': 350,            # Outlet Temperature °C
                'dTmin': 5,             # minimum temperature difference °C
                'h': 0.2,               # Heat transfer coefficient kW/m²K
                'costs': 0.04*1*52*7,  # specific energy costs per year €/kWh/y # FIXME: ist für testzwecke auf einen sehr hohen wert gestellt
            }, ignore_index=True)

            # Cold utilities
            self.demand.conversion_units['UC'] = self.demand.conversion_units['UC'].append({
                'Name': 'Cooling Water',
                'Tin': 0,               # Inlet Temperature °C
                'Tout': 10,             # Outlet Temperature °C
                'dTmin': 5,             # minimum temperature difference °C
                'h': 0.2,               # Heat transfer coefficient kW/m²K
                'costs': 0.005*1*52*7, # specific energy costs per year €/kWh/y # FIXME: ist für testzwecke auf einen sehr hohen wert gestellt
            }, ignore_index=True)

            # Hot internal utilities
            self.demand.conversion_units['CU'] = self.demand.conversion_units['CU'].append({
                'Name': 'Compression Heat Pump',
                'Tmax': 80,            # Maximum Condenser Temperature °C
                'Tmin': 20,             # Minimum Evaporator Temperature °C
                'dTmin': 5,             # minimum temperature difference °C
                'dT lift max': 50,      # maximum Temperature lift °C
                'dT lift min': 20,      # minimum temperature difference °C
                'h': 0.2,               # Heat transfer coefficient kW/m²K
                'phase change': 1,      # determines whether a phase change takes place in the HEX
                'costs': 0.1*1*52*7,   # specific electricity costs per year €/kWh/y #fixme: muss angepasst werden, nur für testzwecke so niedrig
            }, ignore_index=True)
            self.demand.conversion_units['CU'] = self.demand.conversion_units['CU'].append({
                'Name': 'Two-Tank Storage',
                'Tmax': 100,            # Maximum Condenser Temperature °C
                'Tmin': 30,             # Minimum Evaporator Temperature °C
                'dTmin': 5,             # minimum temperature difference °C
                'dT lift min': 30,      # minimum temperature difference °C
                'h': 0.2,               # Heat transfer coefficient kW/m²K
                'phase change': 0,      # determines whether a phase change takes place in the HEX
                'costs var': 0.3*24,    # specific storage costs €/kg #fixme: muss angepasst werden, nur für testzwecke so niedrig
                'costs fix': 25000,     # step fixed storage costs € #fixme: muss angepasst werden, nur für testzwecke so niedrig
                'annualization': 5,    # years for annualization
            }, ignore_index=True)

    def show_utilities(self, parent, row, col):
        if self.demand == None:
            print('No stream data loaded!')
        else:
            utilities = self.demand.conversion_units.keys()
            for i in utilities:
                for j in range(len(self.demand.conversion_units[i])):
                    string1 = i + ': '
                    string2 = self.demand.conversion_units[i].loc[j:j]

                    self.ParamLabel(parent, string1, string2, row, col)

                    button = Button(parent, text='Delete', command=lambda i_=i, j_=j: self.del_utilities(i_, j_))
                    button.grid(row=row, column=col+2)


                    row += 1

    def del_utilities(self, utilitytype, row):
        self.demand.conversion_units[utilitytype] = self.demand.conversion_units[utilitytype].drop(row, axis=0).reset_index(drop=True)
        print(self.demand.conversion_units)
        self.onclick_update_utilities()

    def add_utility(self):
        def open_utility_window():
            self.add_utility_window = Toplevel()
            self.add_utility_window.title('Add Utility')
            self.add_utility_frame = Frame(self.add_utility_window)
            self.add_utility_frame.pack()

            def on_closing():
                self.add_utility_window.destroy()
                self.add_utility_window = None

            self.add_utility_window.protocol("WM_DELETE_WINDOW", on_closing)



            self.add_utility_combo_label = Label(self.add_utility_frame, text='Utility Type: ')
            self.add_utility_combo_label.grid(row=0, column=0)

            self.add_utility_combo = Combobox(self.add_utility_frame)
            self.add_utility_combo['values'] = (list(self.demand.conversion_units.keys()))
            self.add_utility_combo.current(0)  # set the selected item
            self.add_utility_combo.grid(row=0, column=1)

            self.add_utility_entry_frame = Frame(self.add_utility_frame, width=500, height=300)
            self.add_utility_entry_frame.grid(row=1, column=0, pady=10)


            def EntryFieldsUpdate(event):
                self.tmp = []  # used to store information on entry fields

                #if hasattr(self, 'entry_frame'):
                self.add_utility_entry_frame.destroy()
                self.add_utility_entry_frame = Frame(self.add_utility_frame, width=500, height=300)
                self.add_utility_entry_frame.grid(row=1, column=0, pady=10)

                fields = list(self.demand.conversion_units[self.add_utility_combo.get()].keys())

                if 'index' in fields:
                    fields.remove('index')

                if 'level_0' in fields:
                    fields.remove('level_0')

                row = 1
                for i in fields:
                    self.tmp.append(App.InputFields(self.add_utility_entry_frame, i, '', row, 0))

                    row += 1


            EntryFieldsUpdate(None)     # initialize entryfields

            self.add_utility_combo.bind("<<ComboboxSelected>>", EntryFieldsUpdate)


            def add_utility_button():

                keys = list(self.demand.conversion_units[self.add_utility_combo.get()].keys())
                input_fields = self.tmp

                new_utility = {}

                error = 0

                for i in range(len(keys)):
                    if keys[i] == 'Name':
                        try:
                            new_utility[keys[i]] = str(input_fields[i].get())
                        except:
                            print('Name must be a string!\n all other fields must be float/int')
                            error += 1
                            break

                        if (self.add_utility_combo.get() == 'CU') and ((str(input_fields[i].get()) != 'Compression Heat Pump') and (str(input_fields[i].get()) != 'Two-Tank Storage')):
                            print('Name for CU must be:')
                            print('Compression Heat Pump')
                            print('or')
                            print('Two-Tank Storage')
                            error += 1
                            break
                    else:
                        try:
                            new_utility[keys[i]] = float(input_fields[i].get())
                        except:
                            print('Name must be a string!\n all other fields must be float/int')
                            error += 1
                            break


                if error == 0:
                    self.demand.conversion_units[self.add_utility_combo.get()] = self.demand.conversion_units[self.add_utility_combo.get()].append(new_utility, ignore_index=True)
                    self.onclick_update_utilities()

            self.add_utility_add_button = Button(self.add_utility_frame, text='add utility', command=add_utility_button)
            self.add_utility_add_button.grid(row=2, column=0, columnspan=2, pady=10)

        if self.demand is None:
            print('No streamdata loaded!')
        else:
            if hasattr(self, 'add_utility_window'):
                if self.add_utility_window is not None:
                    print('Add Utility Window already open!')
                else:
                    open_utility_window()
            else:
                open_utility_window()



    # Functions for page: TARGETS
    def draw_figure(self, master, figure):
        canvas = FigureCanvasTkAgg(figure, master=master)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, master)
        toolbar.update()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        return canvas, toolbar

    def replace_figure(self, master, figure, canvas, toolbar, curve_name):

        canvas.get_tk_widget().destroy()
        toolbar.destroy()
        canvas, toolbar = self.draw_figure(master, figure)
        self.tabs['targets']['canvases'][curve_name + ' canvas'] = canvas
        self.tabs['targets']['toolbars'][curve_name + ' toolbar'] = toolbar
        return canvas

    def change_figure(self, curve_name, change):
        number = getattr(self, curve_name + '_number')
        number += change

        if number > max(self.intervals):
            number = 1
        elif number <= 0:
            number = max(self.intervals)

        self.tabs['targets']['labels'][curve_name + ' interval']['text'] = str(number)

        setattr(self, curve_name + '_number', number)

        master = self.tabs['targets']['frames'][curve_name + ' targets']
        canvas = self.tabs['targets']['canvases'][curve_name + ' canvas']
        toolbar = self.tabs['targets']['toolbars'][curve_name + ' toolbar']

        figure = Plots.plots.plot_CCs(self.demand, curve_name, 0, 0, number)
        self.replace_figure(master, figure, canvas, toolbar, curve_name)




    @staticmethod
    def set_text(textfield, string):
        textfield['text'] = string

    class ParamLabel:
        def __init__(self, parent, string1, string2, row, col):
            self.parent = parent
            self.string1 = string1
            self.string2 = string2

            self.Label1 = Label(self.parent, text=string1, font=('Courier', 10))
            self.Label1.grid(column=col, row=row, sticky="E")
            self.Label2 = Label(self.parent, text=string2, font=('Courier', 10))
            self.Label2.grid(column=col+1, row=row, sticky="W")

        def set_string(self, stringNr, string):
            if (stringNr == 0) and (type(string) == str):
                App.set_text(self.Label1, string)
            elif (stringNr == 1) and (type(string) == str):
                App.set_text(self.Label2, string)
            else:
                print('Error! Wrong stringnumber or no string supplied')

    class InputFields:
        def __init__(self, parent, string1, string2, row, col):
            self.parent = parent
            self.string1 = string1
            self.string2 = string2

            self.Label1 = Label(self.parent, text=string1, font=('Courier', 10))
            self.Label1.grid(column=col, row=row, sticky="E")
            self.Label2 = Entry(self.parent, font=('Courier', 10))
            self.Label2.insert(END, string2)
            self.Label2.grid(column=col+1, row=row, sticky="W")

        def get(self):
            value = self.Label2.get()
            return value

        def set_string(self, stringNr, string):
            if (stringNr == 0) and (type(string) == str):
                App.set_text(self.Label1, string)
            elif (stringNr == 1) and (type(string) == str):
                App.set_text(self.Label2, string)
            else:
                print('Error! Wrong stringnumber or no string supplied')

if __name__ == '__main__':
    PI_tool = App()
