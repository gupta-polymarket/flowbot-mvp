#!/usr/bin/env python3
"""
Validation script to ensure all Flowbot components are working correctly
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - FAILED")
        print(f"   Exception: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    print(f"🔍 {description}...")
    if os.path.exists(filepath):
        print(f"✅ {description} - EXISTS")
        return True
    else:
        print(f"❌ {description} - MISSING")
        return False

def main():
    """Run all validation checks"""
    print("🚀 Flowbot Validation")
    print("=" * 50)
    
    checks = []
    
    # File structure checks
    checks.append(check_file_exists("flowbot/__init__.py", "Flowbot package structure"))
    checks.append(check_file_exists("flowbot/bot.py", "Main bot module"))
    checks.append(check_file_exists("flowbot/config.py", "Config module"))
    checks.append(check_file_exists("flowbot/distributions.py", "Distributions module"))
    checks.append(check_file_exists("requirements.txt", "Requirements file"))
    checks.append(check_file_exists("env.example", "Environment template"))
    checks.append(check_file_exists("config.yaml", "Configuration file"))
    
    # Python syntax checks
    checks.append(run_command("python -m py_compile flowbot/bot.py", "Bot syntax check"))
    checks.append(run_command("python -m py_compile flowbot/config.py", "Config syntax check"))
    checks.append(run_command("python -m py_compile flowbot/distributions.py", "Distributions syntax check"))
    
    # Import checks
    checks.append(run_command("python -c 'from flowbot.bot import main'", "Bot import check"))
    checks.append(run_command("python -c 'from flowbot.config import load_config'", "Config import check"))
    checks.append(run_command("python -c 'from flowbot.distributions import sample_quantity'", "Distributions import check"))
    
    # Unit tests
    checks.append(run_command("python -m pytest test_flowbot_comprehensive.py -v --tb=short", "Comprehensive unit tests"))
    checks.append(run_command("python -m pytest test_flowbot.py -v --tb=short", "Original unit tests"))
    
    # Integration tests
    checks.append(run_command("python test_integration.py", "Integration tests"))
    
    # Demo test
    checks.append(run_command("python demo.py", "Demo script"))
    
    # Help text check
    checks.append(run_command("python -m flowbot.bot --help", "Help text generation"))
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "=" * 50)
    print(f"🏁 Validation Complete: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validation checks passed!")
        print("\n✨ Flowbot is ready to use!")
        print("\nNext steps:")
        print("1. Copy env.example to .env and set your PRIVATE_KEY")
        print("2. Update config.yaml with your target markets")
        print("3. Test with: python -m flowbot.bot --dry-run --iterations 3")
        print("4. Run live: python -m flowbot.bot")
        return 0
    else:
        print("💥 Some validation checks failed!")
        print("Please fix the issues above before using Flowbot.")
        return 1

if __name__ == "__main__":
    exit(main()) 