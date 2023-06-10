import sqlite3
import typing

class WorkspaceData:
    def __init__(self):
        self.cnt = sqlite3.connect("database.db")
        self.cnt.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self.pointer = self.cnt.cursor()
        self.pointer.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT)")
        self.pointer.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT,"
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self.cnt.commit()  # Saves the changes

    def save(self, table: str, data: typing.List[typing.Tuple]):
        """
        Erase the previous table content and record new data to it.
        :param table: The table name
        :param data: A list of tuples, the tuples elements must be ordered like the table columns
        :return:
        """
        self.pointer.execute(f"DELETE FROM {table}")

        table_data = self.pointer.execute(f"SELECT * FROM {table}")

        columns = [description[0] for description in table_data.description]  # Lists the columns of the table

        # Creates the SQL insert statement dynamically
        sql_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
        self.pointer.executemany(sql_statement, data)
        self.cnt.commit()

    def get(self, table: str) -> typing.List[sqlite3.Row]:
        """
        Get all the rows recorded for the table.
        :param table: The table name to get the rows from. e.g: strategies, watchlist
        :return: A list of sqlite3.Rows accessible like Python dictionaries.
        """
        self.pointer.execute(f"SELECT * FROM {table}")
        data = self.pointer.fetchall()
        return data
