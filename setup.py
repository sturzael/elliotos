#!/usr/bin/env python3
"""
ElliotOS Setup Script
Helps with initial configuration and dependency installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Ollama is running")
            return True
        else:
            print("⚠️ Ollama is installed but not running")
            print("   Start it with: ollama serve")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama not found or not running")
        print("   Install it from: https://ollama.ai")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("⚠️ .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your credentials")
        return True
    else:
        print("❌ env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "data"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")

def check_macos_features():
    """Check macOS-specific features"""
    if sys.platform != "darwin":
        print("⚠️ Not running on macOS - some features will be limited")
        return False
    
    print("✅ macOS detected - full feature set available")
    return True

def test_basic_functionality():
    """Test basic ElliotOS functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test imports
        from config.settings import settings
        from utils.logger import logger
        print("✅ Core modules import successfully")
        
        # Test configuration
        missing_config = settings.validate_config()
        if missing_config:
            print("⚠️ Configuration incomplete:")
            for item in missing_config:
                print(f"   - {item}")
        else:
            print("✅ Configuration is valid")
        
        # Test feature status
        feature_status = settings.get_feature_status()
        enabled_features = [k for k, v in feature_status.items() if v]
        print(f"✅ {len(enabled_features)} features enabled: {', '.join(enabled_features)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎉 Setup completed!")
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your credentials:")
    print("   - Add Slack webhook URL or bot token")
    print("   - Configure Google API credentials (optional)")
    print("   - Add NewsAPI key (optional)")
    print("   - Set your preferred schedule times")
    
    print("\n2. Test the system:")
    print("   python main.py --test-data")
    print("   python main.py --test-slack")
    print("   python main.py --status")
    
    print("\n3. Run a test digest:")
    print("   python main.py --test-morning")
    
    print("\n4. Start ElliotOS:")
    print("   python main.py")
    
    print("\n📚 For detailed configuration, see README.md")

def main():
    """Main setup function"""
    print("🚀 ElliotOS Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    check_macos_features()
    check_ollama()
    
    # Setup
    create_directories()
    
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    if not setup_environment():
        print("❌ Setup failed during environment configuration")
        sys.exit(1)
    
    if not test_basic_functionality():
        print("❌ Setup completed but basic tests failed")
        print("   Check your configuration and try again")
        sys.exit(1)
    
    show_next_steps()

if __name__ == "__main__":
    main() 