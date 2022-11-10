
import mysql.connector
import numpy as np
import pandas as pd
import xlsxwriter as xls
import csv
import openpyxl as opx
import xlrd
import sys


##############


from xlrd.xldate import xldate_from_datetime_tuple
from xlrd.xldate import xldate_as_datetime
from xlrd.xldate import xldate_as_tuple
from tkinter import messagebox


##############


def execute(global_context,query): # function for connecting to the database, running a query and returning the results
    mydb = mysql.connector.connect( # connect
        host=global_context.hostip,
        user=global_context.username,
        password=global_context.password,
        database="demand"
    )
    mycursor = mydb.cursor() # create cursor
    print(query)
    mycursor.execute(query) # run query
    result = [x for x in mycursor]
    mydb.commit() # make sure the actions stick
    return result # return result

def construct_query(global_context): # query from each selection
    print(global_context.items)
    data = [] # holds the actual data
    columns = [] # holds the column names
    for element in global_context.items: # for each item
        query_region_id = []
        query_region_name = []
        if element[0] == '*': # select all regions
            # select regions
            for x in execute(global_context,f"SELECT region_id,name FROM region"):
                query_region_id.append(x[0])
                query_region_name.append(x[1])
        else: # select from only the given region
            # select regions
            for x in execute(global_context,f"SELECT region_id,name FROM region WHERE region.name = '{element[0]}'"):
                query_region_id.append(x[0])
                query_region_name.append(x[1])
                break
            if element[1]: # include subregions of that region
                # select subregions
                for x in execute(global_context,f"SELECT region_id,name FROM region WHERE subregion_of = {query_region_id[-1]}"):
                    query_region_id.append(x[0])
                    query_region_name.append(x[1])
        query_scenario_id = []
        query_scenario_name = []
        if element[2] == '*': # select from all scenarios
            for y,z in zip(query_region_id,query_region_name): # for each selected region
                # select scenarios
                for x in execute(global_context,f"SELECT scenario_id,name FROM scenario WHERE scenario.region_id = {y}"):
                    query_scenario_id.append(x[0])
                    query_scenario_name.append((z,x[1]))
        else: # select from only the given component type
            for y,z in zip(query_region_id,query_region_name): # for each selected region
                # select scenarios
                for x in execute(global_context,f"SELECT scenario_id,name FROM scenario WHERE scenario.region_id = {y} and scenario.name = '{element[2]}'"):
                    query_scenario_id.append(x[0])
                    query_scenario_name.append((z,x[1]))
                    break
        query_component_id = []
        query_component_name = []
        if element[3] == '*': # select from all components
            for y,z in zip(query_scenario_id,query_scenario_name): # for each selected scenario
                # select components
                for x in execute(global_context,f"SELECT component_id,name FROM component WHERE component.scenario_id = {y}"):
                    query_component_id.append(x[0])
                    query_component_name.append(z+(x[1],))
        else: # select from only the given component type
            for y,z in zip(query_scenario_id,query_scenario_name): # for each selected scenario
                # select components
                for x in execute(global_context,f"SELECT component_id,name FROM component WHERE component.scenario_id = {y} and component.name = '{element[3]}'"):
                    query_component_id.append(x[0])
                    query_component_name.append(z+(x[1],))
                    break
        if element[4] == '*': # select all from year
            for y,z in zip(query_component_id,query_component_name): # for each selected component
                # select years
                for x in execute(global_context,f"SELECT candidate_year,start,end,data FROM year WHERE year.component_id = {y}"):
                    data.append(eval(x[3])[:100])
                    start=x[1]
                    end=x[2]
                    columns.append(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
        else: # select only that year
            for y,z in zip(query_component_id,query_component_name): # for each selected component
                # select years
                for x in execute(global_context,f"SELECT candidate_year,start,end,data FROM year WHERE year.component_id = {y} and year.candidate_year = {element[4]}"):
                    data.append(eval(x[3])[:100])
                    start=x[1]
                    end=x[2]
                    columns.append(f"{z[0]}/{z[1]}/{z[2]}/{x[0]}")
                    break
    if len(columns): # if anything found
        return convert(global_context,data,columns,start,end) # convert to preferred format and return
    return None

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

#Print the data to an excel document.
def output_Excel(global_context,data):
    workbook = xls.Workbook(f"{global_context.output}.xlsx") # create output file
    worksheet = workbook.add_worksheet()
    
    for c, column in enumerate(data.columns): # write column headings
        worksheet.write(0,c,column)
    for r, row in enumerate(data.values): # write actual data
        r+=1
        for c, item in enumerate(row):
            worksheet.write(r,c,item)
    workbook.close()
    print('excel file has been written successfully!')
    root.debug_log.append('excel file has been written successfully!')

#Print the data to a CSV file.
def output_CSV(global_context,data):
    file = open(f"{global_context.output}.csv", 'w') # create output file
    for e,column in enumerate(data.columns): # write column headings
        if type(column) == str: # if value is a string add string classfifiers
            file.write(f"{global_context.settings['stringclass']}{column}{global_context.settings['stringclass']}")
        else:
            file.write(f"{column}")
        if e != len(data.columns)-1: # end of row doesn't need a separator
            file.write(f"{global_context.settings['separator']}")
    file.write("\n")
    for row in data.values: # write actual data
        for e,value in enumerate(row):
            if type(value) == str: # if value is a string add string classfifiers
                file.write(f"{global_context.settings['stringclass']}{value}{global_context.settings['stringclass']}")
            else:
                file.write(f"{value}")
            if e != len(row)-1: # end of row doesn't need a separator
                file.write(f"{global_context.settings['separator']}")
        file.write('\n')
    file.close()
    print('delimited file has been written successfully!')
    root.debug_log.append('delimited file has been written successfully!')

#Print the data to a txt file.
def output_Txt(global_context,data):
    file = open(f"{global_context.output}.txt", 'w') # create output file
    for e,column in enumerate(data.columns): # write column headings
        if type(column) == str: # if value is a string add string classfifiers
            file.write(f"{global_context.settings['stringclass']}{column}{global_context.settings['stringclass']}")
        else:
            file.write(f"{column}")
        if e != len(data.columns)-1: # end of row doesn't need a separator
            file.write(f"{global_context.settings['separator']}")
    file.write("\n")
    for row in data.values: # write actual data
        for e,value in enumerate(row):
            if type(value) == str: # if value is a string add string classfifiers
                file.write(f"{global_context.settings['stringclass']}{value}{global_context.settings['stringclass']}")
            else:
                file.write(f"{value}")
            if e != len(row)-1: # end of row doesn't need a separator
                file.write(f"{global_context.settings['separator']}")
        file.write('\n')
    file.close()
    print('delimited file has been written successfully!')
    root.debug_log.append('delimited file has been written successfully!')

def process(raw): # turn raw file into just the data ignoring times and column headings
    processed = []
    for x in raw[1:]: # ignore column head
        for y in x[3:]: # ignore date
            processed.append(y) # add value to list
    return processed

def loader(global_context,f,title,kind): # load new files
    if not global_context.year.isdigit(): # check that the year is at least a digit
        print('Not a year!', f'Error: The year box must be a positive integer.')
        global_context.debug_log.append(f"context.year.isdigit() : {global_context.year.isdigit()}")
        sys.exit()
    if kind[:-1] == 'xls': # if excel file
        try:
            wb = opx.load_workbook(f, read_only=True) # open workbook
            sheet = wb.active # get active sheet
            data = [x for x in sheet.values] # get data
            wb.close() # close file
        except:
            print("Error loading excel file!")
            global_context.debug_log.append(f"excel file = {f}")
            global_context.debug_log.append("Error loading excel file!")
            sys.exit()
    else: # if delimited file
        try: # try reading the file
            file = open(f,'r')
            data = [x for x in csv.reader(file, delimiter=global_context.settings['separator'], quotechar=global_context.settings['stringclass'])]
            file.close()
        except: # if fail
            print("Error loading delimited file!")
            global_context.debug_log.append(f"delimited file = {f}")
            global_context.debug_log.append("Error loading delimited file!")
            sys.exit()
    if not all([len(x)==51 for x in data]): # if data is the wrong shape
        print("Error loading file: bad format")
        global_context.debug_log.append(f"file = {f}")
        global_context.debug_log.append("Error loading file: bad format")
        sys.exit()

    # by this point the file has been loaded and is the correct shape
    print(global_context.region,global_context.subregion,global_context.scenario,global_context.component,global_context.year)
    # get start and end dates from tuples
    start = xldate_from_datetime_tuple((int(data[1][0]),int(data[1][1]),int(data[1][2]),0,0,0),0)
    end = xldate_from_datetime_tuple((int(data[-1][0]),int(data[-1][1]),int(data[-1][2]),0,0,0),0)+1

    try: # try to treat data as float but if not just load as-is
        data = [float(y) for y in [x for x in process(data)]]
    except:
        data = [y for y in [x for x in process(data)]]
        print(f'Error: Some of this data cannot be treated as a number.\n It will not be included in any calculations done.')
        global_context.debug_log.append(f'Error: Some of this data cannot be treated as a number.\n It will not be included in any calculations done.')
    
    # region

    # check existence
    regiondupe = execute(global_context,f"SELECT region_id FROM region WHERE name = '{global_context.region}'")
    if len(regiondupe): # if exists
        regiondupe = regiondupe[0][0]
    else: # else create new
        if global_context.subregion: # if subregion
            meta = execute(global_context,f"SELECT region_id FROM region WHERE name = '{global_context.subregion}'")[0][0]
            execute(global_context,f"INSERT INTO region (name,subregion_of) VALUES ('{global_context.region}',{meta})")
        else: # else regular region
            execute(global_context,f"INSERT INTO region (name) VALUES ('{global_context.region}')")
        regiondupe = execute(global_context,f"SELECT region_id FROM region WHERE name = '{global_context.region}'")[0][0]
        print(regiondupe)
    
    # scenario

    # check existence
    scenariodupe = execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {regiondupe} AND scenario.name = '{global_context.scenario}'")
    if len(scenariodupe): # if exists
        scenariodupe = scenariodupe[0][0]
    else: # else create new
        execute(global_context,f"INSERT INTO scenario (name,region_id) VALUES ('{global_context.scenario}',{regiondupe})")
        scenariodupe = execute(global_context,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {regiondupe} AND scenario.name = '{global_context.scenario}'")[0][0]
    
    # component

    # check existence
    componentdupe = execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {scenariodupe} AND component.name = '{global_context.component}'")
    if len(componentdupe): # if exists
        componentdupe = componentdupe[0][0]
    else: # else create new
        execute(global_context,f"INSERT INTO component (name,scenario_id) VALUES ('{global_context.component}',{scenariodupe})")
        componentdupe = execute(global_context,f"SELECT component_id FROM component WHERE component.scenario_id = {scenariodupe} AND component.name = '{global_context.component}'")[0][0]
        
    # year

    # check existence
    yeardupe = execute(global_context,f"SELECT year_id FROM year WHERE year.component_id = {componentdupe} AND year.candidate_year = {global_context.year}")
    if len(yeardupe): # if exists
        print("Error: The file you are trying to enter already exists!")
        print("See section 4 of the user manual for more info.")
        global_context.debug_log.append("Error: The file you are trying to enter already exists!")
        global_context.debug_log.append("See section 4 of the user manual for more info.")
    else: # else create new
        mydb = mysql.connector.connect( # connect
            host="localhost",
            user="setup",
            password="putes",
            database="demand"
        )
        mycursor = mydb.cursor() # create cursor
        mycursor.execute("INSERT INTO year (candidate_year,start,end,component_id,data) VALUES (%s,%s,%s,%s,%s)",(global_context.year,start,end,componentdupe,str(data)))
        mydb.commit() # commit changes

    # done
    print('done')

def delete(global_context): # delete selected entry
    print(global_context.items)
    for element in global_context.items:
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
        else: # select only that year
            for y in query_component_id: # for each selected component
                execute(global_context,f"DELETE FROM year WHERE year.component_id = {y} and year.candidate_year = {element[4]}")

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
    
    print('Entry has been deleted succesfully!')
    global_context.debug_log.append('Entry has been deleted succesfully!')


##############


class Context(object): # expandable container for parsing settings and other global info
    pass

def exit(global_context): # stuff to do on safe exit
    file = open('debug_log.txt','w') # open logfile
    for x in global_context.debug_log: # write log to file
        file.write(str(x))
        file.write('\n')
    file.write('debug log written successfully.') # confirm that the debug log itself didn't crash
    print('debug log written successfully.')
    file.write('\n')
    file.close() # close logfile
    sys.exit() # safe quit

# help: --help

# separator: --separator [character]
# stringclassifier: --stringclassifier [character]
# datetime: --datetime [year] [month] [day] [hour] [minute] [second] [year] [month] [day] [hour] [minute] [second]

# insert: --insert [filepath] [region] [subregion] [scenario] [component] [year]
# delete: --delete [region] [subregions? ('True' or 'False')] [scenario] [component] [year]
# query: --query [n] [[region] [subregions? ('True' or 'False')] [scenario] [component] [year]] [type ('excel'/'csv'/'txt')] [output file name]
# search: --search [region]/ [region] [scenario]/ [region] [scenario] [component]/ [region] [scenario] [component] [year]
# custom: --custom [SQL]

root = Context() # create root container
root.settings = {'start':(2021,7,1,0,0,0),'end':(2051,7,1,0,0,0),'separator':',','stringclass':'"'} # default settings
root.debug_log = []
root.debug_log.append([x for x in sys.argv])
sys.argv.pop(0) # first argument is the filename so 'pop!'

if '--help' in sys.argv: # print help info and exit
    print('help: --help')
    print()
    print('all functional runs must begin with the hostname/ip of the database, the username, and then the password like: program.exe [hostname/ip] [username] [password] ...')
    print()
    print('settings:')
    print('  separator: --separator [character]')
    print('  stringclassifier: --stringclassifier [character]')
    print('  datetime: --datetime [year] [month] [day] [hour] [minute] [second] [year] [month] [day] [hour] [minute] [second]')
    print(' start time, then end time')
    print()
    print('operations:')
    print('  insert: --insert [filepath] [region] [subregion] [scenario] [component] [year]')
    print("  delete: --delete [region] [subregions? ('True' or 'False')] [scenario] [component] [year]")
    print("  query: --query [n] [[region] [subregions? ('True' or 'False')] [scenario] [component] [year]] [type ('excel'/'csv'/'txt')] [output file name]")
    print('  search: --search / [region]/ [region] [scenario]/ [region] [scenario] [component]/ [region] [scenario] [component] [year]')
    print('  custom: --custom [SQL]')
    root.debug_log.append(f"--help")
    exit(root)

if len(sys.argv) < 3: # check that there's enough info to login
    print("not enough arguemnts, expecting [hostname/ip] [username] [password]")
    root.debug_log.append("not enough arguemnts, expecting [hostname/ip] [username] [password]")
    exit(root)

# set login variables
root.hostip = sys.argv.pop(0)
root.username = sys.argv.pop(0)
root.password = sys.argv.pop(0)

try: # try to login
    mydb = mysql.connector.connect( # connect
        host="localhost",
        user="setup",
        password="putes",
        database="demand"
    )
except:
    print(f"cannot connect to '{root.hostip}'")
    root.debug_log.append(f"cannot connect to '{root.hostip}'")
    exit(root)

while len(sys.argv): # while there's more arguments
    print(sys.argv[0])
    if sys.argv[0] == '--datetime': # set datetime range
        sys.argv.pop(0)
        if len(sys.argv) < 12: # make sure there's enough arguments for both datetimes
            print(f"too few arguments, expecting [year] [month] [day] [hour] [minute] [second] [year] [month] [day] [hour] [minute] [second]")
            root.debug_log.append(f"too few arguments, expecting [year] [month] [day] [hour] [minute] [second] [year] [month] [day] [hour] [minute] [second]")
            exit(root)
        root.settings['start'] = tuple([int(x) for x in sys.argv[:6]]) # enter arguments into setting
        for x in range(6): # remove used arguments
            sys.argv.pop(0)
        root.settings['end'] = tuple([int(x) for x in sys.argv[:6]]) # enter arguments into setting
        for x in range(6): # remove used arguments
            sys.argv.pop(0)
    elif sys.argv[0] == '--separator': # set separator
        sys.argv.pop(0)
        root.settings['separator'] = sys.argv[0].replace(r'\t','\t').replace(r'\r','\r').replace(r'\n','\n')[0] # get argument, parse escape characters, get first character
        sys.argv.pop(0)
    elif sys.argv[0] == '--stringclassifier': # set classifier
        sys.argv.pop(0)
        root.settings['stringclass'] = sys.argv[0].replace(r'\t','\t').replace(r'\r','\r').replace(r'\n','\n')[0] # get argument, parse escape characters, get first character
        sys.argv.pop(0)
    elif sys.argv[0] == '--insert': # insert new entry
        sys.argv.pop(0)
        print(sys.argv[0])
        filepath = sys.argv.pop(0) # filepath
        title = filepath.split('/')[-1] # file name
        kind = title.split('.')[-1] # file extension

        # collect arguments
        root.region = sys.argv[0].pop(0)
        root.subregion = sys.argv[0].pop(0)
        if root.subregion == 'NONE':
            root.subregion = None
        root.scenario = sys.argv[0].pop(0)
        root.component = sys.argv[0].pop(0)
        root.year = sys.argv[0].pop(0)

        try: # try loading the file
            loader(root,filepath,title,kind)
        except:
            print(f"ERROR")
            root.debug_log.append(f"ERROR")
        exit(root)
    elif sys.argv[0] == '--custom': # custom SQL queries
        sys.argv.pop(0)
        file = open('custom_output.txt','w') # open output file
        query = sys.argv.pop(0)
        file.write(query)
        file.write('\n')
        try: # try query
            for x in execute(root,query): # run query and print/write results
                print(x)
                root.debug_log.append(x)
                file.write(str(x))
                file.write('\n')
        except: # print error
            print(f"ERROR")
            root.debug_log.append(f"ERROR")
            file.write(f"ERROR")
            file.write('\n')
        file.close()
        exit(root)
    elif sys.argv[0] == '--query': # query database
        sys.argv.pop(0)
        root.items = []

        if not sys.argv[0].isdigit: # check that [n] can be an int
            print(f"{sys.argv[0]} must be an integer.")
            root.debug_log.append(f"{sys.argv[0]} must be an integer.")
            exit(root)

        for z in range(int(sys.argv.pop(0))): # for each entry
            if len(sys.argv) < 7: # make sure there's enough arguments
                print(f"too few arguments, expecting [n] [[region] [subregions? ('True' or 'False')] [scenario] [component] [year]] [type ('excel'/'csv'/'txt')] [output file name]")
                root.debug_log.append(f"too few arguments, expecting [n] [[region] [subregions? ('True' or 'False')] [scenario] [component] [year]] [type ('excel'/'csv'/'txt')] [output file name]")
                exit(root)

            # collect arguments
            root.region = sys.argv.pop(0)
            root.subregions = sys.argv.pop(0)

            if root.subregions == 'True':
                root.subregions = True
            elif root.subregions == 'False':
                root.subregions = False
            else:
                print(f"{root.subregions} is not a boolean value. Should be 'True' or 'False'.")
                root.debug_log.append(f"{root.subregions} is not a boolean value. Should be 'True' or 'False'.")
                exit(root)

            root.scenario = sys.argv[0]
            sys.argv.pop(0)
            root.component = sys.argv[0]
            sys.argv.pop(0)
            root.year = sys.argv[0]
            sys.argv.pop(0)

            root.items.append((root.region,root.subregions,root.scenario,root.component,root.year)) # add entry to list

        if len(sys.argv) < 2: # make sure theres enough arguments for output
            print(f"missing output type or name, expecting [type ('excel'/'csv'/'txt')] [output file name]")
            root.debug_log.append(f"missing output type or name, expecting [type ('excel'/'csv'/'txt')] [output file name]")
            exit(root)

        if sys.argv[0] == 'excel': # check output type and run
            sys.argv.pop(0)
            root.output = sys.argv[0]
            try:
                output_Excel(root,construct_query(root))
            except:
                print('error: query had no results!')
                root.debug_log.append('error: query had no results!')
                exit(root)
        elif sys.argv[0] == 'csv': # check output type and run
            sys.argv.pop(0)
            root.output = sys.argv[0]
            try:
                output_CSV(root,construct_query(root))
            except:
                print('error: query had no results!')
                root.debug_log.append('error: query had no results!')
                exit(root)
        elif sys.argv[0] == 'delimited': # check output type and run
            sys.argv.pop(0)
            root.output = sys.argv[0]
            try:
                output_Txt(root,construct_query(root))
            except:
                print('error: query had no results!')
                root.debug_log.append('error: query had no results!')
                exit(root)
        else: # no output
            print('no output specified!')
            root.debug_log.append('No output specified!')
        exit(root)

    elif sys.argv[0] == '--delete': # delete entry
        sys.argv.pop(0)

        if len(sys.argv) < 5: # make sure there's enough arguments
            print(f"too few arguments, expecting [region] [subregions? ('True' or 'False')] [scenario] [component] [year]]")
            root.debug_log.append(f"too few arguments, expecting [region] [subregions? ('True' or 'False')] [scenario] [component] [year]]")
            exit(root)

        # collect arguments
        root.region = sys.argv.pop(0)
        root.subregions = sys.argv.pop(0)

        if root.subregions == 'True':
            root.subregions = True
        elif root.subregions == 'False':
            root.subregions = False
        else:
            print(f"{root.subregions} is not a boolean value. Should be 'True' or 'False'.")
            exit(root)

        root.scenario = sys.argv.pop(0)
        root.component = sys.argv.pop(0)
        root.year = sys.argv.pop(0)

        root.items = [(root.region,root.subregions,root.scenario,root.component,root.year)] # add entry to list

        try: # try to delete entries
            delete(root)
        except:
            print(f"ERROR")
            root.debug_log.append(f"ERROR")
        exit(root)

    elif sys.argv[0] == '--search': # search the database one layer at a time
        sys.argv.pop(0)
        output = []
        query = []
        print(sys.argv)
        if len(sys.argv): # if theres any arguments left work down the heirarchy
            region_query = []
            query.append(sys.argv.pop(0))
            for x in execute(root,f"SELECT region_id FROM region WHERE region.name = '{query[-1]}'"): # select region
                region_query.append(x)
            if len(sys.argv): # if theres any arguments left work down the heirarchy
                scenario_query = []
                query.append(sys.argv.pop(0))
                for x in region_query:
                    for y in execute(root,f"SELECT scenario_id FROM scenario WHERE scenario.region_id = {x[0]} and scenario.name = '{query[-1]}'"): # select scenario
                        scenario_query.append(y)
                if len(sys.argv): # if theres any arguments left work down the heirarchy
                    component_query = []
                    query.append(sys.argv.pop(0))
                    for x in scenario_query:
                        for y in execute(root,f"SELECT component_id FROM component WHERE component.scenario_id = {x[0]} AND component.name = '{query[-1]}'"): # select component
                            component_query.append(y)
                    if len(sys.argv): # if theres any arguments left work down the heirarchy
                        query.append(sys.argv.pop(0))
                        for x in component_query:
                            for y in execute(root,f"SELECT year_id,candidate_year,component_id FROM year WHERE year.component_id = {x[0]} AND year.candidate_year = {query[-1]}"): # select year
                                output.append(y)
                    else: # return years
                        for x in component_query:
                            for y in execute(root,f"SELECT year_id,candidate_year,component_id FROM year WHERE year.component_id = {x[0]}"): # select year
                                output.append(y)
                else: # return components
                    for x in scenario_query:
                        for y in execute(root,f"SELECT component_id,name,scenario_id FROM component WHERE component.scenario_id = {x[0]}"): # select component
                            output.append(y)
            else: # return scenarios
                for x in region_query:
                    for y in execute(root,f"SELECT scenario_id,name,region_id FROM scenario WHERE scenario.region_id = {x[0]}"): # select scenario
                        output.append(y)
        else: # return regions
            for x in execute(root,f"SELECT region_id,name,subregion_of FROM region"): # select region
                output.append(x)
        file = open(f"searchoutput.txt", 'w') # write results to file
        file.write(str(query))
        file.write('\n\n')
        for line in output:
            print(line)
            file.write(str(line))
            file.write('\n')
        file.close()
        print('search output has been written successfully!')
        root.debug_log.append('search output has been written successfully!')
        exit(root)

    else: # if the argument doesn't belong to anything
        print(f"unexpected argument: {sys.argv[0]}")
        root.debug_log.append(f"unexpected argument: {sys.argv[0]}")
        exit(root)

exit(root)
