from flask import Flask, render_template, request, jsonify
from chatbot import DisasterChatbot

app = Flask(__name__ , static_folder='static',  template_folder='templates')
chatbot = DisasterChatbot()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message")
    response = chatbot.generate_response(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)