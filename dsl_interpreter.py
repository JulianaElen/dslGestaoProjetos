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

    def do_SELECT(self, args):
        'SELECT "<nome>": Seleciona um projeto existente ( com arquivo de tarefas correspondente).'
        
        match = re.match(r'^"([^"]+)"$', args.strip())

        if not match:
            print('Erro: Nome do projeto é obrigatório e deve estar entre aspas. Use o comando SELECT "<nome>" corretamente.')
            return

        project_name = match.group(1).strip()
        
        try:
            data = pd.read_csv("projects.csv")
        except Exception as e:
            print(f"Erro ao ler o arquivo 'projects.csv': {e}")
            return
        
        projeto = data[data['nome'] == project_name]
        
        if projeto.empty:
            print(f'Erro: Projeto "{project_name}" não existe. Confira os projetos existentes usando LIST_PROJECTS ou crie um novo projeto usando CREATE_PROJECT "<nome>".')
            return
        
        project_id = projeto.iloc[0]['id']
        self.current_task_file = f"tasks{project_id}.csv"
        self.current_project = project_id
        
        print(f"Projeto '{project_name}' selecionado com sucesso. Arquivo de tarefas agora é '{self.current_task_file}'.")

    def do_ADD_TASK(self, args):
        'ADD_TASK "<nome>" "<prazo>" "<prioridade>": Adicionar uma nova tarefa ao projeto atual, com prazo e prioridade.'

        if self.current_project is None:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return

        try:
            matches = re.findall(r'"([^"]+)"', args)
            if len(matches) < 3:
                print('Erro: Os campos "<nome>", "<prazo>" e "<prioridade>" são obrigatórios e devem estar entre aspas.')
                return
            
            nome_tarefa, prazo, prioridade = matches

            tarefa_id = self.get_next_id(self.current_task_file)

            new_task = {
                "id": tarefa_id,
                "nome": nome_tarefa,
                "prazo": prazo,
                "prioridade": prioridade,
                "responsavel": "",
                "status": "Não iniciada",
                "dependencias": "",
            }

            self.add_data_to_file(self.current_task_file, new_task)

            print(f"Tarefa '{nome_tarefa}' adicionada ao projeto '{self.current_project}' com sucesso.")
        
        except Exception as e:
            print(f'Erro ao adicionar tarefa: {e}. Verifique o arquivo de tarefas do projeto e se o projeto foi selecionado da forma correta.')

    def do_ASSIGN(self, args):
        'ASSIGN "tarefa" "responsável": Atribuir um responsável para uma tarefa específica.'
        
        matches = re.findall(r'"([^"]+)"', args)

        if len(matches) < 2:
            print("Erro: Os campos [nome], [prazo], [prioridade] são obrigatórios e devem estar entre aspas.")
            return
        
        nome_tarefa, responsavel = matches

        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return
        
        data = pd.read_csv(self.current_task_file)

        data['responsavel'] = data['responsavel'].astype(str)
        
        if nome_tarefa not in data['nome'].values:
            print(f'Erro: A tarefa "{nome_tarefa}" não foi encontrada na lista de tarefas. Adicione a tarefa usando ADD_TASK "<nome>" "<prazo>" "<prioridade>".')
            return
        
        data.loc[data['nome'] == nome_tarefa, 'responsavel'] = responsavel
        
        data.to_csv(self.current_task_file, index=False)
        
        print(f"Responsável '{responsavel}' atribuído à tarefa '{nome_tarefa}' com sucesso.")

    def do_SET_STATUS(self, args):
        'SET_STATUS "tarefa" "status": Definir o status de uma tarefa (e.g., "em andamento", "concluída").'
        
        matches = re.findall(r'"([^"]+)"', args)
        if len(matches) < 2:
            print("Erro: Os campos [nome], [prazo], [prioridade] são obrigatórios e devem estar entre aspas.")
            return
        
        nome_tarefa, status = matches

        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return
        
        data = pd.read_csv(self.current_task_file)

        data['status'] = data['status'].astype(str)
        
        if nome_tarefa not in data['nome'].values:
            print(f'Erro: A tarefa "{nome_tarefa}" não foi encontrada na lista de tarefas. Adicione a tarefa usando ADD_TASK "<nome>" "<prazo>" "<prioridade>".')
            return
        
        data.loc[data['nome'] == nome_tarefa, 'status'] = status
        
        data.to_csv(self.current_task_file, index=False)
        
        print(f"Status da tarefa '{nome_tarefa}' atualizado para '{status}'.")

    def do_LIST_TASKS(self, arg):
        'LIST_TASKS "filtro": Lista tarefas do projeto com base em um filtro específico ou exibe todas se nenhum filtro for fornecido.'
       
        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return

        try:
            data = pd.read_csv(self.current_task_file)

            if arg:
                filter_condition = arg.strip().strip('"').strip("'")

                match = re.match(r'(\w+)\s*(==|!=)\s*(.+)', filter_condition)
                if not match:
                    raise ValueError('Erro no comando. Use LIST_TASKS "coluna == ou != \'valor\'".')

                column, operator, value = match.groups()

                value = value.strip().strip('"').strip("'")

                if column not in data.columns:
                    raise ValueError(f"A coluna '{column}' não existe no arquivo de tarefas.")

                if operator == "==":
                    data = data[data[column] == value]
                elif operator == "!=":
                    data = data[data[column] != value]

            else:
                print("Exibindo todas as tarefas do projeto.")

            if not data.empty:
                headers = ["ID", "Nome", "Prazo", "Prioridade", "Responsável", "Status", "Dependências"]
                print(tabulate(data, headers=headers, tablefmt="fancy_grid"))
            else:
                print("Nenhuma tarefa encontrada com o filtro especificado.")

        except ValueError as ve:
            print(f"Erro no filtro: {ve}")
        except Exception as e:
            print(f"Erro ao listar as tarefas: {e}")

    def do_REMOVE_TASK(self, args):
        'REMOVE_TASK "<nome>": Remover uma tarefa do projeto.'
        
        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return
        
        match = re.match(r'^"([^"]+)"$', args.strip())
        if not match:
            print('Erro: O nome da tarefa deve ser especificado entre aspas, por exemplo, REMOVE_TASK "nome_da_tarefa".')
            return

        nome_tarefa = match.group(1)
        data = pd.read_csv(self.current_task_file, encoding="utf-8")
        
        if nome_tarefa not in data['nome'].values:
            print(f"Erro: Tarefa '{nome_tarefa}' não encontrada.")
            return
        
        data = data[data['nome'] != nome_tarefa]
        
        data.to_csv(self.current_task_file, index=False)
        
        print(f"Tarefa '{nome_tarefa}' apagada. Use LIST_TASKS para conferir.")

    def do_ADD_DEPENDENCY(self, args):
        'ADD_DEPENDENCY "<tarefa>" "<tarefa_dependente>": Adicionar uma dependência entre tarefas.'

        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return

        matches = re.findall(r'"([^"]+)"', args)
        if len(matches) < 2:
            print('Erro: Os campos "<tarefa>" e "<tarefa_dependente>" são obrigatórios e devem estar entre aspas.')
            return

        tarefa, tarefa_dependente = matches

        try:
            data = pd.read_csv(self.current_task_file, encoding="utf-8")

            if 'dependencias' in data.columns:
                data['dependencias'] = data['dependencias'].astype(str).fillna('')

            if tarefa not in data['nome'].values:
                print(f"Erro: Tarefa '{tarefa}' não encontrada.")
                return
            if tarefa_dependente not in data['nome'].values:
                print(f"Erro: Tarefa dependente '{tarefa_dependente}' não encontrada.")
                return

            tarefa_idx = data[data['nome'] == tarefa].index[0]

            dependencias_atual = data.at[tarefa_idx, 'dependencias']

            dependencias_lista = dependencias_atual.split() if dependencias_atual else []
            if tarefa_dependente not in dependencias_lista:
                dependencias_lista.append(tarefa_dependente)
                data.at[tarefa_idx, 'dependencias'] = " ".join(dependencias_lista)

            data.to_csv(self.current_task_file, index=False, encoding="utf-8")
            
            print(f"Dependência entre '{tarefa}' e '{tarefa_dependente}' adicionada com sucesso.")

        except Exception as e:
            print(f"Erro ao adicionar dependência: {e}")

    def do_EXPORT(self, args):
        'EXPORT_REPORT "<formato>" "<caminho>": Exportar um relatório do projeto em PDF ou CSV.'
        
        matches = re.findall(r'"([^"]+)"', args)
        if len(matches) < 2:
            print('Erro: Os campos "<formato>" e "<caminho>" são obrigatórios e devem estar entre aspas.')
            return

        formato, caminho = matches
        formato = formato.lower()
        
        if formato not in ['pdf', 'csv']:
            print("Erro: Formato inválido. Escolha entre 'pdf' ou 'csv'.")
            return
        
        if not self.current_project:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return
        
        try:
            data = pd.read_csv(self.current_task_file, encoding="utf-8")
            
            if data.empty:
                print("Erro: Não há tarefas no projeto para exportar.")
                return
            
            if formato == 'csv':

                data.to_csv(caminho, index=False)
                print(f"Relatório exportado para {caminho} no formato CSV.")
            
            elif formato == 'pdf':

                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font('Arial', 'B', 12)
                

                pdf.cell(200, 10, txt="Relatório de Tarefas", ln=True, align='C')
                pdf.ln(10)

                pdf.set_font('Arial', 'B', 10)
                headers = ["ID", "Nome", "Status", "Prioridade"]
                header_line = " | ".join(headers)
                pdf.cell(200, 10, txt=header_line, ln=True)

                pdf.set_font('Arial', '', 10)
                for _, row in data.iterrows():
                    tarefa_info = f"{row['id']} | {row['nome']} | {row['status']} | {row['prioridade']}"
                    pdf.cell(200, 10, txt=tarefa_info, ln=True)
                
                pdf.output(caminho)
                print(f"Relatório exportado para {caminho} no formato PDF.")

        except FileNotFoundError:
            print(f"Erro: Arquivo de tarefas '{self.current_task_file}' não encontrado.")
        except PermissionError:
            print(f"Erro: Permissão negada para salvar em '{caminho}'. Verifique as permissões.")
        except Exception as e:
            print(f"Erro ao exportar relatório: {e}")

    def do_UPDATE(self, arg):
        'UPDATE "<coluna>" "<novo_valor>" WHERE ID "<id>": Atualiza valores em uma coluna com base em uma condição.'
        
        matches = re.findall(r'"([^"]+)"', arg)
        
        if len(matches) != 3:
            print('Erro: O formato correto é "<coluna>" "<novo_valor>" WHERE ID "<id>".')
            return
        
        coluna, novo_valor, tarefa_id = matches
        
        if not tarefa_id.isdigit():
            print("Erro: O ID da tarefa deve ser um número.")
            return
        
        tarefa_id = int(tarefa_id)
        
        if not self.current_project or not self.current_task_file:
            print('Erro: Nenhum projeto selecionado. Use o comando SELECT "<nome>" para selecionar um projeto.')
            return
        
        try:
            data = pd.read_csv(self.current_task_file, encoding="utf-8")
        except FileNotFoundError:
            print(f"Erro: O arquivo de tarefas '{self.current_task_file}' não foi encontrado.")
            return
        except pd.errors.EmptyDataError:
            print("Erro: O arquivo de tarefas está vazio.")
            return
        
        if coluna not in data.columns:
            print(f"Erro: A coluna '{coluna}' não existe.")
            return
        
        if tarefa_id not in data['id'].values:
            print(f"Erro: Tarefa com ID {tarefa_id} não encontrada.")
            return

        data.loc[data['id'] == tarefa_id, coluna] = novo_valor
        
        try:
            data.to_csv(self.current_task_file, index=False)
            print(f"Valor da coluna '{coluna}' atualizado para '{novo_valor}' na tarefa ID {tarefa_id}.")
        except Exception as e:
            print(f"Erro ao salvar o arquivo de tarefas: {e}")

    def do_LIST_PROJECTS(self, args):
        'SHOW_PROJECTS: Exibir todos os projetos existentes em formato tabular.'
        
        if not os.path.isfile("projects.csv"):
            print("Nenhum projeto encontrado.")
            return

        data = pd.read_csv("projects.csv")
        print("Projetos existentes:")
        print(tabulate(data, headers="keys", tablefmt="fancy_grid", showindex=False))

    def do_EXIT(self, arg):
        'EXIT: Sai da interface de linha de comando.'
        print("Saindo da interface DSL.")
        return True       

if __name__ == "__main__":
    DSL_interpreter().cmdloop()