#!/usr/bin/env python3
"""
Development runner script that sets OAuth environment variables before starting the app
"""

import os
import sys

def setup_oauth_environment():
    """Set up OAuth environment variables for development"""
    print("🔧 Setting up OAuth environment for development...")
    
    # Set OAuth environment variables
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    os.environ['FLASK_ENV'] = 'development'
    
    print("✅ OAuth environment variables set:")
    print(f"  - OAUTHLIB_INSECURE_TRANSPORT: {os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}")
    print(f"  - OAUTHLIB_RELAX_TOKEN_SCOPE: {os.environ.get('OAUTHLIB_RELAX_TOKEN_SCOPE')}")
    print(f"  - FLASK_ENV: {os.environ.get('FLASK_ENV')}")

def main():
    """Main function to run the development server"""
    print("🚀 Invoice Australia - Development Server")
    print("=" * 50)
    
    # Set up OAuth environment
    setup_oauth_environment()
    
    print("\n🌐 Starting development server...")
    print("📋 The application will be available at: http://localhost:5000")
    print("🔑 OAuth login should now work without HTTPS errors")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    # Import and run the app
    try:
        from app_refactored import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 