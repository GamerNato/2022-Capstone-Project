
import mysql.connector
import csv
import openpyxl as opx
import xlrd
import numpy as np
import pandas as pd
import xlsxwriter as xls
import tkinter as tk
import sys
import tkinter.filedialog as fd
import tkcalendar as tkc


##############


from xlrd.xldate import xldate_from_datetime_tuple
from xlrd.xldate import xldate_as_datetime
from xlrd.xldate import xldate_as_tuple
from tkinter import messagebox
from tkinter import ttk
from tkinter import messagebox
from functools import partial


##############


def execute(global_context,query): # function for connecting to the database, running a query and returning the results
    mydb = mysql.connector.connect( # connect
        host=global_context.hostip.get(),
        user=global_context.username.get(),
        password=global_context.password.get(),
        database="demand"
    )
    mycursor = mydb.cursor() # create cursor
    print(query)
    mycursor.execute(query) # run query
    result = [x for x in mycursor]
    mydb.commit()
    return result # return result


def region_combo(global_context,query_region_id,value): # utility function
    global_context.scenario_var.set(value) # set variable to value
    findscenario(global_context,query_region_id,value) # populate next list


def scenario_combo(global_context,query_scenario_id,value): # utility function
    global_context.component_var.set(value) # set variable to value
    findcomponent(global_context,query_scenario_id,value) # populate next list


def find_region(global_context,extra): # populate component dropdown from database
    print(extra)
    global_context.region_var.set(extra)
    
    query_region_id = []
    if extra == '*': # select all regions
        for e,x in enumerate(execute(global_context,f"SELECT region.region_id FROM region")):
            print(x[0])
            query_region_id.append(x[0])
    else: # select only one region
        for e,x in enumerate(execute(global_context,f"SELECT region.region_id FROM region WHERE region.name = '{extra}'")):
            print(x[0])
            query_region_id.append(x[0])
    
    options = ['*']
    for y in query_region_id: # for each region select all components
        for e,x in enumerate(execute(global_context,f"SELECT scenario.name FROM scenario WHERE scenario.region_id = {y} GROUP BY scenario.name")):
            print(x[0])
            options.append(x[0])
    
    global_context.scenario_menu.children['menu'].delete(0,'end') # clear current options
    global_context.scenario = []
    
    for x in options: # add component to dropdown
        print("scenario options",options)
        global_context.scenario_menu.children['menu'].add_command(label=x,command=partial(region_combo,global_context,query_region_id,x))
        global_context.scenario.append(x)
    

def findscenario(global_context,query_region_id,extra):
    print(extra)
    
    query_scenario_id = []
    if extra == '*': # select all regions
        for y in query_region_id:
            for e,x in enumerate(execute(global_context,f"SELECT scenario.scenario_id FROM scenario WHERE scenario.region_id = {y}")):
                print(x[0])
                query_scenario_id.append(x[0])
    else: # select only one region
        for y in query_region_id:
            for e,x in enumerate(execute(global_context,f"SELECT scenario.scenario_id FROM scenario WHERE scenario.name = '{extra}' AND scenario.region_id = {y}")):
                print(x[0])
                query_scenario_id.append(x[0])
    
    options = ['*']
    for y in query_scenario_id: # for each region select all components
        for e,x in enumerate(execute(global_context,f"SELECT component.name FROM component WHERE component.scenario_id = {y} GROUP BY component.name")):
            print(x[0])
            options.append(x[0])
    
    global_context.component_menu.children['menu'].delete(0,'end') # clear current options
    global_context.component = []
    
    print(query_scenario_id)
    for x in options: # add component to dropdown
        print("component options",options)
        global_context.component_menu.children['menu'].add_command(label=x,command=partial(scenario_combo,global_context,query_scenario_id,x))
        global_context.component.append(x)


def sortkey(e): # sort years ascending
    if e == '*':
        return -1
    else:
        return int(e)


def findcomponent(global_context,query_scenario_id,extra): # populate year dropdown from database
    print('here')
    print(extra)
    
    print("scenario_id",query_scenario_id)
    query_component_id = []
    print("component_ids")
    
    if extra == '*': # select all components
        for y in query_scenario_id: # for each region
            for e,x in enumerate(execute(global_context,f"SELECT component.component_id FROM component WHERE component.scenario_id = {y}")):
                print(x[0])
                query_component_id.append(x[0])
    else: # select only one component
        for y in query_scenario_id: # for each region
            for e,x in enumerate(execute(global_context,f"SELECT component.component_id FROM component WHERE component.name like '{extra}' AND component.scenario_id = {y}")):
                print(x[0])
                query_component_id.append(x[0])
    
    options = ['*']
    print("years")
    for y in query_component_id: # for each component
        for e,x in enumerate(execute(global_context,f"SELECT year.candidate_year FROM year WHERE year.component_id = {y}")):
            print(x[0])
            if x[0] not in options: # keep years unique
                options.append(x[0])
    
    global_context.year_menu.children['menu'].delete(0,'end') # clear current options
    global_context.year = []
    options.sort(key=sortkey)
    for x in options: # add year to dropdown
        global_context.year_menu.children['menu'].add_command(label=x,command=lambda o=x:global_context.year_var.set(o))
        global_context.year.append(x)
    
    global_context.range_menu.children['menu'].delete(0,'end') # clear current options
    for x in options[1:]: # add year to dropdown
        global_context.range_menu.children['menu'].add_command(label=x,command=lambda o=x:global_context.range_var.set(o))
    print('end')
    

def add_entry(global_context): # add entry to list box
    if global_context.region_var.get() != "region" and global_context.scenario_var.get() != "scenario" and global_context.component_var.get() != "component" and global_context.year_var.get() != "year": # check there's no default values
        if global_context.year_var.get() == '*': # every year
            global_context.list_box.insert(0,f"('{global_context.region_var.get()}',{bool(int(global_context.subregion_check.get()))},'{global_context.scenario_var.get()}','{global_context.component_var.get()}','*')")
        elif global_context.range_check.get() and global_context.range_var.get().isdigit(): # range of years
            if int(global_context.year_var.get()) < int(global_context.range_var.get())+1: # work both ways
                for x in range(int(global_context.year_var.get()),int(global_context.range_var.get())+1): # from year to range limit
                    global_context.list_box.insert(0,f"('{global_context.region_var.get()}',{bool(int(global_context.subregion_check.get()))},'{global_context.scenario_var.get()}','{global_context.component_var.get()}',{x})")
            else:
                for x in range(int(global_context.range_var.get()),int(global_context.year_var.get())+1): # from range limit to year
                    global_context.list_box.insert(0,f"('{global_context.region_var.get()}',{bool(int(global_context.subregion_check.get()))},'{global_context.scenario_var.get()}','{global_context.component_var.get()}',{x})")
        else: # single year
            global_context.list_box.insert(0,f"('{global_context.region_var.get()}',{bool(int(global_context.subregion_check.get()))},'{global_context.scenario_var.get()}','{global_context.component_var.get()}',{global_context.year_var.get()})")
    else: # values are missing
        messagebox.showerror('Query Error', 'Error: Missing values.')


def construct_query(global_context): # query from each selection
    items = []
    for x in global_context.list_box.get(0,'end'): # fetch items
        items.append(eval(x))
    print(items)
    data = []
    columns = []
    for element in items[::-1]: # work in FIFO order
        query_region_id = []
        query_region_name = []
        if element[0] == '*': # select all regions
            for x in execute(global_context,f"SELECT region_id,name FROM region"):
                query_region_id.append(x[0])
                query_region_name.append(x[1])
        else: # select from only the given region
            for x in execute(global_context,f"SELECT region_id,name FROM region WHERE region.name = '{element[0]}'"):
                query_region_id.append(x[0])
                query_region_name.append(x[1])
                break
            if element[1]: # include subregions of that region
                for x in execute(global_context,f"SELECT region_id,name FROM region WHERE subregion_of = {query_region_id[-1]}"):
                    query_region_id.append(x[0])
                    query_region_name.append(x[1])
        query_scenario_id = []
        query_scenario_name = []
        if element[2] == '*': # select from all scenarios
            for y,z in zip(query_region_id,query_region_name): # for each selected region
                for x in execute(global_context,f"SELECT scenario_id,name FROM scenario WHERE scenario.region_id = {y}"):
                    query_scenario_id.append(x[0])
                    query_scenario_name.append((z,x[1]))
        else: # select from only the given component type
            for y,z in zip(query_region_id,query_region_name): # for each selected region
                for x in execute(global_context,f"SELECT scenario_id,name FROM scenario WHERE scenario.region_id = {y} and scenario.name = '{element[2]}'"):
                    query_scenario_id.append(x[0])
                    query_scenario_name.append((z,x[1]))
                    break
        query_component_id = []
        query_component_name = []
        if element[3] == '*': # select from all components
            for y,z in zip(query_scenario_id,query_scenario_name): # for each selected scenario
                for x in execute(global_context,f"SELECT component_id,name FROM component WHERE component.scenario_id = {y}"):
                    query_component_id.append(x[0])
                    query_component_name.append(z+(x[1],))
        else: # select from only the given component type
            for y,z in zip(query_scenario_id,query_scenario_name): # for each selected scenario
                for x in execute(global_context,f"SELECT component_id,name FROM component WHERE component.scenario_id = {y} and component.name = '{element[3]}'"):
                    query_component_id.append(x[0])
                    query_component_name.append(z+(x[1],))
                    break
        if element[4] == '*': # select all from year
            for y,z in zip(query_component_id,query_component_name): # for each selected component
                for x in execute(global_context,f"SELECT candidate_year,start,end,data FROM year WHERE year.component_id = {y}"):
                    print(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
                    data.append(eval(x[3]))
                    start=x[1]
                    end=x[2]
                    columns.append(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
        else: # select only that year
            for y,z in zip(query_component_id,query_component_name): # for each selected component
                for x in execute(global_context,f"SELECT candidate_year,start,end,data FROM year WHERE year.component_id = {y} and year.candidate_year = {element[4]}"):
                    print(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
                    data.append(eval(x[3]))
                    start=x[1]
                    end=x[2]
                    columns.append(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
                    break
    print("query end")
    print(columns)
    if len(columns):
        display_Data(global_context,convert(global_context,data,columns,start,end))
    print("display end")


def swap(global_context): # toggle range dropdown
    print('global_context.range_check',global_context.range_check.get())
    if global_context.range_check.get(): # if checked then normal
        global_context.range_menu.configure(state='normal')
    else: # else disabled
        global_context.range_menu.configure(state='disabled')


def subswap(global_context,menu): # toggle subregion dropdown
    print('subcheck',global_context.load_subregion_check.get())
    if global_context.load_subregion_check.get(): # if checked then normal
        menu.configure(state='normal')
    else: # else disabled
        menu.configure(state='disabled')


def convert(global_context,data,columns,start,end): # function converts raw data list into pandas dataframe as desired output format
    df = pd.DataFrame()
    summary = ['datetime','min','p90','median','average','p10','max']
    for x in summary:
        df[x] = [0 for y in range(len(data[0]))]
    for e,x in enumerate(columns):
        df[x] = data[e]
    m = [[],[],[],[],[],[],[]] # list of empty lists representing columns-to-be

    for e,x in enumerate(df.iloc[:, 7:].values): # filter out usable numbers from other data like strings
        row = []
        for y in x:
            try:
                row.append(float(y)) # try to include as float, otherwise skip
            except:
                pass
        e+=1
        datetuple = xldate_as_tuple(start+(e/48),0) # turn exceldatetime int into tuple
        m[0].append(f"{datetuple[2]:02d}\\{datetuple[1]:02d}\\{datetuple[0]:02d} {datetuple[3]:02d}:{datetuple[4]:02d}:{datetuple[5]:02d}") # format datetime string
        if len(row): # if any numbers on that row are usable calculate data
            m[1].append(min(row))
            m[2].append(np.percentile(row, 10))
            m[3].append(np.percentile(row, 50))
            m[4].append(sum(row)/len(row))
            m[5].append(np.percentile(row, 90))
            m[6].append(max(row))
        else: # otherwise just put 0
            m[1].append(0)
            m[2].append(0)
            m[3].append(0)
            m[4].append(0)
            m[5].append(0)
            m[6].append(0)
    for x,y in zip(summary,m): # zip columns into dataframe
        df[x] = y
    # return dataframe in requested datetime
    return df.iloc[int((xldate_from_datetime_tuple(global_context.settings['start'], 0)-start)*48):int((xldate_from_datetime_tuple(global_context.settings['end'], 0)-start)*48)]


def display_Data(global_context,data):
    #get column names from database
    cols = tuple(data.columns)
    print(cols)
    
    display_window = tk.Toplevel(global_context) # create display window
    display_window.geometry("1500x600")
    display_window.title("Display Data")
    
    display_window.columnconfigure(0, weight=1)
    display_window.columnconfigure(1, weight=1)
    display_window.columnconfigure(2, weight=1)
    display_window.columnconfigure(3, weight=0)
    display_window.rowconfigure(0, weight=0)
    display_window.rowconfigure(1, weight=1)
    display_window.rowconfigure(2, weight=0)
    
    # output buttons
    excelOutBut = tk.Button(display_window,text='output excel',command=partial(output_Excel,global_context,data))
    excelOutBut.grid(column=1, row=0, sticky=tk.W)
    csvOutBut = tk.Button(display_window,text='output csv',command=partial(output_CSV,global_context,data))
    csvOutBut.grid(column=1, row=0)
    txtOutBut = tk.Button(display_window,text='output txt',command=partial(output_TXT,global_context,data))
    txtOutBut.grid(column=1, row=0, sticky=tk.E)
    
    tree = ttk.Treeview(display_window, columns=cols, show="headings")
    #create column labels for the display box
    for c in cols:
        tree.heading(c,text=c)
        tree.column(c, minwidth=0, width=100)

    #Insert the rows into the display box
    for row in data.values:
        tree.insert('',tk.END,values=list(row))

    tree.grid(column=0, row=1, sticky=tk.NSEW, columnspan=3)
    
    #Add a scroll bars that can be used to scroll for the display box
    scrollbarV = tk.Scrollbar(display_window,orient=tk.VERTICAL,command=tree.yview)
    scrollbarH = tk.Scrollbar(display_window,orient=tk.HORIZONTAL,command=tree.xview)
    tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)
    
    scrollbarV.grid(column=3, row=1, sticky=tk.NS) # vertical scrollbar
    scrollbarH.grid(column=0, row=2, sticky=tk.EW, columnspan=3) # horizontal scrollbar
    

#Print the data to an excel document.
def output_Excel(global_context,data):
    # get output filename
    out_window = tk.Toplevel(global_context)
    out_entry = tk.Text(out_window,width=10,height=1)
    out_entry.pack()
    out_button = tk.Button(out_window,text='confirm',command=partial(var_set,global_context,global_context.output,out_entry))
    out_window.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,out_window,global_context.output,global_context.output.get()))
    out_button.pack()
    out_button.wait_variable(global_context.output) # wait for input
    out_window.destroy()
    
    workbook = xls.Workbook(f"{global_context.output.get()}.xlsx") # create output file
    worksheet = workbook.add_worksheet()
    
    for c, column in enumerate(data.columns): # write column headings
        worksheet.write(0,c,column)
    for r, row in enumerate(data.values): # write actual data
        r+=1
        for c, item in enumerate(row):
            worksheet.write(r,c,item)
    workbook.close()
    print('excel file has been written successfully!')
    messagebox.showinfo('Done!','excel file has been written successfully!')
    

#Print the data to a CSV file.
def output_CSV(global_context,data):
    # get output filename
    out_window = tk.Toplevel(global_context)
    out_entry = tk.Text(out_window,width=10,height=1)
    out_entry.pack()
    out_button = tk.Button(out_window,text='confirm',command=partial(var_set,global_context,global_context.output,out_entry))
    out_window.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,out_window,global_context.output,global_context.output.get()))
    out_button.pack()
    out_button.wait_variable(global_context.output) # wait for input
    out_window.destroy()
    
    file = open(f"{global_context.output.get()}.csv", 'w') # create output file
    for e,column in enumerate(data.columns): # write column headings
        if type(column) == str: # if value is a string add string classfifiers
            file.write(f"{global_context.settings['stringclass'].get()}{column}{global_context.settings['stringclass'].get()}")
        else:
            file.write(f"{column}")
        if e != len(data.columns)-1: # end of row doesn't need a separator
            file.write(f"{global_context.settings['separator'].get()}")
    file.write("\n")
    for row in data.values: # write actual data
        for e,value in enumerate(row):
            if type(value) == str: # if value is a string add string classfifiers
                file.write(f"{global_context.settings['stringclass'].get()}{value}{global_context.settings['stringclass'].get()}")
            else:
                file.write(f"{value}")
            if e != len(row)-1: # end of row doesn't need a separator
                file.write(f"{global_context.settings['separator'].get()}")
        file.write('\n')
    file.close()
    print('delimited file has been written successfully!')
    messagebox.showinfo('Done!','delimited file has been written successfully!')


#Print the data to a txt file.
def output_TXT(global_context,data):
    # get output filename
    out_window = tk.Toplevel(global_context)
    out_entry = tk.Text(out_window,width=10,height=1)
    out_entry.pack()
    out_button = tk.Button(out_window,text='confirm',command=partial(var_set,global_context,global_context.output,out_entry))
    out_window.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,out_window,global_context.output,global_context.output.get()))
    out_button.pack()
    out_button.wait_variable(global_context.output) # wait for input
    out_window.destroy()
    
    file = open(f"{global_context.output.get()}.txt", 'w') # create output file
    for e,column in enumerate(data.columns): # write column headings
        if type(column) == str: # if value is a string add string classfifiers
            file.write(f"{global_context.settings['stringclass'].get()}{column}{global_context.settings['stringclass'].get()}")
        else:
            file.write(f"{column}")
        if e != len(data.columns)-1: # end of row doesn't need a separator
            file.write(f"{global_context.settings['separator'].get()}")
    file.write("\n")
    for row in data.values: # write actual data
        for e,value in enumerate(row):
            if type(value) == str: # if value is a string add string classfifiers
                file.write(f"{global_context.settings['stringclass'].get()}{value}{global_context.settings['stringclass'].get()}")
            else:
                file.write(f"{value}")
            if e != len(row)-1: # end of row doesn't need a separator
                file.write(f"{global_context.settings['separator'].get()}")
        file.write('\n')
    file.close()
    print('delimited file has been written successfully!')
    messagebox.showinfo('Done!','delimited file has been written successfully!')


def submit_Date(global_context,window,args): # apply start and end date tuples to global settings

    # start datetime limit
    startDateTemp = list(map(int,str(args[4].get_date()).split('/')))
    global_context.settings['start'] = (
        startDateTemp[2], 
        startDateTemp[0],
        startDateTemp[1],
        int(args[0].get()),
        int(args[1].get()),
        0
    )

    # end datetime limit
    endDateTemp = list(map(int,str(args[5].get_date()).split('/')))
    global_context.settings['end'] = (
        endDateTemp[2], 
        endDateTemp[0],
        endDateTemp[1],
        int(args[2].get()),
        int(args[3].get()),
        0
    )
    print(global_context.settings['start'])
    print(global_context.settings['end'])
    show_date(global_context) # update settings display
    window.destroy() # destroy host window


def setDate(global_context): # set new datetime range

    # create window
    dateWindow = tk.Toplevel(global_context)
    startHourString = tk.StringVar()
    startMinuteString = tk.StringVar()
    endHourString = tk.StringVar()
    endMinuteString = tk.StringVar()
    dateWindow.geometry("550x270")

    #The two calendars for start and end range.
    calStart = tkc.Calendar(dateWindow, selectmode = "day", year = global_context.settings['start'][0], month = global_context.settings['start'][1], day = global_context.settings['start'][2])
    calStart.configure(date_pattern='mm/dd/yyyy')
    calStart.grid(row = 0, column = 0,padx = 10, columnspan = 2)
    calEnd = tkc.Calendar(dateWindow, selectmode = "day", year = global_context.settings['end'][0], month = global_context.settings['end'][1], day = global_context.settings['end'][2])
    calEnd.configure(date_pattern='mm/dd/yyyy')
    calEnd.grid(row = 0, column = 2 , columnspan = 2)
    print(calStart.get_date())
    
    #Spin box for selecting the hour/minue for the start of the range.
    hourLabelL = tk.Label(dateWindow, text="Hour")
    minuteLabelL = tk.Label(dateWindow, text="Minute")

    
    startHour = tk.Spinbox(dateWindow, from_ = 0, to = 23,wrap = True, textvariable=startHourString,state="readonly",width = 10)
    startHour.grid(row = 2,column=0)
    startHourString.set(str(global_context.settings['start'][3]))

    startMinute = tk.Spinbox(dateWindow, from_ = 0, to = 30,wrap = True, textvariable=startMinuteString, increment = 30,state="readonly",width = 10)
    startMinute.grid(row = 2,column=1)
    startMinuteString.set(str(global_context.settings['start'][4]))

    hourLabelL.grid(row=1,column =0)
    minuteLabelL.grid(row=1,column =1)

    #Spin box for selecting the hour/minue for the end of the range.

    hourLabelR = tk.Label(dateWindow, text="Hour")
    minuteLabelR = tk.Label(dateWindow, text="Minute")

    endHourString.set(str(global_context.settings['end'][3]))
    endHour = tk.Spinbox(dateWindow, from_ = 0, to = 23,wrap = True, textvariable=endHourString,state="readonly",width = 10)
    endHour.grid(row = 2,column=2)

    endMinuteString.set(str(global_context.settings['end'][4]))
    endMinute = tk.Spinbox(dateWindow, from_ = 0, to = 30,wrap = True, textvariable=endMinuteString, increment = 30,state="readonly",width = 10)
    endMinute.grid(row = 2,column=3)
    hourLabelR.grid(row=1,column = 2)
    minuteLabelR.grid(row=1,column =3)
    
    #Submit button
    args = (startHour,startMinute,endHour,endMinute,calStart,calEnd)
    submit_But = tk.Button(dateWindow,text = "Submit", command = partial(submit_Date,global_context,dateWindow,args))
    submit_But.grid(row = 3,column=0, columnspan=4)


def customwindow(global_context): # window for custom SQL interactions
    query_window = tk.Toplevel(global_context) # base gui class
    query_window.geometry("700x600")
    query_window.title('custom query') # set title
    
    query_window.columnconfigure(0, weight=1)
    query_window.rowconfigure(0, weight=1)
    query_window.rowconfigure(1, weight=1)

    box = tk.Text(query_window,height=32,width=75) # text box
    box.grid(column=0,row=0)
    tk.Button(query_window,text='confirm',command=partial(custom,global_context,box)).grid(column=0,row=1) # confirm button


def custom(global_context,box): # runs custom SQL commands as is **USE WITH CAUTION**
    query = str(box.get("1.0",'end-1c')) # get query
    print(query)

    f = open('custom_output.txt','w') # open output file
    f.write(query)
    f.write('\n')
    box.insert(tk.END,'\n')
    try:
        output = execute(global_context,query) # for each result
        for x in output: # for each result
            f.write('\n')
            f.write(str(x))
            box.insert(tk.END,'\n')
            box.insert(tk.END,str(x))
            print(x)
    except:
        for x in ['ERROR']: # write error indicator
            f.write('\n')
            f.write(str(x))
            box.insert(tk.END,'\n')
            box.insert(tk.END,str(x))
            print(x)
    f.close()


def on_soft_exit(context,var,default): # close child windows safely without giving input
    context.destroy()
    var.set(default)


def files(global_context): # create file dialog for selecting files to load into database
    filenames = fd.askopenfilenames(title='Select a File/Folder',filetypes=((("all files"),('*.*')),(('.csv files'),('*.csv'))))
    print(filenames) # print files selected
    for e,f in enumerate(filenames): # for each file
        title = f.split('/')[-1] # file name
        kind = title.split('.')[-1] # file type
        print(title,kind)
        # create/config file entry window
        file_entry_selecter = tk.Toplevel(global_context)
        file_entry_selecter.title(f'{e+1}/{len(filenames)}')
        file_entry_selecter.geometry("500x300")
        file_entry_selecter.columnconfigure(0, weight=1)
        file_entry_selecter.columnconfigure(1, weight=1)
        file_entry_selecter.rowconfigure(0, weight=1)
        file_entry_selecter.rowconfigure(1, weight=1)
        file_entry_selecter.rowconfigure(2, weight=1)
        file_entry_selecter.rowconfigure(3, weight=1)
        file_entry_selecter.rowconfigure(4, weight=1)
        file_entry_selecter.rowconfigure(5, weight=1)
        file_entry_selecter.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,file_entry_selecter,global_context.skipvar,0))
    
        tk.Label(file_entry_selecter,text=title).grid(column=0,row=0,columnspan=2)
        
        if len(global_context.region) > 1: # if theres options have a subregion selecter
            subregion_menu = tk.OptionMenu(file_entry_selecter,global_context.subregion_var,*global_context.region[1:]) # subregion dropdown
            subregion_menu.configure(width=20, state='disabled')
            subregion_menu.grid(column=1, row=1, sticky=tk.E)
            subregion_button = tk.Checkbutton(file_entry_selecter, text='subregion',variable=global_context.load_subregion_check, onvalue=1, offvalue=0,command=partial(subswap,global_context,subregion_menu))
            subregion_button.grid(column=1,row=1, sticky=tk.W)


        # entry boxes for each variable
        region_entry = tk.Entry(file_entry_selecter)
        file_entry_selecter.region_entry = region_entry
        region_entry.insert(tk.END,'region')
        region_entry.grid(column=0,row=1)

        scenario_entry = tk.Entry(file_entry_selecter)
        file_entry_selecter.scenario_entry = scenario_entry
        scenario_entry.insert(tk.END,'scenario')
        scenario_entry.grid(column=0,row=2)

        component_entry = tk.Entry(file_entry_selecter)
        file_entry_selecter.component_entry = component_entry
        component_entry.insert(tk.END,'component')
        component_entry.grid(column=0,row=3)

        year_entry = tk.Entry(file_entry_selecter)
        file_entry_selecter.year_entry = year_entry
        year_entry.insert(tk.END,'year')
        year_entry.grid(column=0,row=4)
        
        # submit or skip buttons

        tk.Button(file_entry_selecter,text='submit',command=partial(loader,global_context,file_entry_selecter,f,title,kind)).grid(column=1, row=2)
        
        skip_button = tk.Button(file_entry_selecter,text='skip',command=partial(on_soft_exit,file_entry_selecter,global_context.skipvar,0))
        skip_button.grid(column=1,row=4)
        skip_button.wait_variable(global_context.skipvar) # wait for submit or skip (or close)


def process(raw):
    processed = []
    for x in raw[1:]: # ignore column head
        for y in x[3:]: # ignore date
            processed.append(y) # add value to list
    return processed


def loader(global_context,context,f,title,kind): # actually parse file and insert data into the database
    print(f,title,kind)
    # make sure all inputs are valid
    if context.region_entry.get() == 'region' or context.scenario_entry.get() == 'scenario' or context.component_entry.get() == 'component' or context.year_entry.get() == 'year':
        messagebox.showerror('Query Error', 'Error: Missing values.')
        return
    if not context.year_entry.get().isdigit(): # check that the year is at least a digit
        messagebox.showerror('Not a year!', f'Error: The year box must be a positive integer.')
        return
    if kind[:-1] == 'xls': # if excel file
        try: # try reading the file
            wb = opx.load_workbook(f, read_only=True) # open workbook
            sheet = wb.active # get active sheet
            data = [x for x in sheet.values] # get data
            wb.close() # close file
        except: # if fail
            print("Error loading excel file!")
            messagebox.showerror('Error!', f'Error: The file you are trying to enter could not be loaded.\n')
            return
    else: # if delimited file
        check = True
        try: # try reading the file
            file = open(f,'r')
            data = [x for x in csv.reader(file, delimiter=global_context.settings['separator'].get(), quotechar=global_context.settings['stringclass'].get())]
            file.close()
        except: # if fail
            print("Error loading delimited file!")

            separator_handler = tk.Toplevel(context) # create additional window for getting new separator
            separator_handler.geometry("300x100")
            separator_handler.title("Error!")
            tk.Label(separator_handler,text=f"Are you sure '{global_context.settings['separator'].get()[0]}' is correct for this file?").pack()
            tk.Label(separator_handler,text='Please input alternative separator.').pack()
            box = tk.Text(separator_handler,width=10,height=1)
            box.pack() # add basic text input box
            enter = tk.Button(separator_handler,text='confirm',command=lambda: global_context.settings['separator'].set(box.get("1.0",'end-1c')[0]))
            enter.pack() # add _button for getting input from the text box
            separator_handler.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,separator_handler,global_context.settings['separator'],global_context.settings['separator'].get()))
            enter.wait_variable(global_context.settings['separator']) # wait for input
            separator_handler.destroy() # close input window

            try: # try again with new separator
                file = open(f,'r')
                data = [x for x in csv.reader(file, delimiter=global_context.settings['separator'].get(), quotechar=global_context.settings['stringclass'].get())]
                file.close()
                check = False
            except: # give up
                print("Error loading delimited file!")
                messagebox.showerror('Bad format!', f'Error: The file you are trying to enter could not be loaded.\n')
                return
        if not all([len(x)==51 for x in data]): # if data is the wrong shape
            print("Error loading delimited file!")
            if check:
                separator_handler = tk.Toplevel(context) # create additional window for getting new separator
                separator_handler.geometry("300x100")
                separator_handler.title("Error!")
                tk.Label(separator_handler,text=f"Are you sure '{global_context.settings['separator'].get()[0]}' is correct for this file?").pack()
                tk.Label(separator_handler,text='Please input alternative separator.').pack()
                box = tk.Text(separator_handler,width=10,height=1)
                box.pack() # add basic text input box
                enter = tk.Button(separator_handler,text='confirm',command=lambda: global_context.settings['separator'].set(box.get("1.0",'end-1c')[0]))
                enter.pack() # add _button for getting input from the text box
                separator_handler.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,separator_handler,global_context.settings['separator'],global_context.settings['separator'].get()))
                enter.wait_variable(global_context.settings['separator']) # wait for input
                separator_handler.destroy() # close input window

                try: # try again with new separator
                    file = open(f,'r')
                    data = [x for x in csv.reader(file, delimiter=global_context.settings['separator'].get(), quotechar=global_context.settings['stringclass'].get())]
                    file.close()
                    check = False
                except:
                    pass
            else:
                print("Error loading delimited file!")
                messagebox.showerror('Bad format!', f'Error: The file you are trying to enter could not be loaded.')
            return
    if not all([len(x)==51 for x in data]):
        print("Error loading file!")
        messagebox.showerror('Bad format!', f'Error: The file you are trying to enter is the wrong shape.')
        return

    # by this point the file has been loaded and is the correct shape
    print(context.region_entry.get(),global_context.subregion_var.get(),context.scenario_entry.get(),context.component_entry.get(),context.year_entry.get())
    # get start and end dates from tuples
    start = xldate_from_datetime_tuple((int(data[1][0]),int(data[1][1]),int(data[1][2]),0,0,0),0)
    end = xldate_from_datetime_tuple((int(data[-1][0]),int(data[-1][1]),int(data[-1][2]),0,0,0),0)+1

    try: # try to treat data as float but if not just load as-is
        data = [float(y) for y in [x for x in process(data)]]
    except:
        data = [y for y in [x for x in process(data)]]
        messagebox.showerror('Bad data!', f'Error: Some of this data cannot be treated as a number.\n It will not be included in any calculations done.')
    print(data[:100])
    
    # region
    
    # check existence
    region_dupe = execute(global_context,f"SELECT region_id FROM region WHERE name = '{context.region_entry.get()}'")
    if len(region_dupe): # if exists
        region_dupe = region_dupe[0][0]
    else: # else create new
        if global_context.load_subregion_check.get():
            meta = execute(global_context,f"SELECT region_id FROM region WHERE name = '{global_context.subregion_var.get()}'")[0][0]
            execute(global_context,f"INSERT INTO region (name,subregion_of) VALUES ('{context.region_entry.get()}',{meta})")
        else: # else regular region
            execute(global_context,f"INSERT INTO region (name) VALUES ('{context.region_entry.get()}')")
        region_dupe = execute(global_context,f"SELECT region_id FROM region WHERE name = '{context.region_entry.get()}'")[0][0]
        print(region_dupe)
        global_context.region_menu.children['menu'].add_command(label=context.region_entry.get(),command=partial(find_region,global_context,context.region_entry.get()))
    
    # scenario

    # check existence
    scenario_dupe = execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {region_dupe} AND scenario.name = '{context.scenario_entry.get()}'")
    if len(scenario_dupe): # if exists
        scenario_dupe = scenario_dupe[0][0]
    else: # else create new
        execute(global_context,f"INSERT INTO scenario (name,region_id) VALUES ('{context.scenario_entry.get()}',{region_dupe})")
        scenario_dupe = execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {region_dupe} AND scenario.name = '{context.scenario_entry.get()}'")[0][0]
        if global_context.region_var.get() == context.region_entry.get():
            global_context.scenario_menu.children['menu'].add_command(label=context.scenario_entry.get(),command=partial(findscenario,region_dupe,context.scenario_entry.get()))
    
    # component

    # check existence
    component_dupe = execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {scenario_dupe} AND component.name = '{context.component_entry.get()}'")
    if len(component_dupe): # if exists
        component_dupe = component_dupe[0][0]
    else: # else create new
        execute(global_context,f"INSERT INTO component (name,scenario_id) VALUES ('{context.component_entry.get()}',{scenario_dupe})")
        component_dupe = execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {scenario_dupe} AND component.name = '{context.component_entry.get()}'")[0][0]
        if global_context.scenario_var.get() == context.scenario_entry.get() and global_context.region_var.get() == context.region_entry.get():
            global_context.component_menu.children['menu'].add_command(label=context.component_entry.get(),command=partial(scenario_combo,global_context,scenario_dupe,context.component_entry.get()))
        
    # year
    
    # check existence
    year_dupe = execute(global_context,f"SELECT year_id FROM year WHERE year.component_id = {component_dupe} AND year.candidate_year = {context.year_entry.get()}")
    if len(year_dupe): # if exists
        print("DUPLICATE!")
        messagebox.showerror('Duplicate!', f'Error: The file you are trying to enter already exists!\nSee section 4 of the user manual for more info.')
    else: # else create new
        mydb = mysql.connector.connect( # connect
            host="localhost",
            user="setup",
            password="putes",
            database="demand"
        )
        mycursor = mydb.cursor() # create cursor
        mycursor.execute("INSERT INTO year (candidate_year,start,end,component_id,data) VALUES (%s,%s,%s,%s,%s)",(context.year_entry.get(),start,end,component_dupe,str(data)))
        mydb.commit()

        if global_context.component_var.get() == context.component_entry.get() and global_context.scenario_var.get() == context.scenario_entry.get() and global_context.region_var.get() == context.region_entry.get():
            global_context.year.append(context.year_entry.get())
            global_context.year_menu.children['menu'].add_command(label=context.year_entry.get(),command=lambda o=context.year_entry.get():global_context.year_var.set(o))
            global_context.range_menu.children['menu'].add_command(label=context.year_entry.get(),command=lambda o=context.year_entry.get():global_context.range_var.set(o))
        
    # done
    context.destroy() # close file window
    global_context.skipvar.set(0)
    print('done')


def show_date(global_context): # show current date range as text
    global_context.startlabel.configure(text=f"start\n{global_context.settings['start'][2]:02d}\\{global_context.settings['start'][1]:02d}\\{global_context.settings['start'][0]:02d} {global_context.settings['start'][3]:02d}:{global_context.settings['start'][4]:02d}:{global_context.settings['start'][5]:02d}")
    global_context.endlabel.configure(text=f"end\n{global_context.settings['end'][2]:02d}\\{global_context.settings['end'][1]:02d}\\{global_context.settings['end'][0]:02d} {global_context.settings['end'][3]:02d}:{global_context.settings['end'][4]:02d}:{global_context.settings['end'][5]:02d}")


def delete(global_context): # delete selected entry

    # double check that the user means to delete
    delete_window = tk.Toplevel(global_context)
    delete_window.title('DELETE')
    delete_window.columnconfigure(0, weight=1)
    delete_window.columnconfigure(1, weight=1)
    delete_window.rowconfigure(0, weight=1)
    delete_window.rowconfigure(1, weight=1)
    tk.Label(delete_window,text='Are you sure you want to delete these entries?').grid(column=0,row=0,columnspan=2)
    delete_check = tk.IntVar()
    delete_check.set(0)
    yes = tk.Button(delete_window,text='yes.',command=partial(delete_check.set,1))
    no = tk.Button(delete_window,text='NO!',command=partial(delete_check.set,-1))
    yes.grid(column=0,row=1)
    no.grid(column=1,row=1)
    delete_window.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,delete_window,delete_check,0))
    yes.wait_variable(delete_check)
    if delete_check.get() == 1:
        print('deleted')
        delete_window.destroy()
    else:
        print('not deleted')
        delete_window.destroy()
        return
    print('start deleting')
    items = []

    for x in global_context.list_box.get(0,'end'):
        items.append(eval(x))
    print(items)
    for element in items[::-1]: #
        query_region_id = []
        if element[0] == '*': # select all regions
            for x in execute(global_context,f"SELECT region_id FROM region"):
                query_region_id.append(x[0])
        else: # select from only the given region
            for x in execute(global_context,f"SELECT region_id FROM region WHERE region.name = '{element[0]}'"):
                query_region_id.append(x[0])
                break
            if element[1]: # include subregions of that region
                for x in execute(global_context,f"SELECT region_id FROM region WHERE subregion_of = {query_region_id[-1]}"):
                    query_region_id.append(x[0])
        query_scenario_id = []
        if element[2] == '*': # select from all scenarios
            for y in query_region_id: # for each selected region
                for x in execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {y}"):
                    query_scenario_id.append(x[0])
        else: # select from only the given component type
            for y in query_region_id: # for each selected region
                for x in execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {y} and scenario.name = '{element[2]}'"):
                    query_scenario_id.append(x[0])
                    break
        query_component_id = []
        if element[3] == '*': # select from all components
            for y in query_scenario_id: # for each selected scenario
                for x in execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {y}"):
                    query_component_id.append(x[0])
        else: # select from only the given component type
            for y in query_scenario_id: # for each selected scenario
                for x in execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {y} and component.name = '{element[3]}'"):
                    query_component_id.append(x[0])
                    break
        # query end
        if element[4] == '*': # select all from year
            for y in query_component_id: # for each selected component
                execute(global_context,f"DELETE FROM year WHERE year.component_id = {y}")
                print('component',element[3],'years deleted') # placeholder for display demo
        else: # select only that year
            for y in query_component_id: # for each selected component
                execute(global_context,f"DELETE FROM year WHERE year.component_id = {y} and year.candidate_year = {element[4]}")
                print(element[4],'deleted')

    # work back up the heirarchy and delete any now-empty entries
    for x in query_component_id:
        if not len(execute(global_context,f"SELECT year_id FROM year WHERE component_id = {x}")):
            execute(global_context,f"DELETE FROM component WHERE component_id = {x}")
    for x in query_scenario_id:
        if not len(execute(global_context,f"SELECT component_id FROM component WHERE scenario_id = {x}")):
            execute(global_context,f"DELETE FROM scenario WHERE scenario_id = {x}")
    for x in query_region_id:
        if not len(execute(global_context,f"SELECT scenario_id FROM scenario WHERE region_id = {x}")):
            execute(global_context,f"DELETE FROM region WHERE region_id = {x}")
    
    # reset GUI variables
    global_context.region_var.set('region')
    global_context.scenario_var.set('scenario')
    global_context.component_var.set('component')
    global_context.year_var.set('year')
    
    global_context.region_menu.children['menu'].delete(0,'end')
    
    global_context.region = ['*']
    
    global_context.region_menu.children['menu'].add_command(label='*',command=partial(find_region,global_context,'*'))
    for e,x in enumerate(execute(global_context,"SELECT region.name FROM region")): # populate region dropdown
        global_context.region_menu.children['menu'].add_command(label=x,command=partial(find_region,global_context,x[0]))
        global_context.region.append(x[0])
    
    global_context.scenario_menu.children['menu'].delete(0,'end')
    global_context.scenario_menu.children['menu'].add_command(label='*',command=partial(findscenario,'*'))
    global_context.component_menu.children['menu'].delete(0,'end')
    global_context.component_menu.children['menu'].add_command(label='*',command=partial(findcomponent,'*'))
    global_context.year_menu.children['menu'].delete(0,'end')
    global_context.year_menu.children['menu'].add_command(label='*',command=partial(global_context.year_var.set,'*'))
    
    print("delete end")
    messagebox.showinfo('Done!','Entries have been deleted succesfully!')


def sepb(global_context): # separator change window
    sepbwindow = tk.Toplevel(global_context)
    sepentry = tk.Text(sepbwindow,width=10,height=1)
    sepentry.insert(tk.END,global_context.settings['separator'].get())
    sepentry.pack()
    submit = tk.Button(sepbwindow,text='confirm',command=partial(sepbb,global_context,sepentry))
    sepbwindow.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,sepbwindow,global_context.settings['separator'],global_context.settings['separator'].get()))
    submit.pack()
    submit.wait_variable(global_context.settings['separator']) # wait for input
    sepbwindow.destroy()


def sepbb(global_context,entry): # separator changer function
    global_context.settings['separator'].set(entry.get("1.0",'end-1c'))
    global_context.sep_button.configure(text=f"separator = {global_context.settings['separator'].get()}")


def strb(global_context): # string classifier change window
    strbwindow = tk.Toplevel(global_context)
    strentry = tk.Text(strbwindow,width=10,height=1)
    strentry.insert(tk.END,global_context.settings['stringclass'].get())
    strentry.pack()
    submit = tk.Button(strbwindow,text='confirm',command=partial(strbb,global_context,strentry))
    strbwindow.protocol("WM_DELETE_WINDOW", partial(on_soft_exit,strbwindow,global_context.settings['stringclass'],global_context.settings['stringclass'].get()))
    submit.pack()
    submit.wait_variable(global_context.settings['stringclass']) # wait for input
    strbwindow.destroy()


def strbb(global_context,entry): # string classifier changer function
    global_context.settings['stringclass'].set(entry.get("1.0",'end-1c'))
    global_context.str_button.configure(text=f"string classifier = {global_context.settings['stringclass'].get()}")


def var_set(global_context,var,entry): # set variable to entry contents
    var.set(entry.get("1.0",'end-1c'))


def host_set(global_context): # set login info from GUI
    global_context.hostip.set(global_context.hostbox.get())
    global_context.username.set(global_context.userbox.get())
    global_context.password.set(global_context.passbox.get())


def on_exit(global_context): # exit root program cleanly
    print('quitting')
    global_context.hostip.set('')
    try:
        global_context.destroy()
        global_context.destroyed = False
    except:
        pass
    sys.exit()


##############


root = tk.Tk() # base gui class
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.columnconfigure(3, weight=1)
root.columnconfigure(4, weight=1)
root.columnconfigure(5, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)

root.protocol("WM_DELETE_WINDOW", partial(on_exit,root))

root.geometry("900x350")

# login window
root.hostget = tk.Toplevel(root)
root.hostget.title('login')
root.hostget.columnconfigure(0, weight=1)
root.hostget.columnconfigure(1, weight=1)
root.hostget.rowconfigure(0, weight=1)
root.hostget.rowconfigure(1, weight=1)
root.hostget.rowconfigure(2, weight=1)
root.hostget.rowconfigure(3, weight=1)
root.hostget.rowconfigure(4, weight=1)

root.hostget.geometry("250x200")

root.hostget.protocol("WM_DELETE_WINDOW", partial(on_exit,root))

root.hostip = tk.StringVar()
root.hostip.set('')
root.username = tk.StringVar()
root.username.set('')
root.password = tk.StringVar()
root.password.set('')

tk.Label(root.hostget,text='Please login.').grid(column=0,row=0,columnspan=2)
tk.Label(root.hostget,text='Hostname/IP:').grid(column=0,row=1,sticky=tk.E)
tk.Label(root.hostget,text='Username:').grid(column=0,row=2,sticky=tk.E)
tk.Label(root.hostget,text='Password:').grid(column=0,row=3,sticky=tk.E)
root.hostbox = tk.Entry(root.hostget)
root.hostbox.grid(column=1,row=1)
root.userbox = tk.Entry(root.hostget)
root.userbox.grid(column=1,row=2)
root.passbox = tk.Entry(root.hostget)
root.passbox.grid(column=1,row=3)
root.host_button = tk.Button(root.hostget,text='confirm',command=partial(host_set,root))
root.host_button.grid(column=0,row=4,columnspan=2)

root.destroyed = True

while True: # login attempt loop
    if root.destroyed:
        root.host_button.wait_variable(root.hostip)
        try:
                #print(root.hostip.get(),root.username.get(),root.password.get())
                execute(root,"SHOW TABLES")
                break
        except:
            try:
                root.geometry("900x350")
                messagebox.showerror('Login Failed', 'Error: Failed to connect and/or login.')
            except:
                pass
    else:
        sys.exit()

root.hostget.destroy()

# main GUI and variables below
root.region = ["*"]
for e,x in enumerate(execute(root,"SELECT region.name FROM region")): # populate region dropdown
    root.region.append(x[0])

root.scenario = ["*"]
root.component = ["*"]
root.year = ["*"]
root.ranges = ['']

root.settings = {'start':(2021,7,1,0,0,0),'end':(2051,7,1,0,0,0),'separator':tk.StringVar(root,','),'stringclass':tk.StringVar(root,'"')}

root.skipvar = tk.IntVar()
root.region_var = tk.StringVar(root)
root.region_var.set("region") # default value
root.scenario_var = tk.StringVar(root)
root.scenario_var.set("scenario") # default value
root.subregion_var = tk.StringVar(root)
root.subregion_var.set("subregion") # default value
root.component_var = tk.StringVar(root)
root.component_var.set("component") # default value
root.year_var = tk.StringVar(root)
root.year_var.set("year") # default value
root.range_var = tk.StringVar(root)
root.range_var.set('range')

root.output = tk.StringVar(root)
root.output.set('output')

root.geometry("900x350")
root.title('AEMO data interface') # set title


# all the dropdowns
root.region_menu = tk.OptionMenu(root,root.region_var,*root.region,command=partial(find_region,root)) # region dropdown
root.region_menu.configure(width=20)
root.region_menu.grid(column=0, row=0, sticky=tk.N)

root.subregion_check = tk.IntVar(root)
tk.Checkbutton(root, text='Include subregions',variable=root.subregion_check, onvalue=1, offvalue=0).grid(column=0,row=0)

root.scenario_menu = tk.OptionMenu(root,root.scenario_var,*root.scenario,command=partial(findscenario,root.scenario_var)) # subregion dropdown
root.scenario_menu.configure(width=20)
root.scenario_menu.grid(column=1, row=0, sticky=tk.N)

root.component_menu = tk.OptionMenu(root,root.component_var,*root.component,command=partial(findcomponent,root.component_var)) # component dropdown
root.component_menu.configure(width=20)
root.component_menu.grid(column=1, row=0)

root.year_menu = tk.OptionMenu(root,root.year_var,*root.year)#,command=partial()) # year dropdown
root.year_menu.configure(width=10)
root.year_menu.grid(column=2, row=0, sticky=tk.N)

root.list_box = tk.Listbox(root) # list selection
root.list_box.configure(width=50,height=20)
root.list_box.grid(column=4, row=0, sticky=None, rowspan=3)

root.range_menu = tk.OptionMenu(root,root.range_var,*root.ranges) # range dropdown
root.range_menu.configure(width=10, state='disabled')
root.range_menu.grid(column=1, row=0, sticky=tk.SE)

root.range_check = tk.IntVar(root)
root.range_check.set(0)
root.load_subregion_check = tk.IntVar(root)
root.load_subregion_check.set(0)

root.range_button = tk.Checkbutton(root, text='Range',variable=root.range_check, onvalue=1, offvalue=0, command=partial(swap,root))
root.range_button.grid(column=1, row=0, sticky=tk.SW)


# all the buttons
tk.Button(root,text='add selection',command=partial(add_entry,root)).grid(column=2, row=1, sticky=tk.E)
tk.Button(root,text='run query',command=partial(construct_query,root)).grid(column=2, row=2, sticky=tk.NE)
tk.Button(root,text='clear',command=partial(root.list_box.delete,0,'end')).grid(column=2, row=2, sticky=tk.E)
tk.Button(root,text='load file',command=partial(files,root)).grid(column=0, row=2)
tk.Button(root,text='custom query',command=partial(customwindow,root)).grid(column=0, row=2, sticky=tk.N)
tk.Button(root,text='DELETE selected entries',command=partial(delete,root)).grid(column=2, row=0, sticky=tk.SE)

tk.Button(root,text='Set date range',command=partial(setDate,root)).grid(column=0, row=0, sticky=tk.S)


# all the settings
root.sep_button = tk.Button(root,text=f"separator = {root.settings['separator'].get()}",command=partial(sepb,root))
root.sep_button.grid(column=1, row=2, sticky=tk.N)
root.str_button = tk.Button(root,text=f"string classifier = {root.settings['stringclass'].get()}",command=partial(strb,root))
root.str_button.grid(column=1, row=2, sticky=None)

root.startlabel = tk.Label(root)
root.endlabel = tk.Label(root)
show_date(root)
root.startlabel.grid(column=0,row=1,sticky=tk.N,columnspan=1)
root.endlabel.grid(column=0,row=1,sticky=None,columnspan=1)



root.mainloop() # run gui
