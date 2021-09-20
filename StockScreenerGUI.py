#Author: Brendan MacIntyre
#Date: 09/19/2021
#Description: Stock screener GUI using StockScreenerEnginer

import PySimpleGUI as sg
from StockScreenerEngine import *

def is_float(str):
    """
    Returns True if string input can be converted to a float, otherwise returns False.
    """
    try:
        float(str)
        return True
    except(ValueError):
        return False


def login_window():
    """
    Displays login window and verifies that API key is valid.

    Returns:
        API key as a string if valid, or False if key is invalid.
    """
    #Set window layout
    login_layout = [[sg.Text('Enter your TD Ameritrade API key:')], [sg.Input(key='-ID-', do_not_clear=False)],
                    [sg.Button('OK')], [sg.Text(size =(30,1), key = '-ERROR-')]]
    login_window = sg.Window('Stock Screener', login_layout)

    #Event/display loop
    valid_key = False
    while not valid_key:
        event, values = login_window.read()
        #close window       
        if event == sg.WIN_CLOSED:
            break
        #Check if password valid
        elif event == 'OK':
            api_key = values['-ID-']
            valid_key = authenticate_API_key(api_key)
        #Display error message if invalid
        if not valid_key:
            login_window['-ERROR-'].update('Error: API key is invalid! Please try again')
  
    #Return API key if valid
    login_window.close()
    if valid_key:
        return api_key
    else:
        return False


def load_stock_data(api_key):
    """
    Creates a StockScreenerEngine object and displays a loading message while object is initializing.

    Args:
        api_key: String containing API key to access TD Ameritrade APIs 
    """
    screener = StockScreenerEngine(api_key)
    if screener.init_cancelled():
        return

    return screener


def get_query_filters(screener):
    """
    Displays window to retrieve query filters from user. Validates data and returns a list of the filters.

    Args:
        screener: StockScreenerEngine object
    """
    #Get list of currently supported filter options
    filter_options = screener.available_filters()
    
    #Set window layout
    filter_layout = [[sg.Text('Please choose filters:')]]
    for filter in filter_options:
        if screener.get_all_stock_data()[filter].dtypes == object:
            #One input for string filters
            filter_layout.append([sg.Checkbox(filter+":", size=(30,1)), sg.InputText(key = filter,size=(15,1))])
        else:
            #Min and max input for numerical filters
            filter_layout.append([sg.Checkbox(filter+":", size = (30,1)), 
                                  sg.Text('min'), sg.InputText(key = filter+'min',size=(15,1)),
                                  sg.Text('max'), sg.InputText(key = filter+'max',size=(15,1))])
    filter_layout.append([sg.Submit('Set Filters')])
    
    #Display window
    window = sg.Window('Stock Screener', filter_layout)
    event, values = window.read()
    window.close()

    #Unpack and format input
    filters = {} 
    invalid_input = False
    for checkmark in range(len(filter_options)):
        #Check if filter was selected
        if values[checkmark]:
            try:
                #String filter (one input/key)
                filters[filter_options[checkmark]] = values[filter_options[checkmark]]
            except(KeyError):
                #Numerical filter (multiple inputs/keys)
                filter = filter_options[checkmark]
                min = values[filter+'min']
                max = values[filter+'max']
                
                #Set default values if no input entered
                if min == "":
                    min = screener.get_all_stock_data()[filter].min()
                if max == "":
                    max = screener.get_all_stock_data()[filter].max()
                
                #Validate that input is numerical
                if not is_float(min) or not is_float(max):
                    invalid_input = True 
                    sg.popup("Error: Invalid input... Please enter numerical data only in min/max values")
                    break
                
                filters[filter] = [float(min),float(max)]
    
    #Re-prompt for input if input was invalid
    if invalid_input:
        get_query_filters(screener)
    
    return filters


def display_query(screener):
    """
    Displays the query results dataframe. Window contains options to reset filters and sort data.

    Args:
        screener: StockScreenerEngine object
    """
    #Get query results dataframe
    header_list = screener.get_query_results().columns.values.tolist()
    data = screener.get_query_results().values.tolist()
    
    #Display error message if dataframe is empty
    if len(data) == 0:
        sg.popup("Your query returned 0 results, please try again.")
        screener.reset_query()
        new_filters = get_query_filters(screener)
        screener.query(**new_filters)
        display_query(screener)

    #Set layout
    layout = [[sg.Button('Reset Filters'), sg.Button('Sort Data')],
              [sg.Table(values=data, headings=header_list,
               display_row_numbers=False, auto_size_columns=True,
               num_rows=min(25, len(data)))]]

    #Display window and get events
    window = sg.Window('Stock Screener', layout)
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        return

    #Get new filters
    if event == 'Reset Filters':
        screener.reset_query()
        new_filters = get_query_filters(screener)
        screener.query(**new_filters)
        window.close()
        display_query(screener)
    
    #Sort data
    if event == 'Sort Data':
        sort_query_display(screener)
        window.close()
        display_query(screener)

    window.close()


def sort_query_display(screener):
    """
    Displays a window to get sorting options from user.

    Args:
        screener: StockScreenerEngine object
    """
    
    #Set layout
    columns = tuple(screener.get_query_results().columns.values.tolist())
    layout = [[sg.Text('What column do you want to sort by?')],
              [sg.Listbox(columns, size=(30,len(columns)), key = '-COL-')],
              [sg.Checkbox('Descending Order')],
              [sg.Button('OK')]]

    window = sg.Window('Stock Screener', layout)

    #Display/event loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == 'OK':
            #Get column chosen and ascending/descending option
            if values['-COL-']:
               screener.sort_query_results(values['-COL-'][0], not values[0])
               break
    
    window.close()


def main():
    api_key = login_window()
    if api_key is not False:
        StockScreener = load_stock_data(api_key)
        if StockScreener is None:
            #User closed program
            return
        filters = get_query_filters(StockScreener)
        StockScreener.query(**filters)        
        display_query(StockScreener)


if __name__ == '__main__':
    main()

        



