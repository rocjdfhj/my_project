import tkinter as tk
import typing


class Autocomplete(tk.Entry):

    def __init__(self, symbols: typing.List[str], *args, **kwargs):

        """
        Initializes a new instance of the class. The function takes a list of symbols
        and arbitrary arguments and keyword arguments. It creates an instance of the parent
        class using the arbitrary arguments and keyword arguments. It initializes the symbols
        instance variable with the symbols passed. It creates an instance of tkinter's Listbox
        and initializes the _lb_open instance variable to False to keep track of whether
        the Listbox is open or not. It binds the _up_down method to the "<Up>" and "<Down>"
        keys and binds the _select method to the "<Right>" key. Finally, it creates an instance
        of tkinter's StringVar and links it to the tk.Entry content. It also sets a trace on the
        instance variable so that the _changed method is called when the variable value changes.
        """

        super().__init__(*args, **kwargs)

        self._symbols = symbols

        self._lb: tk.Listbox
        self._lb_open = False  # Used to know whether the Listbox is already open or not

        self.bind("<Up>", self._up_down)
        self.bind("<Down>", self._up_down)
        self.bind("<Right>", self._select)

        self._var = tk.StringVar()
        self.configure(textvariable=self._var)  # Links the tk.Entry content to a StringVar()
        self._var.trace("w", self._changed)  # When the self._var value changes



    def _changed(self, var_name: str, index: str, mode: str):
        """
        A method that handles changes to the tk.Entry widget. It sets the content of the widget to uppercase as
        the user types, closes the Listbox when the widget is empty, and displays up to 8 symbols that start with the
        characters typed in the widget in a Listbox. If no matches are found, the Listbox is closed if it was open.
        
        :param var_name: A string representing the name of a variable.
        :param index: A string representing an index.
        :param mode: A string representing the mode of the function.
        :return: None
        """

        

        self._var.set(self._var.get().upper())  # Set the content of the tk.Entry widget to uppercase as you type

        if self._var.get() == "":  # Closes the Listbox when the tk.Entry is empty
            if self._lb_open:
                self._lb.destroy()
                self._lb_open = False
        else:
            if not self._lb_open:
                self._lb = tk.Listbox(height=8)  # Limits the number of items displayed in the Listbox
                self._lb.place(x=self.winfo_x() + self.winfo_width(), y=self.winfo_y() + self.winfo_height() + 40)

                self._lb_open = True

            # Finds symbols that start with the characters that was typed in the tk.Entry widget
            symbols_matched = [symbol for symbol in self._symbols if symbol.startswith(self._var.get())]

            if len(symbols_matched) > 0:

                try:
                    self._lb.delete(0, tk.END)
                except tk.TclError:
                    pass

                for symbol in symbols_matched[:8]:  # Takes only the first 8 elements of the list to match the Listbox
                    self._lb.insert(tk.END, symbol)

            else:  # If no match, closes the Listbox if it was open
                if self._lb_open:
                    self._lb.destroy()
                    self._lb_open = False

    def _select(self, event: tk.Event):
        
        """
    	Selects an item in the listbox and closes the listbox if open.

    	:param event: The tkinter event that triggered the method.
    	"""
        
        if self._lb_open:
            self._var.set(self._lb.get(tk.ACTIVE))
            self._lb.destroy()
            self._lb_open = False
            self.icursor(tk.END)

    def _up_down(self, event: tk.Event):

        """
        Move the Listbox cursor up or down depending on the keyboard key that was pressed.
        :param event:
        :return:
        """

        if self._lb_open:
            if self._lb.curselection() == ():  # No Listbox item selected yet
                index = -1
            else:
                index = self._lb.curselection()[0]

            lb_size = self._lb.size()

            if index > 0 and event.keysym == "Up":
                self._lb.select_clear(first=index)
                index = str(index - 1)
                self._lb.selection_set(first=index)
                self._lb.activate(index)
            elif index < lb_size - 1 and event.keysym == "Down":
                self._lb.select_clear(first=index)
                index = str(index + 1)
                self._lb.selection_set(first=index)
                self._lb.activate(index)
