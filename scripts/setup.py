#!/usr/bin/env python3
"""
Setup script for EisenhowerTriageAgent project.
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_requirements():
    """Check if requirements.txt exists."""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    print("✅ requirements.txt found")
    return True

def create_env_template():
    """Create .env template if it doesn't exist."""
    env_file = Path(__file__).parent.parent / ".env"
    env_template = Path(__file__).parent.parent / ".env.example"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_template.exists():
        print("✅ .env.example found")
        return True
    
    # Create .env.example template
    template_content = """# EisenhowerTriageAgent Environment Configuration

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Optional: Logging Configuration
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_template, 'w') as f:
            f.write(template_content)
        print("✅ Created .env.example template")
        return True
    except Exception as e:
        print(f"❌ Error creating .env.example: {str(e)}")
        return False

def check_directories():
    """Check if required directories exist."""
    project_root = Path(__file__).parent.parent
    required_dirs = [
        "backend",
        "scripts", 
        "tests",
        "docs",
        "data/sample_emails"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}/ directory exists")
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    return True

def main():
    """Main setup function."""
    print("🔧 EisenhowerTriageAgent Setup")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Requirements File", check_requirements),
        ("Environment Template", create_env_template),
        ("Directory Structure", check_directories),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {check_name} check failed")
    
    print(f"\n{'='*50}")
    print(f"Setup Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run tests: python scripts/run_tests.py")
        print("4. Process sample emails: python scripts/run_batch_from_eml.py")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed")
        print("Please fix the issues above before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 