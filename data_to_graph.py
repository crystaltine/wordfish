import xlsxwriter
import override_excel2img as excel2img
from string import ascii_uppercase
import itertools
from PIL.ImageFile import ImageFile

def data_to_graph(
    timestamps: list[str], 
    data: list[list[int]], 
    names: list[str], 
    query: str, 
    timeinterval: str,
    imgfilename: str,
    __temp_filename: str = 'temp.xlsx'
    ) -> list[str] | ImageFile | None:
    """
    Notes:
    `timestamps` must be in ASCENDING ORDER! (earliest to latest)
    `data` and `names` must be synchronized (i.e. index of a username matches to the index of their data)
    
    The following are true:
    ```
    len(timestamps) == len(data[0]) # number of timestamps equals number of data points in each list (data series) in data
    len(names) == len(data) # number of users equals number of lists (data series) in data
    ```
    
    Saves a stacked column chart with x-axis as `timestamps` and y-axis as frequency (numbers in `data`) at `imgfilename`
    """
    
    if not __temp_filename.endswith('.xlsx'):
        __temp_filename += '.xlsx'

    workbook = xlsxwriter.Workbook(__temp_filename)
    worksheet = workbook.add_worksheet('Sheet1')
    # select data range
    # from A1 - J5
    #worksheet = workbook.add_worksheet()

    timeinterval_word = \
        'day' if timeinterval == "d" else \
        'week' if timeinterval == "w" else 'month'
        
        
    #data_start_location = [0, 0] # A1
    #data_end_location = [9, 4] # J5

    # Get a stacked column chart graph
    chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
    chart.set_y_axis({'name': 'Frequency'})
    chart.set_x_axis({'name': 'Date'})
    
    chart.set_title({'name': f"Frequency of '{query}' by {timeinterval_word}"})
    if query == "": # activity
        chart.set_title({'name': f"Activity by {timeinterval_word}"})

    def _col_name_ranges(num: int):
        """
        Returns a generator from `B` with `num` elements, in excel column name format
        ex.
        ```
        _col_name_ranges(30) -> ['B', 'C', 'D', ... , 'Z', 'AA', ... , 'AE']
        ```
        """
        _ct = 0
        for size in itertools.count(1):
            for s in itertools.product(ascii_uppercase, repeat=size):
                if _ct < num:
                    
                    # TODO - include start variable
                    
                    yield (chr(ord(''.join(s))+1), _ct)
                    _ct += 1
                    continue
                return    

    # write timestamps in col 1
    worksheet.write_column('A2', timestamps)

    # write names in row 1
    worksheet.write_row('B1', names)

    for colname, idx in _col_name_ranges(len(names)):
        # write data
        worksheet.write_column(f'{colname}2', data[idx])
        
        # add series to chart
        chart.add_series({
            'categories': f'=Sheet1!$A$2:$A${len(timestamps) + 1}',
            'values': f'=Sheet1!${colname}$2:${colname}${len(timestamps) + 1}',
            'name': f'=Sheet1!${colname}$1'     
        })
            
    chart.set_size({'width': 961, 'height': 342})
    
    workbook.worksheets()[0].insert_chart('A1', chart)
    workbook.close()

    # get chart from workbook as image
    # chart width = 14 cells, height = 16 cells (i think)
    try:
        excel2img.export_img(__temp_filename, imgfilename, 'Sheet1', 'A1:O17')
    except:
        raise Exception() # handle this on higher levels
    # delete excel file
    #import os
    #os.remove('test13.xlsx')