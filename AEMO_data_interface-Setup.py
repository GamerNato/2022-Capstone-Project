
import mysql.connector
import sys
import tkinter as tk


##############


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
    mycursor.execute(query) # run query
    result = [x for x in mycursor]
    mydb.commit()
    return result # return result

def host_set(global_context):
    global_context.hostip.set(global_context.hostbox.get())
    global_context.username.set(global_context.userbox.get())
    global_context.password.set(global_context.passbox.get())

def on_exit(global_context):
    print('quitting')
    global_context.hostip.set('')
    try:
        global_context.destroy()
        global_context.destroyed = False
    except:
        pass
    sys.exit()


##############

# login window
root = tk.Tk() # base gui class

root.hostip = tk.StringVar()
root.hostip.set('')
root.username = tk.StringVar()
root.username.set('')
root.password = tk.StringVar()
root.password.set('')

root.protocol("WM_DELETE_WINDOW", partial(on_exit,root))

root.geometry("250x200")

root.title('login')
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)
root.rowconfigure(4, weight=1)

tk.Label(root,text='Please login.').grid(column=0,row=0,columnspan=2)
tk.Label(root,text='Hostname/IP:').grid(column=0,row=1,sticky=tk.E)
tk.Label(root,text='Username:').grid(column=0,row=2,sticky=tk.E)
tk.Label(root,text='Password:').grid(column=0,row=3,sticky=tk.E)
root.hostbox = tk.Entry(root)
root.hostbox.grid(column=1,row=1)
root.userbox = tk.Entry(root)
root.userbox.grid(column=1,row=2)
root.passbox = tk.Entry(root)
root.passbox.grid(column=1,row=3)
root.hostbutton = tk.Button(root,text='confirm',command=partial(host_set,root))
root.hostbutton.grid(column=0,row=4,columnspan=2)

root.destroyed = True

while True: # login attempt loop
    if root.destroyed:
        root.hostbutton.wait_variable(root.hostip)
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

root.destroy()


try:
    execute(root,"CREATE TABLE region (region_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, subregion_of INT)")
except:
    execute(root,"DROP TABLE region")
    execute(root,"CREATE TABLE region (region_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, subregion_of INT)")

try:
    execute(root,"CREATE TABLE scenario (scenario_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, region_id INT NOT NULL)")
except:
    execute(root,"DROP TABLE scenario")
    execute(root,"CREATE TABLE scenario (scenario_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, region_id INT NOT NULL)")

try:
    execute(root,"CREATE TABLE component (component_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, scenario_id INT NOT NULL)")
except:
    execute(root,"DROP TABLE component")
    execute(root,"CREATE TABLE component (component_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, scenario_id INT NOT NULL)")

try:
    execute(root,"CREATE TABLE year (year_id INT AUTO_INCREMENT PRIMARY KEY, candidate_year INT NOT NULL, start FLOAT NOT NULL, end FLOAT NOT NULL, component_id INT NOT NULL, data LONGBLOB NOT NULL)")
except:
    execute(root,"DROP TABLE year")
    execute(root,"CREATE TABLE year (year_id INT AUTO_INCREMENT PRIMARY KEY, candidate_year INT NOT NULL, start FLOAT NOT NULL, end FLOAT NOT NULL, component_id INT NOT NULL, data LONGBLOB NOT NULL)")

# ^^ create blank tables or wipe tables and make new ones

for x in execute(root,"SHOW TABLES"):
    print(x)

# ^ list tables
