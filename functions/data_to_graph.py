import xlsxwriter
import functions.override_excel2img as excel2img
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
    __temp_filename: str = 'temp.xlsx',
    proportional_chart: bool = False
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
    graph_subtype = 'stacked' if not proportional_chart else 'percent_stacked'
    chart = workbook.add_chart({'type': 'column', 'subtype': graph_subtype})
    chart.set_y_axis({
        'name': 'Frequency' if not proportional_chart else 'Share of total',
        'name_font': {
            'name': 'Posterama',
            'color': '#F0F0F0',
            'size': 13,
            'bold': False,
        },
        'num_font': {
            'name': 'Posterama',
            'color': '#F0F0F0',
            'size': 10,
            'bold': False,
        },
        # dim the gridlines
        'major_gridlines': {
            'visible': True,
            'line': {'color': '#333339'},
        },
    })
    chart.set_x_axis({
        'name': 'Date',
        'name_font': {
            'name': 'Posterama',
            'color': '#F0F0F0',
            'size': 12,
            'bold': False,
        },
        'num_font': {
            'name': 'Posterama',
            'color': '#F0F0F0',
            'size': 10,
            'bold': False,
            'rotation': -30,
        },
    })
    
    chart_title_header = "Frequency" if not proportional_chart else "Share"
    
    chart.set_title({
        'name': f"{chart_title_header} of '{query}' by {timeinterval_word}",
        'name_font': {
            'name': 'Posterama',
            'color': '#FBFBFB',
            'size': 18,
        },
    })
    
    if query == "": # activity
        activity_title_header = "" if not proportional_chart else "Share of "
        chart.set_title({
            'name': f"{activity_title_header}Activity by {timeinterval_word}",
            'name_font': {
                'name': 'Posterama',
                'color': '#FBFBFB',
                'size': 18,
            },
        })

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
                    yield (chr(ord(''.join(s))+1), _ct)
                    _ct += 1
                    continue
                return    

    # write timestamps in col 1
    worksheet.write_column('A2', timestamps)

    # write names in row 1
    worksheet.write_row('B1', names)
    
    gap = 30
    if len(timestamps) > 50: gap = 20
    if len(timestamps) > 150: gap = 10
    if len(timestamps) > 250: gap = 0
    

    for colname, idx in _col_name_ranges(len(names)):
        # write data
        worksheet.write_column(f'{colname}2', data[idx])
        
        # add series to chart
        chart.add_series({
            'categories': f'=Sheet1!$A$2:$A${len(timestamps) + 1}',
            'values': f'=Sheet1!${colname}$2:${colname}${len(timestamps) + 1}',
            'name': f'=Sheet1!${colname}$1',
            
            # Formatting
            'gap': gap
        })
    
    CHART_WIDTH = 1663
    CHART_HEIGHT = 680
    _excel_num_cols = int(round(CHART_WIDTH / 64 - 1))
    _excel_num_rows = int(round(CHART_HEIGHT / 20))
    
    chart.set_size({'width': CHART_WIDTH, 'height': CHART_HEIGHT})
    
    # format chart
    chart.set_legend({
        'position': 'bottom',
        'font': {
            'name': 'Posterama',
            'color': '#F0F0F0',
            'size': 11,
        }
    })
    chart.set_plotarea({
        # background
        'border': {'none': True},
        'fill': {'color': '#192025'},
    })
    chart.set_chartarea({
        # background
        'border': {'none': True},
        'fill': {'color': '#192025'},
    })
    
    workbook.worksheets()[0].insert_chart('A1', chart)
    workbook.close()

    # get chart from workbook as image
    # chart width = 14 cells, height = 16 cells (i think)
    end_col_letter = chr(ord('A') + _excel_num_cols)
    excel2img.export_img(__temp_filename, imgfilename, 'Sheet1', f'A1:{end_col_letter}{_excel_num_rows}')
    # delete excel file
    #import os
    #os.remove('test13.xlsx')