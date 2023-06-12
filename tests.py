import win32com.client
import PIL
from PIL import ImageGrab, Image
import os
import sys

inputExcelFilePath = "D:\\projects\\wordfish\\queryfiles\\a-general-monthly-d504b98c.xlsx"
outputPNGImagePath = "D:\\projects\\wordfish\\graphimgs\\test1"

# This function extracts a graph from the input excel file and saves it into the specified PNG image path (overwrites the given PNG image)
def saveExcelGraphAsPNG(inputExcelFilePath, outputPNGImagePath):
    # Open the excel application using win32com
    o = win32com.client.Dispatch("Excel.Application")
    # Disable alerts and visibility to the user
    o.Visible = 0
    o.DisplayAlerts = 0
    # Open workbook
    wb = o.Workbooks.Open(inputExcelFilePath)

    # Extract first sheet
    sheet = o.Sheets(1)
    for n, shape in enumerate(sheet.Shapes):
        # Save shape to clipboard, then save what is in the clipboard to the file
        shape.Copy()
        image = ImageGrab.grabclipboard()
        length_x, width_y = image.size
        size = int(2 * length_x), int(2 * width_y)
        image_resized = image.resize(size, Image.ANTIALIAS)
        temp_saved_img = outputPNGImagePath + 'temp.png'
        image_resized.save(temp_saved_img, 'PNG')
        pass
    pass

    wb.Close(True)
    o.Quit()
    
saveExcelGraphAsPNG(inputExcelFilePath, outputPNGImagePath)