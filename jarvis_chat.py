"""
Jarvis - Personal Secretary Chat Interface
Feature 1: Basic Text-Based Conversation with OpenAI API

Run: python jarvis_chat.py
Requires: OPENAI_API_KEY environment variable
"""

import os
from flask import Flask, render_template, request, jsonify
from src.conversation_manager import ConversationManager
from src.storage import ConversationStorage
from src.config import MAX_MESSAGE_LENGTH

app = Flask(__name__)

# Initialize conversation manager
conv_manager = ConversationManager()


@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html', max_length=MAX_MESSAGE_LENGTH)


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Process message
    response, error = conv_manager.process_message(session_id, user_message)
    
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify({
        "response": response,
        "session_id": session_id
    })


@app.route('/history/<session_id>')
def get_history(session_id):
    """Get conversation history for a session"""
    storage = ConversationStorage()
    session = storage.get_or_create_session(session_id)
    
    # Return messages excluding system prompt for display
    messages = [msg for msg in session["messages"] if msg["role"] != "system"]
    
    return jsonify({
        "messages": messages,
        "session_id": session_id
    })


if __name__ == '__main__':
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    print("Starting Jarvis chat server...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
