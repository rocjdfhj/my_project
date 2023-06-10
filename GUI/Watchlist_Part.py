import tkinter as tk
from turtle import width
import typing

from tblib import Frame

from Exchange_Data import *

from GUI.Styles import *
from GUI.Autocompletion import Autocomplete
from GUI.Scrollable import ScrollableFrame

from Database import WorkspaceData


class Watchlist(tk.Frame):
    def __init__(self, contracts: typing.Dict[str, ContractData], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = WorkspaceData()
        self.symbols_list = list(contracts.keys())

        self._commands_frame = tk.Frame(self, bg=BACKGROUND)
        self._commands_frame.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self, bg=BACKGROUND)
        self._table_frame.pack(side=tk.TOP)

        self._binance_label = tk.Label(
            self._commands_frame, text="Binance", bg=BACKGROUND, fg=FOREGROUND, font=BOLD_FONT)
        self._binance_label.grid(row=0, column=0)
        self._binance_entry = Autocomplete(self.symbols_list, self._commands_frame, fg=FOREGROUND, justify=tk.CENTER,
                                           insertbackground=FOREGROUND, bg=BACKGROUND_2, highlightthickness=1,highlightbackground = "white")
        self._binance_entry.bind("<Return>", self._add_binance_symbol)
        self._binance_entry.grid(row=1, column=0, padx=5)

        self.body_widgets = dict()

        self._headers = ["symbol", "bid", "ask", "remove"]
        self._headers_frame = tk.Frame(self._table_frame, bg=BACKGROUND)

        self._col_width = 13

        # Creates the headers dynamically

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._headers_frame, text=h.capitalize() if h != "remove" else "", bg=BACKGROUND,
                              fg=FOREGROUND, font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)
        header = tk.Label(self._headers_frame, text="", bg=BACKGROUND,
                          fg=FOREGROUND, font=GLOBAL_FONT, width=3)
        header.grid(row=0, column=len(self._headers))
        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        # Creates the table body
        self._body_frame = ScrollableFrame(
            self._table_frame, bg=BACKGROUND, height=250)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        # Add keys to the body_widgets dictionary, the keys represents columns or data related to a column
        # You could also have another logic: instead of body_widgets[column][row] have body_widgets[row][column]

        for h in self._headers:
            self.body_widgets[h] = dict()
            if h in ["bid", "ask"]:
                self.body_widgets[h + "_var"] = dict()
        self._body_index = 0

        # Loads the Watchlist symbols saved to the database during a previous session

        previous_saved_symbols = self.db.get("watchlist")
        for s in previous_saved_symbols:
            self._add_symbol(s['symbol'])

    def _remove_symbol(self, b_index: int):
        for h in self._headers:
            self.body_widgets[h][b_index].grid_forget()
            del self.body_widgets[h][b_index]

    def _add_binance_symbol(self, event):
        symbol = event.widget.get()
        if symbol in self.symbols_list:
            self._add_symbol(symbol)
            event.widget.delete(0, tk.END)

    def _add_symbol(self, symbol: str):
        b_index = self._body_index
        self.body_widgets['symbol'][b_index] = tk.Label(self._body_frame.sub_frame, text=symbol, bg=BACKGROUND,
                                                        fg=FOREGROUND_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['symbol'][b_index].grid(row=b_index, column=0)


        self.body_widgets['bid_var'][b_index] = tk.StringVar()
        self.body_widgets['bid'][b_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['bid_var'][b_index],
                                                     bg=BACKGROUND, fg=FOREGROUND_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['bid'][b_index].grid(row=b_index, column=1)


        self.body_widgets['ask_var'][b_index] = tk.StringVar()
        self.body_widgets['ask'][b_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['ask_var'][b_index],
                                                     bg=BACKGROUND, fg=FOREGROUND_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['ask'][b_index].grid(row=b_index, column=2)


        self.body_widgets['remove'][b_index] = tk.Button(self._body_frame.sub_frame, text="X",
                                                         bg="darkred", fg=FOREGROUND, font=GLOBAL_FONT,
                                                         command=lambda: self._remove_symbol(b_index), width=4)
        self.body_widgets['remove'][b_index].grid(row=b_index, column=3)
        self._body_index += 1
