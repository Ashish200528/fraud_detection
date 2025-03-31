from flask import Flask, render_template, request, jsonify
import uuid
import core  

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transaction", methods=["POST"])
def process_transaction():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["sender_account", "receiver_account", "amount", "transaction_type", "transaction_time"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        
        # Call core function
        core.main(
            data["sender_account"],
            data["receiver_account"],
            data["amount"],
            data["transaction_time"],
            data["transaction_type"]
        )
        
        return jsonify({
            "status": "success",
            "transaction_id": str(uuid.uuid4())[:20],
            "message": "Transaction processed"
        })
        
    except Exception as e:
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)