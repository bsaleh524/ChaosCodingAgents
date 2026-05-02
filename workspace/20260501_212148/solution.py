# solution.py

import tkinter as tk
import random
from typing import Protocol


class NumberSource(Protocol):
    def get_value(self) -> int:
        ...


class FixedNumberSource:
    def __init__(self, value: int) -> None:
        self._value = value

    def get_value(self) -> int:
        return self._value


class RandomNumberSource:
    def __init__(self, low: int = 1, high: int = 100) -> None:
        self._low = low
        self._high = high

    def get_value(self) -> int:
        return random.randint(self._low, self._high)


class CalculatorModel:
    def __init__(self) -> None:
        self._total: int = 0

    def add(self, source: NumberSource) -> int:
        self._total += source.get_value()
        return self._total

    def reset(self) -> int:
        self._total = 0
        return self._total

    @property
    def total(self) -> int:
        return self._total


class CalculatorView(tk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padx=16, pady=16, bg="#1e1e2e")
        master.title("Addition Calculator")
        master.resizable(False, False)
        self._build_widgets()

    def _build_widgets(self) -> None:
        style = {
            "bg": "#1e1e2e",
            "fg": "#cdd6f4",
            "font": ("Courier New", 13),
        }
        btn_style = {
            "bg": "#313244",
            "fg": "#cdd6f4",
            "activebackground": "#45475a",
            "activeforeground": "#cdd6f4",
            "relief": tk.FLAT,
            "font": ("Courier New", 12, "bold"),
            "cursor": "hand2",
            "pady": 6,
        }

        self.total_var = tk.StringVar(value="Total: 0")
        self.status_var = tk.StringVar(value="")

        tk.Label(self, textvariable=self.total_var, **style,
                 font=("Courier New", 18, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 10))

        tk.Label(self, text="Enter number:", **style).grid(
            row=1, column=0, sticky="e", padx=(0, 6))

        self.entry = tk.Entry(self, width=10,
                              bg="#313244", fg="#cdd6f4",
                              insertbackground="#cdd6f4",
                              font=("Courier New", 13),
                              relief=tk.FLAT)
        self.entry.grid(row=1, column=1, padx=4)

        self.btn_add = tk.Button(self, text="Add", width=8, **btn_style)
        self.btn_add.grid(row=1, column=2, padx=(6, 0))

        self.btn_random = tk.Button(self, text="+ Random (1–100)",
                                    width=22, **btn_style)
        self.btn_random.grid(row=2, column=0, columnspan=3, pady=(10, 4))

        self.btn_reset = tk.Button(self, text="Reset",
                                   width=22, **btn_style,
                                   fg="#f38ba8")
        self.btn_reset.grid(row=3, column=0, columnspan=3, pady=(0, 8))

        tk.Label(self, textvariable=self.status_var,
                 **style, fg="#a6e3a1",
                 font=("Courier New", 11)).grid(
            row=4, column=0, columnspan=3)

    def get_entry_value(self) -> str:
        return self.entry.get().strip()

    def clear_entry(self) -> None:
        self.entry.delete(0, tk.END)

    def set_total(self, value: int) -> None:
        self.total_var.set(f"Total: {value}")

    def set_status(self, message: str) -> None:
        self.status_var.set(message)


class CalculatorController:
    def __init__(self, model: CalculatorModel, view: CalculatorView) -> None:
        self._model = model
        self._view = view
        self._bind_events()

    def _bind_events(self) -> None:
        self._view.btn_add.config(command=self._handle_add_fixed)
        self._view.btn_random.config(command=self._handle_add_random)
        self._view.btn_reset.config(command=self._handle_reset)
        self._view.entry.bind("<Return>", lambda _: self._handle_add_fixed())

    def _handle_add_fixed(self) -> None:
        raw = self._view.get_entry_value()
        try:
            value = int(raw)
        except ValueError:
            self._view.set_status(f"'{raw}' is not a valid integer.")
            return

        source = FixedNumberSource(value)
        total = self._model.add(source)
        self._view.set_total(total)
        self._view.set_status(f"Added {value}.")
        self._view.clear_entry()

    def _handle_add_random(self) -> None:
        source = RandomNumberSource(1, 100)
        value = source.get_value()
        total = self._model.add(FixedNumberSource(value))
        self._view.set_total(total)
        self._view.set_status(f"Added random value: {value}.")

    def _handle_reset(self) -> None:
        total = self._model.reset()
        self._view.set_total(total)
        self._view.set_status("Calculator reset.")
        self._view.clear_entry()


def main() -> None:
    root = tk.Tk()
    model = CalculatorModel()
    view = CalculatorView(root)
    view.pack()
    CalculatorController(model, view)
    root.mainloop()


if __name__ == "__main__":
    main()