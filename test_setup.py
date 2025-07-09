import os
import sys
import subprocess
import requests
import time

print("🚀 Starting RetailMate setup test...")
print("=" * 50)

# Test 1: Check Python version
print(f"Python version: {sys.version}")

# Test 2: Check if virtual environment is active
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("✅ Virtual environment is active")
else:
    print("⚠️ Warning: Virtual environment may not be active")

# Test 3: Check installed packages
print("\n📦 Checking installed packages...")
required_packages = [
    'fastapi', 'uvicorn', 'streamlit', 'ollama', 'langchain', 'chromadb', 'sentence_transformers',
    'pandas', 'numpy', 'vaderSentiment', 'textblob', 'sqlalchemy', 'pydantic', 'requests'
]

for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"✅ Package '{pkg}' is installed")
    except ImportError:
        print(f"❌ Package '{pkg}' is NOT installed")

# Test 4: Test Ollama CLI
print("\n🤖 Testing Ollama CLI...")
try:
    result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(f"✅ Ollama CLI version: {result.stdout.strip()}")
    else:
        print(f"❌ Ollama CLI error: {result.stderr}")
except Exception as e:
    print(f"❌ Ollama CLI not found or error: {e}")

# Test 5: Test Ollama model availability
print("\n🧠 Testing Ollama models...")
try:
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        if 'qwen2.5:3b' in result.stdout:
            print("✅ Qwen 2.5 3B model is available")
        else:
            print("⚠️ Qwen 2.5 3B model not found. Run: ollama pull qwen2.5:3b")
        print("Available models:")
        print(result.stdout)
    else:
        print(f"❌ Failed to list models: {result.stderr}")
except Exception as e:
    print(f"❌ Error checking models: {e}")

# Test 6: Test directory structure
print("\n📁 Testing directory structure...")
required_dirs = [
    'backend', 'backend/app', 'frontend', 'data', 'ollama', 'tests'
]

for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✅ Directory '{dir_path}' exists")
    else:
        print(f"❌ Directory '{dir_path}' missing")

# Test 7: Test configuration files
print("\n⚙️ Testing configuration files...")
config_files = [
    'requirements.txt', '.env', '.gitignore'
]

for file_path in config_files:
    if os.path.exists(file_path):
        print(f"✅ File '{file_path}' exists")
    else:
        print(f"❌ File '{file_path}' missing")

# Test 8: Test import capabilities
print("\n🔍 Testing key imports...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers import successful")
except Exception as e:
    print(f"❌ sentence-transformers import failed: {e}")

try:
    import chromadb
    print("✅ chromadb import successful")
except Exception as e:
    print(f"❌ chromadb import failed: {e}")

try:
    import ollama
    print("✅ ollama import successful")
except Exception as e:
    print(f"❌ ollama import failed: {e}")

# Test 9: Test Git repository
print("\n📡 Testing Git repository...")
try:
    result = subprocess.run(['git', 'status'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Git repository is initialized")
    else:
        print("❌ Git repository not initialized")
except Exception as e:
    print(f"❌ Git test failed: {e}")

# Test 10: Final summary
print("\n" + "=" * 50)
print("🎉 RetailMate setup test completed!")
print("=" * 50)

print("\n📋 Next Steps:")
print("1. Ensure Ollama is running: ollama serve")
print("2. Pull model if needed: ollama pull qwen2.5:3b")
print("3. Start development with your favorite IDE")
print("4. Begin implementing backend and frontend components")
