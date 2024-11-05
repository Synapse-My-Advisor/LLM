import os
from flask import Flask, request, jsonify
from functools import wraps
from openai import OpenAI
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(

        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

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
        db_connection = get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        query = f"SELECT description FROM tg where {tg_id} = %s"
        cursor.execute(query, (tg_id,))    
        result = cursor.fetchone()
        descricao = result["description"]
        
        cursor.close()
        db_connection.close()
    
    except mysql.connector.Error as err:
        return jsonify({'Falhou com Sucesso'})

    try:
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": "Analise esse trabalho de graduação e retorne dicas e insigths para aperfeiçoar, além de fazer pequenas correções se necessário."},
                {"role": "user", "content": descricao},
      
            ],
        )

        response_content = completion.choices[0].message.content
        response_json = {
            "response": response_content,
            "user_id":user_id,
            "tg_id":tg_id,
            "description": descricao
        }
        
        return jsonify(response_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)