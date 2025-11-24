"""Test script to check if server can start"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    print("Testing imports...")
    from jarvis_chat import app
    print("✓ App imported successfully")
    
    print("\nTesting server startup...")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


