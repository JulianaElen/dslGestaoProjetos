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
    
    # Obtem o proximo id em um arquivo
    def get_next_id(self, args):
        if not os.path.isfile(args):
            return 1
        try:
            data = pd.read_csv(args)
            if not data.empty:
                return data['id'].max() + 1
            else:
                return 1
        except Exception as e:
            print(f"Erro ao ler o arquivo '{args}': {e}")
            return 1
        
    # gera um novo arquivo cmd
    def generate_file(self, file_type, project_id=None):
        if file_type == "project":
            file_name = "projects.csv"
            columns = ["id", "nome", "creation_date"]
        elif file_type == "tasks":
            if project_id is None:
                print("Erro: O ID do projeto é obrigatório para gerar arquivos de tarefas.")
                return
            file_name = f"tasks{project_id}.csv"
            columns = ["id", "nome", "prazo", "prioridade", "responsavel", "status", "dependencias"]
        else:
            print(f"Erro: Tipo de arquivo desconhecido '{file_type}'.")
            return

        try:
            with open(file_name, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
        except Exception as e:
            print(f"Erro ao criar o arquivo '{file_name}': {e}")

    def add_data_to_file(self, file_name, data):
        try:
            with open(file_name, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                writer.writerow(data)
        except Exception as e:
            print(f"Erro ao adicionar dados ao arquivo '{file_name}': {e}")

    def do_CREATE_PROJECT(self, args):
        'CREATE_PROJECT "<nome>": Criar um novo projeto com o nome especificado.'

        match = re.match(r'^"([^"]+)"$', args.strip())

        if not match:
            print('Erro: Nome do projeto é obrigatório e deve estar entre aspas. Use o comando: CREATE_PROJECT "<nome>".')
            return

        project_name = match.group(1).strip()

        project_id = self.get_next_id("projects.csv")
        creation_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        new_project = {
            "id": project_id,
            "nome": project_name,
            "creation_date": creation_date,
        }

        if not os.path.isfile("projects.csv"):
            self.generate_file("project")

        self.add_data_to_file("projects.csv", new_project)

        self.generate_file("tasks", project_id)

        self.current_project = project_id
        self.current_task_file = f"tasks{project_id}.csv"
        print(f"Projeto '{project_name}' criado com sucesso.")
        print(f"Arquivo de tarefas '{self.current_task_file}' foi criado e definido como o arquivo atual.")

if __name__ == "__main__":
    DSL_interpreter().cmdloop()