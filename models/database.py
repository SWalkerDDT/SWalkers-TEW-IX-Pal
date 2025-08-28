import os
import sqlite3
from config import DB_PATH

try:
    import pyodbc
except ImportError:
    pyodbc = None

class Database:
    """
    Database connection manager supporting SQLite and MS Access (MDB) files.

    Args:
        backend (str): 'sqlite' or 'access'.
        db_path (str, optional): Path to the database file. Defaults to DB_PATH.
        password (str, optional): Password for Access database.

    Raises:
        ImportError: If pyodbc is not installed for Access backend.
        ValueError: If backend is not supported.
    """
    def __init__(self, backend='sqlite', db_path=None, password=None):
        """
        Initialize the Database connection manager.

        Args:
            backend (str): 'sqlite' or 'access'.
            db_path (str, optional): Path to the database file. Defaults to DB_PATH.
            password (str, optional): Password for Access database.
        Raises:
            ImportError: If pyodbc is not installed for Access backend.
            ValueError: If backend is not supported.
        """
        self.backend = backend
        self.db_path = db_path or DB_PATH
        self.password = "20YearsOfTEW" #password
        if self.backend == 'sqlite':
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        elif self.backend == 'access':
            if pyodbc is None:
                raise ImportError('pyodbc is required for Access/MDB support')
        else:
            raise ValueError('Unsupported backend: ' + str(backend))

    def get_connection(self):
        """
        Get a database connection for the configured backend.

        Returns:
            sqlite3.Connection or pyodbc.Connection: Connection object for SQLite or Access.
        Raises:
            ValueError: If backend is not supported.
        """
        if self.backend == 'sqlite':
            return sqlite3.connect(self.db_path)
        elif self.backend == 'access':
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={self.db_path};'
            )
            if self.password:
                conn_str += f'PWD={self.password};'
            return pyodbc.connect(conn_str)
        else:
            raise ValueError('Unsupported backend: ' + str(self.backend))

    def close_connection(self, conn):
        """
        Close the given database connection.

        Args:
            conn: The database connection object to close.
        """
        if conn:
            conn.close()

    def backup_db(self, subfolder):
        """
        Backup the current database file into data/backup/<subfolder>/.

        Args:
            subfolder (str): Subfolder name under data/backup/.
        Returns:
            str: Path to the backup file created.
        """
        import shutil
        from datetime import datetime
        backup_dir = os.path.join('data', 'backup', subfolder)
        os.makedirs(backup_dir, exist_ok=True)
        base_name = os.path.basename(self.db_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'{base_name}.{timestamp}.bak')
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def init_db(self):
        """
        Initialize the database with a default users table (for SQLite only).
        """
        if self.backend == 'sqlite':
            """
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    )
                ")
                #conn.commit()
            """
        elif self.backend == 'access':
            pass


