import os
import xlsxwriter
from . import BaseReport
import time


PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)


def report(info):
    create_time = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
    workbook = xlsxwriter.Workbook(create_time + '_monkey_report.xlsx')
    bo = BaseReport.OperateReport(workbook)
    bo.monitor(info)
    bo.crash()
    bo.analysis(info)
    bo.close()