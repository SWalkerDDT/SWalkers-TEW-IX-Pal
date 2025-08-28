from typing import List, Dict, Any, Optional

def get_column_names(db, table: str) -> list:
    """
    Get all column names for the given table (works for SQLite and Access).

    Args:
        db: Database instance.
        table (str): Name of the table.

    Returns:
        list: List of column names.
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(f"PRAGMA table_info({table})")
            rows = cur.fetchall()
            if rows:
                return [row[1] for row in rows]
        except Exception:
            pass
        cur.execute(f"SELECT * FROM {table} WHERE 1=0")
        return [desc[0] for desc in cur.description]
    finally:
        db.close_connection(conn)

def insert(db, table: str, data: Dict[str, Any]) -> int:
    """
    Insert a row into the given table.

    Args:
        db: Database instance.
        table (str): Name of the table.
        data (dict): Dictionary of column-value pairs to insert.

    Returns:
        int: The last row id of the inserted row.
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        cur.execute(sql, tuple(data.values()))
        conn.commit()
        return cur.lastrowid
    finally:
        db.close_connection(conn)

def select(db, table: str, columns: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> list:
    """
    Select rows from the given table with optional columns and where condition.

    Args:
        db: Database instance.
        table (str): Name of the table.
        columns (list, optional): List of columns to select. Selects all if None.
        where (dict, optional): Dictionary of column-value pairs for WHERE clause.

    Returns:
        list: List of rows (tuples).
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cols = ", ".join(columns) if columns else "*"
        sql = f"SELECT {cols} FROM {table}"
        params = []
        if where:
            conditions = " AND ".join(f"{k}=?" for k in where)
            sql += f" WHERE {conditions}"
            params = list(where.values())
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        db.close_connection(conn)

def update(db, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
    """
    Update rows in the given table.

    Args:
        db: Database instance.
        table (str): Name of the table.
        data (dict): Dictionary of column-value pairs to update.
        where (dict): Dictionary of column-value pairs for WHERE clause.

    Returns:
        int: Number of rows updated.
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        set_clause = ", ".join(f"{k}=?" for k in data)
        where_clause = " AND ".join(f"{k}=?" for k in where)
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        cur.execute(sql, tuple(data.values()) + tuple(where.values()))
        conn.commit()
        return cur.rowcount
    finally:
        db.close_connection(conn)

def delete(db, table: str, where: Dict[str, Any]) -> int:
    """
    Delete rows from the given table.

    Args:
        db: Database instance.
        table (str): Name of the table.
        where (dict): Dictionary of column-value pairs for WHERE clause.

    Returns:
        int: Number of rows deleted.
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        where_clause = " AND ".join(f"{k}=?" for k in where)
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        cur.execute(sql, tuple(where.values()))
        conn.commit()
        return cur.rowcount
    finally:
        db.close_connection(conn)

def get_table_names(db) -> list:
    """
    Get all table names in the database (works for SQLite and Access).

    Args:
        db: Database instance.

    Returns:
        list: List of table names.
    """
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
        except Exception:
            cur.tables()
            tables = [row.table_name for row in cur.fetchall() if row.table_type == 'TABLE']
        return tables
    finally:
        db.close_connection(conn)
