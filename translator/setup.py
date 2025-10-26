"""
Setup script để initialize project lần đầu.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Tạo các thư mục cần thiết."""
    dirs = ['input', 'output', 'workflows', 'tests']
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_name}/")
        else:
            print(f"ℹ️  Directory already exists: {dir_name}/")


def create_env_file():
    """Tạo .env file từ .env.example nếu chưa có."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Created .env file from template")
            print(f"⚠️  Please edit .env and add your GEMINI_API_KEY")
        else:
            print(f"⚠️  .env.example not found")
    else:
        print(f"ℹ️  .env file already exists")


def check_python_version():
    """Kiểm tra Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required, current version: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Kiểm tra xem dependencies đã được cài chưa."""
    required_packages = [
        'langchain_google_genai',
        'langchain_core',
        'langgraph',
        'rich',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ Package installed: {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ Package missing: {package}")
    
    if missing:
        print(f"\n⚠️  Please install dependencies:")
        print(f"   pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main setup function."""
    print("=" * 60)
    print("AI Agent Vietnamese Translator - Setup")
    print("=" * 60)
    print()
    
    # Check Python version
    print("📌 Checking Python version...")
    if not check_python_version():
        sys.exit(1)
    print()
    
    # Create directories
    print("📌 Creating directories...")
    create_directories()
    print()
    
    # Create .env file
    print("📌 Setting up environment file...")
    create_env_file()
    print()
    
    # Check dependencies
    print("📌 Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    if deps_ok:
        print("=" * 60)
        print("✅ Setup completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Edit .env and add your GEMINI_API_KEY")
        print("2. Place input JSON files in input/ directory")
        print("3. Run: python main.py")
        print()
    else:
        print("=" * 60)
        print("⚠️  Setup incomplete - please install dependencies")
        print("=" * 60)
        print()
        print("Run: pip install -r requirements.txt")
        print()


if __name__ == "__main__":
    main()
