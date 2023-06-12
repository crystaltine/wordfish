csvpath = 'queryfiles/a-general-monthly-d504b98c.csv'

from pyexcel.cookbook import merge_all_to_a_book
import glob
import xlsxwriter

merge_all_to_a_book(glob.glob(csvpath), "output.xlsx")