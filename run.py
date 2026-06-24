import os
import sys

# Ensure Python path includes the backend/ directory
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def main():
    print("=" * 60)
    print("      ROADGUARD AI - SMART INFRASTRUCTURE HUB LAUNCHER      ")
    print("=" * 60)
    print("System check in progress...")
    
    # Check directory layouts
    db_dir = os.path.join(backend_dir, 'db')
    os.makedirs(db_dir, exist_ok=True)
    print(f"✓ Database folder validated: {db_dir}")

    # Check for API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print("✓ Google Gemini API configuration detected. Live AI enabled.")
    else:
        print("⚠ GEMINI_API_KEY environment variable not found.")
        print("  Running in safe rule-based simulation fallback mode.")

    print("\nStarting RoadGuard AI Web Server on http://localhost:5000...")
    print("Press Ctrl+C to stop.")
    print("-" * 60)

    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nRoadGuard AI server stopped cleanly.")
    except Exception as e:
        print(f"\nFailed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
