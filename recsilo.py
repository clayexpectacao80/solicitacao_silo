import flet as ft
import json
import os
from datetime import datetime
import sqlite3

dados_movimentacoes = []
USUARIOS_FILE = "usuarios.json"
DB_FILE = "usuarios.db"

# Verifica se o arquivo de usuários existe, senão cria um vazio
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w") as f:
        json.dump({}, f)

# Cria a tabela de usuários no banco de dados se não existir
def criar_tabela_usuarios():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT
    )
    """)
    conn.commit()
    conn.close()

# Cria a tabela de movimentações no banco de dados se não existir
def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material TEXT,
        tipo TEXT,
        quantidade INTEGER,
        data TEXT,
        colaborador TEXT,
        lote TEXT,
        status TEXT,
        pagador TEXT,
        recebedor TEXT
    )
    """)
    conn.commit()
    conn.close()

# Função para adicionar movimentação no banco de dados
def adicionar_movimentacao_bd(material, tipo, quantidade, data, colaborador, lote):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO movimentacoes (material, tipo, quantidade, data, colaborador, lote, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (material, tipo, quantidade, data, colaborador, lote, "Pendente de Pagamento"))
    conn.commit()
    conn.close()

# Função para carregar as movimentações
def carregar_movimentacoes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movimentacoes")
    movimentacoes = cursor.fetchall()
    conn.close()
    return movimentacoes

criar_tabela_usuarios()
criar_tabela_movimentacoes()  # Cria a tabela de movimentações

def carregar_usuarios():
    """Carrega os usuários do banco de dados SQLite"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, senha FROM usuarios")
    usuarios = {usuario: senha for usuario, senha in cursor.fetchall()}
    conn.close()
    return usuarios

def salvar_usuarios(usuarios):
    """Salva os usuários no banco de dados SQLite"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for usuario, senha in usuarios.items():
        cursor.execute("INSERT OR REPLACE INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
    conn.commit()
    conn.close()

def adicionar_movimentacao(e, page, material, tipo, quantidade, data, colaborador, lote, tabela):
    # Adicionar a movimentação no banco de dados
    adicionar_movimentacao_bd(material.value, tipo.value, int(quantidade.value), data.value, colaborador.value, lote.value)
   
    # Atualizar a tabela com as movimentações do banco de dados
    atualizar_tabela(page, tabela)
   
    # Limpar os campos
    limpar_campos(material, tipo, quantidade, data, colaborador, lote, page)

def abrir_popup_pagador(e, page, index, tabela):
    """Popup de autenticação para o pagador"""
    def confirmar_pagador(e):
        usuarios = carregar_usuarios()
        pagador = campo_pagador.value
        senha_pagador = campo_senha_pagador.value

        if pagador in usuarios and usuarios[pagador] == senha_pagador:
            # Atualizar status da movimentação no banco de dados para "Pago"
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE movimentacoes SET status = ?, pagador = ? WHERE id = ?",
                           ("Pago", pagador, index))
            conn.commit()
            conn.close()
           
            atualizar_tabela(page, tabela)
            page.dialog.open = False
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    campo_pagador = ft.TextField(label="Usuário (Quem paga)")
    campo_senha_pagador = ft.TextField(label="Senha", password=True)

    popup = ft.AlertDialog(
        title=ft.Text("Autenticação do Pagador"),
        content=ft.Column([campo_pagador, campo_senha_pagador]),
        actions=[ft.TextButton("Confirmar", on_click=confirmar_pagador)]
    )
    page.dialog = popup
    popup.open = True
    page.update()

def abrir_popup_recebedor(e, page, index, tabela):
    """Popup de autenticação para o recebedor"""
    def confirmar_recebedor(e):
        usuarios = carregar_usuarios()
        recebedor = campo_recebedor.value
        senha_recebedor = campo_senha_recebedor.value

        if recebedor in usuarios and usuarios[recebedor] == senha_recebedor:
            # Atualizar status da movimentação no banco de dados para "Recebido"
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE movimentacoes SET status = ?, recebedor = ? WHERE id = ?",
                           ("Recebido", recebedor, index))
            conn.commit()
            conn.close()
           
            atualizar_tabela(page, tabela)
            page.dialog.open = False
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    campo_recebedor = ft.TextField(label="Usuário (Quem recebe)")
    campo_senha_recebedor = ft.TextField(label="Senha", password=True)

    popup = ft.AlertDialog(
        title=ft.Text("Autenticação do Recebedor"),
        content=ft.Column([campo_recebedor, campo_senha_recebedor]),
        actions=[ft.TextButton("Confirmar", on_click=confirmar_recebedor)]
    )
    page.dialog = popup
    popup.open = True
    page.update()

def atualizar_tabela(page, tabela, filtro_lote=""):
    """Atualiza a tabela de movimentações com ou sem filtro de lote"""
    tabela.rows.clear()
    movimentacoes = carregar_movimentacoes()  # Carregar movimentações do banco de dados
    for mov in movimentacoes:
        if filtro_lote and filtro_lote not in mov[6]:
            continue  # Filtra pelo lote, caso o filtro seja preenchido

        status = ft.Text(mov[7], color="green" if mov[7] == "Recebido" else "red")
        tabela.rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(mov[1])),  # material
            ft.DataCell(ft.Text(mov[2])),  # tipo
            ft.DataCell(ft.Text(str(mov[3]))),  # quantidade
            ft.DataCell(ft.Text(mov[4])),  # data
            ft.DataCell(ft.Text(mov[5])),  # colaborador
            ft.DataCell(ft.Text(mov[6])),  # lote
            ft.DataCell(status),
            ft.DataCell(ft.IconButton(ft.icons.CHECK, on_click=lambda e, idx=mov[0]: abrir_popup_pagador(e, page, idx, tabela))),
            ft.DataCell(ft.IconButton(ft.icons.PERSON, on_click=lambda e, idx=mov[0]: abrir_popup_recebedor(e, page, idx, tabela) if mov[7] == "Pago" else None))
        ]))
    page.update()

def limpar_campos(material, tipo, quantidade, data, colaborador, lote, page):
    material.value = ""
    quantidade.value = ""
    data.value = datetime.now().strftime('%d/%m/%Y')
    lote.value = ""
    colaborador.value = None
    tipo.value = None
    page.update()

def pagina_principal(page: ft.Page):
    """Página principal com os inputs e a tabela"""
    page.clean()
    page.title = "Controle de Pagamentos"
    page.window_width = 900
    page.window_height = 700
    page.scroll = ft.ScrollMode.AUTO

    campo_material = ft.TextField(label="Material", width=200)
    dropdown_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Solicitação"), ft.dropdown.Option("Entrada")], width=200)
    campo_quantidade = ft.TextField(label="Quantidade", width=150, keyboard_type="number")
    campo_data = ft.TextField(label="Data", width=150, value=datetime.now().strftime('%d/%m/%Y'))
    dropdown_colaborador = ft.Dropdown(label="Colaborador", options=[ft.dropdown.Option(nome) for nome in ["Clay", "Ricardo", "Helton", "Daltino", "Yeda", "Wellingson", "Lucas", "Samuel", "Adriano"]], width=200)
    campo_lote = ft.TextField(label="Lote", width=150)

    campo_pesquisa_lote = ft.TextField(label="Pesquisar por Lote", width=200)

    tabela = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Material")),
        ft.DataColumn(ft.Text("Tipo")),
        ft.DataColumn(ft.Text("Quantidade")),
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Colaborador")),
        ft.DataColumn(ft.Text("Lote")),
        ft.DataColumn(ft.Text("Status")),
        ft.DataColumn(ft.Text("Pagamento")),
        ft.DataColumn(ft.Text("Recebimento"))
    ])

    def filtrar_por_lote(e):
        filtro_lote = campo_pesquisa_lote.value
        atualizar_tabela(page, tabela, filtro_lote)

    campo_pesquisa_lote.on_change = filtrar_por_lote

    botao_adicionar = ft.ElevatedButton(text="Adicionar", on_click=lambda e: adicionar_movimentacao(e, page, campo_material, dropdown_tipo, campo_quantidade, campo_data, dropdown_colaborador, campo_lote, tabela))

    page.add(
        ft.Column([
            ft.Text("Controle de Pagamentos", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([campo_material, dropdown_tipo, campo_quantidade]),
            ft.Row([campo_data, dropdown_colaborador, campo_lote]),
            ft.Row([botao_adicionar]),
            ft.Row([campo_pesquisa_lote]),
            ft.Text("Movimentações", size=20, weight=ft.FontWeight.BOLD),
            tabela
        ])
    )

    atualizar_tabela(page, tabela)

def login(page: ft.Page):
    """Tela de login"""
    page.clean()
    page.title = "Login"

    campo_usuario = ft.TextField(label="Usuário", width=200)
    campo_senha = ft.TextField(label="Senha", password=True, width=200)

    def verificar_login(e):
        usuarios = carregar_usuarios()
        usuario = campo_usuario.value
        senha = campo_senha.value

        if usuario in usuarios and usuarios[usuario] == senha:
            pagina_principal(page)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha inválidos!", color="red"))
            page.snack_bar.open = True
            page.update()

    def criar_usuario(e):
        usuarios = carregar_usuarios()
        usuario = campo_usuario.value
        senha = campo_senha.value

        if usuario and senha:
            if usuario in usuarios:
                page.snack_bar = ft.SnackBar(ft.Text("Usuário já existe!", color="red"))
            else:
                usuarios[usuario] = senha
                salvar_usuarios(usuarios)
                page.snack_bar = ft.SnackBar(ft.Text("Usuário criado com sucesso!", color="green"))
            page.snack_bar.open = True
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha usuário e senha!", color="red"))
            page.snack_bar.open = True
            page.update()

    botao_login = ft.ElevatedButton(text="Entrar", on_click=verificar_login)
    botao_criar = ft.ElevatedButton(text="Criar Usuário", on_click=criar_usuario)

    page.add(
        ft.Column([
            ft.Text("Login no Sistema", size=24, weight=ft.FontWeight.BOLD),
            campo_usuario,
            campo_senha,
            ft.Row([botao_login, botao_criar])
        ])
    )

def main(page: ft.Page):
    login(page)

ft.app(target=main)