import pyodbc
from SeattleFire.config import data
import os

cursor = None
cnxn = None

def getCnxn(forced=False):
    global cnxn
    if forced:
        cnxn = None
    if not cnxn:
        if False and 'SQLAZURECONNSTR_data' in os.environ:
            connStr = os.environ['SQLAZURECONNSTR_data']
            print(connStr)
            cnxn = pyodbc.connect(connStr)
            cnxn.timeout = 100
        else:
            cnxn = pyodbc.connect(Trusted_Connection='no',
                driver='{SQL Server}',
                server='tcp:rsseattledata.database.windows.net,1433',
                database='data',
                Uid=data['username'],
                Pwd=data['password'],
                Encrypt='yes',
                TrustServerCertificate='no',
                Connection_Timeout='30')
    return cnxn

def getCursor(forced=False):
    global cursor
    if forced:
        cursor = None
    if not cursor:
        getCnxn(forced)
        cursor = cnxn.cursor()
    return cursor
    
    