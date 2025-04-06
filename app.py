import os
import sqlite3
from flask import Flask, render_template, request
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializa Flask
app = Flask(__name__)

# Banco de dados SQLite
def init_db():
    conn = sqlite3.connect('qrqc.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_ocorrencia TEXT,
            nome_operador TEXT,
            setor_area TEXT,
            descricao TEXT,
            tipo_ocorrencia TEXT,
            nivel_impacto TEXT,
            problema_recorrente TEXT,
            detalhamento_tecnico TEXT,
            resposta_ia TEXT,
            imagem_url TEXT,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Função para gerar resposta da IA
def get_ai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Erro na IA: {e}]"

# Função para gerar imagem

def gerar_imagem(prompt):
    try:
        visual_prompt = (
            f"Crie um diagrama explicativo da seguinte solução: {prompt}. "
            "Use estilo técnico, educativo e claro."
        )
        response = client.images.generate(
            model="dall-e-3",
            prompt=visual_prompt,
            n=1,
            size="1024x1024",
            quality="hd"
        )
        return response.data[0].url
    except Exception as e:
        return f"[Erro na geração da imagem: {e}]"

@app.route('/')
def index():
    return render_template('inicialtotem.html')

@app.route('/telaInicial')
def telaInicial():
    return render_template('telaInicial.html')

@app.route('/historico')
def historico():
    try:
        conn = sqlite3.connect('qrqc.db')
        conn.row_factory = sqlite3.Row  # permite acessar os dados como dicionário
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ocorrencias ORDER BY data_registro DESC")
        ocorrencias = cursor.fetchall()
        conn.close()
        return render_template('historico.html', ocorrencias=ocorrencias)
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return render_template('historico.html', ocorrencias=[])

@app.route('/Solicitação_Suporte')
def solicitacao():
    return render_template('Solicitação_Suporte.html')

@app.route('/CadastroOcorrencia')
def CadastroOcorrencia():
    return render_template('CadastroOcorrencia.html')


@app.route('/registrar_ocorrencia', methods=['POST'])
def registrar_ocorrencia():
    try:
        # Dados do formulário
        data_ocorrencia = request.form.get('data_ocorrencia')
        nome_operador = request.form.get('nome_operador')
        setor_area = request.form.get('setor_area')
        descricao = request.form.get('descricao')
        tipo_ocorrencia = request.form.get('tipo_ocorrencia')
        nivel_impacto = request.form.get('nivel_impacto')
        problema_recorrente = request.form.get('problema_recorrente')
        detalhamento_tecnico = request.form.get('detalhamento_tecnico')
        gerar_imagem_checkbox = request.form.get('gerar_imagem')  # Checkbox

        # Validação
        if not all([data_ocorrencia, nome_operador, setor_area, descricao, tipo_ocorrencia, nivel_impacto, problema_recorrente, detalhamento_tecnico]):
            raise ValueError("Todos os campos são obrigatórios!")

        # Gera prompt para IA
        prompt = f"""
        Ocorrência registrada por {nome_operador} em {data_ocorrencia}.
        Setor: {setor_area}.
        Tipo: {tipo_ocorrencia}. Impacto: {nivel_impacto}. Recorrente: {problema_recorrente}. Detalhamento técnico: {detalhamento_tecnico}.
        Descrição do problema: {descricao}.
        
        Gere uma solução em formato de passo a passo numerado, com instruções objetivas e técnicas que o operador possa aplicar imediatamente na prática.
        Evite explicações longas, foque em ações diretas e claras.
        """
        resposta_ia = get_ai_response(prompt)
        
        imagem_url = None
        if gerar_imagem_checkbox:
            imagem_url = gerar_imagem(resposta_ia)

        # Salva no banco de dados
        conn = sqlite3.connect('qrqc.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ocorrencias (
                data_ocorrencia, nome_operador, setor_area, descricao,
                tipo_ocorrencia, nivel_impacto, problema_recorrente,
                detalhamento_tecnico, resposta_ia, imagem_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data_ocorrencia, nome_operador, setor_area, descricao,
              tipo_ocorrencia, nivel_impacto, problema_recorrente,
              detalhamento_tecnico, resposta_ia, imagem_url))
        conn.commit()
        conn.close()

        # Envia os dados para a nova tela de solução
        dados_ocorrencia = {
            'data_ocorrencia': data_ocorrencia,
            'nome_operador': nome_operador,
            'setor_area': setor_area,
            'descricao': descricao,
            'tipo_ocorrencia': tipo_ocorrencia,
            'nivel_impacto': nivel_impacto,
            'problema_recorrente': problema_recorrente,
            'detalhamento_tecnico': detalhamento_tecnico
        }

        return render_template('solucao.html',
                               dados=dados_ocorrencia,
                               resposta_ia=resposta_ia,
                               imagem_gerada=imagem_url)

    except Exception as e:
        print(f"Erro ao registrar ocorrência: {e}")
        return render_template('CadastroOcorrencia.html', error=True)


if __name__ == '__main__':
    app.run(debug=True)