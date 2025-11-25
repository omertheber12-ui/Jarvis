"""
Jarvis - Personal Secretary Chat Interface
Feature 1: Basic Text-Based Conversation with OpenAI API

Run: python jarvis_chat.py
Requires: .env file with OPENAI_API_KEY or environment variable
"""

import argparse

from flask import Flask, render_template, request, jsonify

from src.config import (
    ENABLE_CALENDAR,
    ENABLE_TASKS,
    MAX_MESSAGE_LENGTH,
    OPENAI_API_KEY,
)
from src.conversation_manager import ConversationManager
from src.storage import ConversationStorage

app = Flask(__name__)

# Initialize conversation manager (lazy initialization to avoid errors at import)
conv_manager = None

def get_conv_manager():
    """Get or create conversation manager instance"""
    global conv_manager
    if conv_manager is None:
        conv_manager = ConversationManager()
    return conv_manager


@app.route('/')
def index():
    """Main chat interface"""
    return render_template(
        'index.html',
        max_length=MAX_MESSAGE_LENGTH,
        enable_calendar=ENABLE_CALENDAR,
        enable_tasks=ENABLE_TASKS,
    )


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Process message
        response, error = get_conv_manager().process_message(session_id, user_message)
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({
            "response": response,
            "session_id": session_id
        })
    except Exception as e:
        # Return JSON error instead of HTML error page
        import traceback
        error_details = str(e)
        if app.debug:
            error_details += f"\n{traceback.format_exc()}"
        return jsonify({"error": f"Server error: {error_details}"}), 500


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


def run_calendar_test():
    """List upcoming Google Calendar events as a connectivity check."""
    if not ENABLE_CALENDAR:
        print("Calendar integration is disabled (ENABLE_CALENDAR=false).")
        return

    from src.calendar import GoogleCalendarProvider

    provider = GoogleCalendarProvider()
    events = provider.list_upcoming_events()
    if not events:
        print("No upcoming events found.")
        return

    print("Upcoming events:")
    for event in events:
        print(f"- {event.start} → {event.end}: {event.summary}")


def main():
    parser = argparse.ArgumentParser(description="Jarvis personal secretary server")
    parser.add_argument(
        "--calendar-test",
        action="store_true",
        help="List upcoming Google Calendar events and exit.",
    )
    args = parser.parse_args()

    if args.calendar_test:
        run_calendar_test()
        return

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not set")
        print("Please create a .env file with your API key:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your OpenAI API key to .env file")
        print("  3. Or set it as environment variable: $env:OPENAI_API_KEY='your-key'")
        exit(1)

    print("Starting Jarvis chat server...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
