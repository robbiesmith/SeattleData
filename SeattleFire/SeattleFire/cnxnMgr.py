import pyodbc
from SeattleFire.config import data
import os

#server = 'localhost'
#database = 'seattle_data'
#connStr = "Driver={SQL Server};Server=localhost;Database=seattle_data;Integrated Security=True"
#Driver={ODBC Driver 13 for SQL Server};Server=tcp:rsseattledata.database.windows.net,1433;Database=data2;Uid=robsmith@rsseattledata;Pwd={your_password_here};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
#Driver=Connection Timeout=30;
#SQLAZURECONNSTR_data
#cnxn = pyodbc.connect(Trusted_Connection='yes', driver='{SQL Server}', server='localhost\\SQLEXPRESS', database='seattle_data')
#cnxn = pyodbc.connect(Trusted_Connection='yes', driver='{SQL Server}', server='localhost', database='seattle_data')
cursor = None
cnxn = None

def getCnxn(forced=False):
    global cnxn
    if forced:
        cnxn = None
    if not cnxn:
        if False and 'SQLAZURECONNSTR_data' in os.environ:
            connStr = os.environ['SQLAZURECONNSTR_data']
#            connStr = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:rsseattledata.database.windows.net,1433;Database=data;Uid=robsmith@rsseattledata;Pwd=kaurapo/0kaurapo/0;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            print(connStr)
            cnxn = pyodbc.connect(connStr)
        else:
            cnxn = pyodbc.connect(Trusted_Connection='no',
#                driver='{ODBC Driver 13 for SQL Server}',
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
    
    