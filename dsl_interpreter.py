import cmd
import pandas as pd
import csv
import os
from tabulate import tabulate
from fpdf import FPDF
import re

class DSL_interpreter(cmd.Cmd):
    intro="Bem-vindo à interface de linha de comando da DSL para Gestão de Projetos. Digite 'help' ou '?' para listar os comandos.\n"

if __name__ == "__main__":
    DSL_interpreter().cmdloop()