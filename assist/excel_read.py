import xlrd


# excel文档数据读取
def read_xls(file, sheet, column):
    _workbook = xlrd.open_workbook(file)
    # 输入为sheet名称(str)
    if isinstance(sheet, int):
        _table = _workbook.sheet_by_index(sheet)
    # 输入为sheet索引值(int)
    elif isinstance(sheet, str):
        _table = _workbook.sheet_by_name(sheet_name=sheet)
    else:
        raise ('read_xls()中的参数sheet只能输入sheet名称(str)或sheet索引值(int)')
    _cols = _table.col_values(column)
    return _cols
