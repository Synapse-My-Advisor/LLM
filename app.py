from flask import Flask
from flask import request

app = Flask(__name__)

@app.post("/home")
def hello():
    data = request.json['message'] 
    print(data)
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)