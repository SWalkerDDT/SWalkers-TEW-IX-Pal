import tkinter as tk
from tkinter import ttk
from models.crud import update, select
import re

class ExtendedTreeview(ttk.Treeview):
    """
    An extended Treeview widget with optional editable cells, draggable rows, column sorting, and a search bar.

    Args:
        parent: Parent widget.
        editable (bool): If True, cells are editable on double-click.
        draggable (bool): If True, rows can be reordered by drag-and-drop.
        db: Database instance for committing edits.
        table (str): Table name for committing edits.
        primary_key (str or list): Primary key column name(s) for identifying rows.
        searchbar (bool): If True, a search input and button are placed under the treeview.
        **kwargs: Additional ttk.Treeview options.
    """
    def __init__(self, parent, editable=False, draggable=False, db=None, table=None, primary_key=None, searchbar=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.editable = editable
        self.draggable = draggable
        self.db = db
        self.table = table
        self.primary_key = primary_key
        self._edit_entry = None
        self._sort_column = None
        self._sort_reverse = False
        self.searchbar = searchbar
        self._search_frame = None
        self._search_entry = None
        self._search_button = None
        self._parent = parent

        if self.editable:
            self.bind("<Double-1>", self._on_double_click)
        if self.draggable:
            self.bind("<ButtonPress-1>", self._on_drag_start)
            self.bind("<B1-Motion>", self._on_drag_motion)
            self.bind("<ButtonRelease-1>", self._on_drag_drop)
            self._dragging_item = None
        for col in self['columns']:
            self.heading(col, command=lambda c=col: self._sort_by_column(c))
        if self.searchbar:
            self._add_searchbar()

    def pack(self, *args, **kwargs):
        """
        Pack the Treeview and, if enabled, the search bar below it.
        """
        super().pack(*args, **kwargs)
        if self.searchbar and self._search_frame:
            self._search_frame.pack(pady=5)

    def destroy(self):
        """
        Destroy the Treeview and its search bar if present.
        """
        if self.searchbar and self._search_frame:
            self._search_frame.destroy()
        return super().destroy()

    def _add_searchbar(self):
        """
        Create the search bar widgets but do not pack them.
        """
        self._search_frame = tk.Frame(self._parent)
        self._search_entry = tk.Entry(self._search_frame, width=60)
        self._search_entry.pack(side='left', padx=5)
        self._search_button = tk.Button(self._search_frame, text='Search', command=self._on_search)
        self._search_button.pack(side='left', padx=5)

    def _on_search(self):
        """
        Handle the search button click, parse the query, and update the Treeview with filtered results.
        """
        query = self._search_entry.get()
        where = self._parse_search_query(query)
        for item in self.get_children():
            self.delete(item)
        if self.db and self.table:
            columns = self['columns']
            results = []
            if isinstance(where, list):
                for clause in where:
                    rows = select(self.db, self.table, columns=columns, where=clause)
                    results.extend(rows)
                seen = set()
                unique_results = []
                for row in results:
                    t = tuple(row)
                    if t not in seen:
                        seen.add(t)
                        unique_results.append(row)
                results = unique_results
            elif isinstance(where, dict):
                results = select(self.db, self.table, columns=columns, where=where)
            else:
                results = select(self.db, self.table, columns=columns)
            for row in results:
                self.insert('', 'end', values=tuple(row))

    def _parse_search_query(self, query):
        """
        Parse the search query string into a where clause for the select function.

        Args:
            query (str): The search query string, e.g. "Name='John' AND Age='30' OR City='NY'".

        Returns:
            dict or list: A dict for AND, or a list of dicts for OR. None if query is empty.
        """
        if not query.strip():
            return None
        or_parts = [part.strip() for part in re.split(r'\bOR\b', query, flags=re.IGNORECASE)]
        where_clauses = []
        for part in or_parts:
            and_parts = [p.strip() for p in re.split(r'\bAND\b', part, flags=re.IGNORECASE)]
            clause = {}
            for cond in and_parts:
                m = re.match(r"(\w+)\s*=\s*'([^']*)'", cond)
                if m:
                    col, val = m.groups()
                    clause[col] = val
            if clause:
                where_clauses.append(clause)
        if len(where_clauses) == 1:
            return where_clauses[0]
        elif len(where_clauses) > 1:
            return where_clauses
        return None

    def _on_double_click(self, event):
        """
        Handle double-click event to make a cell editable.
        """
        region = self.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.identify_row(event.y)
        col = self.identify_column(event.x)
        if not row_id or not col:
            return
        x, y, width, height = self.bbox(row_id, col)
        value = self.set(row_id, col)
        self._edit_entry = tk.Entry(self)
        self._edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_entry.insert(0, value)
        self._edit_entry.focus()
        self._edit_entry.bind("<Return>", lambda e: self._save_edit(row_id, col))
        self._edit_entry.bind("<FocusOut>", lambda e: self._save_edit(row_id, col))

    def _save_edit(self, row_id, col):
        """
        Save the edited cell value and update the database if configured.

        Args:
            row_id: The item ID of the row being edited.
            col: The column identifier (e.g., '#2').
        """
        new_value = self._edit_entry.get()
        self.set(row_id, col, new_value)
        self._edit_entry.destroy()
        self._edit_entry = None
        if self.db and self.table and self.primary_key:
            self._commit_edit_to_db(row_id, col, new_value)

    def _commit_edit_to_db(self, row_id, col, new_value):
        """
        Commit the edited cell value to the database.

        Args:
            row_id: The item ID of the row being edited.
            col: The column identifier (e.g., '#2').
            new_value: The new value to set.
        """
        col_index = int(col.replace('#', '')) - 1
        columns = self['columns']
        col_name = columns[col_index]
        row_values = self.item(row_id, 'values')
        if isinstance(self.primary_key, (list, tuple)):
            where = {k: row_values[columns.index(k)] for k in self.primary_key}
        else:
            where = {self.primary_key: row_values[columns.index(self.primary_key)]}
        data = {col_name: new_value}
        update(self.db, self.table, data, where)

    def _on_drag_start(self, event):
        """
        Handle the start of a row drag event.
        """
        row_id = self.identify_row(event.y)
        if row_id:
            self._dragging_item = row_id

    def _on_drag_motion(self, event):
        """
        Handle the row being dragged over another row.
        """
        if not self._dragging_item:
            return
        row_id = self.identify_row(event.y)
        if row_id and row_id != self._dragging_item:
            self.selection_set(row_id)

    def _on_drag_drop(self, event):
        """
        Handle dropping a dragged row to reorder.
        """
        if not self._dragging_item:
            return
        target_id = self.identify_row(event.y)
        if target_id and target_id != self._dragging_item:
            item_data = self.item(self._dragging_item)
            children = self.get_children("")
            idx = children.index(target_id)
            self.move(self._dragging_item, '', idx)
        self._dragging_item = None

    def _sort_by_column(self, col):
        """
        Sort the Treeview by the given column, toggling ascending/descending order.

        Args:
            col: The column name to sort by.
        """
        data = [(self.set(k, col), k) for k in self.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=self._sort_column == col and not self._sort_reverse)
        except Exception:
            data.sort(key=lambda t: t[0], reverse=self._sort_column == col and not self._sort_reverse)
        for index, (val, k) in enumerate(data):
            self.move(k, '', index)
        if self._sort_column == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col
            self._sort_reverse = False
