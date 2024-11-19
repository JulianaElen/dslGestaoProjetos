import cmd
import pandas as pd
import csv
import os
from tabulate import tabulate
from fpdf import FPDF
import re

class DSL_interpreter(cmd.Cmd):
    intro="Bem-vindo à interface de linha de comando da DSL para Gestão de Projetos. Digite 'help' ou '?' para listar os comandos.\n"

    def __init__(self):
        super().__init__()
        self.current_project = None
        self.current_task_file = None
        self.command_count = 1
        self.prompt = f"1 > "

    def precmd(self, line):
        self.command_count += 1
        self.prompt = f"{self.command_count} > "
        return line

if __name__ == "__main__":
    DSL_interpreter().cmdloop()