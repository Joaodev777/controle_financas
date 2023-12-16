from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

app = Flask(__name__)

# Conexão com o banco de dados SQLite
conn = sqlite3.connect('controle_financeiro.db', check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas se não existirem
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor REAL NOT NULL,
        referente TEXT NOT NULL,
        observacao TEXT NOT NULL,
        tipo TEXT NOT NULL,
        dia_referente DATE NOT NULL -- Adicionando a coluna para armazenar a data
    )
''')

# Criação da tabela "apagados" se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS apagados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor REAL NOT NULL,
        referente TEXT NOT NULL,
        observacao TEXT NOT NULL,
        tipo TEXT NOT NULL,
        dia_referente DATE NOT NULL
    )
''')



# Rota principal com filtro
@app.route('/', methods=['GET'])
def index():
    # Obter parâmetros do filtro
    tipo = request.args.get('tipo', 'all')
    referente = request.args.get('referente', '')
    nome = request.args.get('nome', '')
    valor = request.args.get('valor', '')
    dia_referente = request.args.get('dia_referente', '')
    observacao = request.args.get('observacao', '')

    # Construir a query SQL base
    query = "SELECT * FROM transacoes WHERE 1=1"

    # Adicionar condições ao filtro
    if tipo != 'all':
        query += f" AND tipo = '{tipo}'"
    if referente:
        query += f" AND referente LIKE '%{referente}%'"
    if nome:
        query += f" AND nome LIKE '%{nome}%'"
    if valor:
        query += f" AND valor = {float(valor)}"
    if dia_referente:
        query += f" AND dia_referente = '{dia_referente}'"
    if observacao:
        query += f" AND observacao LIKE '%{observacao}%'"
    
    # Adicionando a condição para o tipo "Anotação"
    if tipo == 'anotacao':
        query += " AND tipo = 'Anotação'"

    # Executar a query no banco de dados
    cursor.execute(query)
    transacoes = cursor.fetchall()


    # Consulta para obter transações do tipo "Receita"
    cursor.execute("SELECT * FROM transacoes WHERE tipo = 'Receita'")
    receitas = cursor.fetchall()

    # Consulta para obter transações do tipo "Despesa"
    cursor.execute("SELECT * FROM transacoes WHERE tipo = 'Despesa'")
    despesas = cursor.fetchall()
    
    # Consulta para obter transações do tipo "Anotação"
    cursor.execute("SELECT * FROM transacoes WHERE tipo = 'Anotação'")
    anotacoes = cursor.fetchall()

# Consulta para obter transações apagadas
    cursor.execute("SELECT * FROM apagados")
    transacoes_apagadas = cursor.fetchall()

    # Calcular o valor total das receitas
    valor_total_receitas = sum(receita[2] for receita in receitas)

    # Calcular o valor total das despesas
    valor_total_despesas = sum(despesa[2] for despesa in despesas)

    # Calcular o saldo total (receitas - despesas)
    saldo_total = valor_total_receitas - valor_total_despesas

    return render_template('index.html', transacoes=transacoes, receitas=receitas, despesas=despesas, anotacoes=anotacoes,
                           transacoes_apagadas=transacoes_apagadas,  # Adicionar transações apagadas à renderização
                           valor_total_receitas=valor_total_receitas, valor_total_despesas=valor_total_despesas,
                           saldo_total=saldo_total)




# Rota para adicionar uma nova transação
@app.route('/adicionar', methods=['POST'])
def adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        valor = float(request.form['valor'])
        referente = request.form['referente']
        observacao = request.form['observacao']
        tipo = request.form['tipo']

        # Obter o dia atual
        dia_atual = date.today()

        # Inserir transação no banco de dados, incluindo o dia atual
        cursor.execute("INSERT INTO transacoes (nome, valor, referente, observacao, tipo, dia_referente) VALUES (?, ?, ?, ?, ?, ?)",
                       (nome, valor, referente, observacao, tipo, dia_atual))
        conn.commit()

    return redirect('/')

@app.route('/excluir/<int:id>')
def excluir(id):
    # Consultar a transação antes de excluir
    cursor.execute("SELECT * FROM transacoes WHERE id = ?", (id,))
    transacao_excluida = cursor.fetchone()

    # Inserir transação excluída na tabela de transações apagadas
    cursor.execute("INSERT INTO apagados (nome, valor, referente, observacao, tipo, dia_referente) VALUES (?, ?, ?, ?, ?, ?)",
                   transacao_excluida[1:])  # Ignora o ID ao inserir na tabela de apagados
    conn.commit()

    # Excluir transação da tabela principal
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conn.commit()

    return redirect('/')


# Rota para processar a atualização de uma transação
@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    if request.method == 'POST':
        nome = request.form['nome']
        valor = float(request.form['valor'])
        referente = request.form['referente']
        observacao = request.form['observacao']
        tipo = request.form['tipo']

        # Atualizar transação no banco de dados
        cursor.execute("UPDATE transacoes SET nome = ?, valor = ?, referente = ?, observacao = ?, tipo = ? WHERE id = ?",
                       (nome, valor, referente, observacao, tipo, id))
        conn.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
