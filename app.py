from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuração do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'qrqc_db'


mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('telainicial.html')  



@app.route('/historico')
def historico():
    return render_template('historico.html')  



@app.route('/CadastroOcorrencia')
def CadastroOcorrencia():
    return render_template('CadastroOcorrencia.html')  

@app.route('/registrar_ocorrencia', methods=['POST'])
def registrar_ocorrencia():
    try:
        # Captura os dados do formulário
        data_ocorrencia = request.form.get('data_ocorrencia')
        nome_operador = request.form.get('nome_operador')
        setor_area = request.form.get('setor_area')
        descricao = request.form.get('descricao')
        tipo_ocorrencia = request.form.get('tipo_ocorrencia')
        nivel_impacto = request.form.get('nivel_impacto')
        problema_recorrente = request.form.get('problema_recorrente')
        detalhamento_tecnico = request.form.get('detalhamento_tecnico')

        # Validação simples dos campos para evitar dados inválidos
        if not all([data_ocorrencia, nome_operador, setor_area, descricao, tipo_ocorrencia, nivel_impacto, problema_recorrente, detalhamento_tecnico]):
            raise ValueError("Todos os campos são obrigatórios!")

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO ocorrencias (data_ocorrencia, nome_operador, setor_area, descricao, tipo_ocorrencia, nivel_impacto, problema_recorrente, detalhamento_tecnico)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data_ocorrencia, nome_operador, setor_area, descricao, tipo_ocorrencia, nivel_impacto, problema_recorrente, detalhamento_tecnico))

        
        mysql.connection.commit()

       
        cur.close()

        
        return render_template('CadastroOcorrencia.html', success=True)

    except Exception as e:
        print(f"Erro ao registrar a ocorrência: {e}")
        
        return render_template('CadastroOcorrencia.html', error=True)

if __name__ == '__main__':
    app.run(debug=True)