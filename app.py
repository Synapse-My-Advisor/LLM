import os
from flask import Flask, request, jsonify
from functools import wraps
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

app = Flask(__name__)

# Configuração do SQLAlchemy para conexão com MySQL
DATABASE_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
engine = create_engine(DATABASE_URL)

def require_token_auth(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token de autenticação não fornecido"}), 401
        
        token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
        expected_token = os.getenv("BEARER_TOKEN")
        if not token or token != expected_token:
            return jsonify({"error": "Token de autenticação inválido"}), 401
        
        return func(*args, **kwargs)
    
    return check_token

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Rota protegida com autenticação Bearer Token
@app.route('/home', methods=['POST'])
# @require_token_auth
def analyze():
    data = request.json
    user_content = data.get("content")
    user_id = data.get("user_id")   
    tg_id = data.get("tg_id")
    
    if not user_content:
        return jsonify({"error": "Content is required"}), 400

    try:
        # Query usando SQLAlchemy, habilitando o modo de mapeamento
        with engine.connect() as connection:
            result = connection.execute(text("SELECT description FROM tg WHERE id = :tg_id"), {"tg_id": tg_id})
            row = result.mappings().fetchone()  # Usa o modo de mapeamento para acessar por nome de coluna
            descricao = row["description"] if row else None
            
            if descricao is None:
                return jsonify({"error": "Description not found"}), 404

    except SQLAlchemyError as err:
        return jsonify({'error': 'Database error', 'details': str(err)}), 500

    try:
        # Requisição para o OpenAI
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": "Você é uma assistente geral"},
                {"role": "user", "content": descricao},
            ],
        )

        response_content = completion.choices[0].message.content
        response_json = {
            "response": response_content,
            "user_id": user_id,
            "tg_id": tg_id,
            "description": descricao
        }
        
        return jsonify(response_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
