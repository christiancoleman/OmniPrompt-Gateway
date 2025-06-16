#!/usr/bin/env python
"""
OmniPrompt Gateway Setup Script
Automated setup for easy deployment
"""
import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("   OmniPrompt Gateway (OPG) Setup")
    print("   Multi-model LLM interface with MCP support")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path(".venv")
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return
    
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    print("✓ Virtual environment created")

def get_pip_command():
    """Get the correct pip command for the virtual environment"""
    if platform.system() == "Windows":
        pip_path = Path(".venv/Scripts/pip.exe")
    else:
        pip_path = Path(".venv/bin/pip")
    
    if pip_path.exists():
        return str(pip_path)
    else:
        # Fallback to python -m pip
        if platform.system() == "Windows":
            python_path = Path(".venv/Scripts/python.exe")
        else:
            python_path = Path(".venv/bin/python")
        return f"{python_path} -m pip"

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    pip_cmd = get_pip_command()
    
    # Upgrade pip first
    subprocess.run(f"{pip_cmd} install --upgrade pip".split(), check=True)
    
    # Install requirements
    subprocess.run(f"{pip_cmd} install -r requirements.txt".split(), check=True)
    print("✓ Dependencies installed")

def setup_env_file():
    """Create .env file from template if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("✓ .env file already exists")
        return
    
    # Create .env.example if it doesn't exist
    if not env_example_path.exists():
        example_content = """# OmniPrompt Gateway Configuration
# Copy this file to .env and fill in your API keys

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
# Optional: Change the default model
# OPENAI_MODEL=gpt-4

# Claude Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
# Optional: Change the Claude model
# CLAUDE_MODEL=claude-3-sonnet-20240229

# Optional: MCP Integration
ENABLE_MCP=true
MCP_FILESYSTEM_PATH=.

# Optional: Default system prompt
GENERIC_SYSTEM_PROMPT=You are a helpful AI assistant.
"""
        env_example_path.write_text(example_content)
        print("✓ Created .env.example")
    
    # Copy to .env
    shutil.copy(env_example_path, env_path)
    print("✓ Created .env file (remember to add your API keys!)")

def setup_command_shortcuts():
    """Set up opg command for easy access"""
    system = platform.system()
    
    if system == "Windows":
        # For Windows, we already have opg.cmd
        print("\n✓ Windows command 'opg.cmd' is ready")
        print("  Add this directory to your PATH to use 'opg' from anywhere:")
        print(f"  {os.getcwd()}")
        
        # Create a PowerShell script too
        ps1_content = """# OmniPrompt Gateway PowerShell launcher
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
& python "$scriptPath\\opg.py" @args
"""
        Path("opg.ps1").write_text(ps1_content)
        print("✓ PowerShell script 'opg.ps1' created")
        
    else:
        # For Unix/Linux/Mac, make the script executable
        opg_path = Path("opg")
        if opg_path.exists():
            os.chmod("opg", 0o755)
            print("✓ Made 'opg' executable")
        
        # Suggest adding to PATH
        print("\n  To use 'opg' from anywhere, add this line to your shell config:")
        print(f"  export PATH=\"{os.getcwd()}:$PATH\"")

def check_node_installation():
    """Check if Node.js is installed (for MCP)"""
    print("\nChecking Node.js installation (required for MCP)...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js {result.stdout.strip()} detected")
            return True
        else:
            print("⚠ Node.js not found")
            return False
    except FileNotFoundError:
        print("⚠ Node.js not found")
        return False

def install_mcp_servers():
    """Optionally install MCP servers"""
    response = input("\nWould you like to install MCP filesystem server? (y/n): ").lower()
    if response == 'y':
        print("Installing MCP filesystem server...")
        try:
            subprocess.run(["npm", "install", "-g", "@modelcontextprotocol/server-filesystem"], check=True)
            print("✓ MCP filesystem server installed")
        except Exception as e:
            print(f"⚠ Failed to install MCP server: {e}")
            print("  You can install it manually later with:")
            print("  npm install -g @modelcontextprotocol/server-filesystem")

def create_deployment_package():
    """Create a deployment package"""
    response = input("\nCreate deployment package? (y/n): ").lower()
    if response != 'y':
        return
    
    print("\nCreating deployment package...")
    deploy_dir = Path("opg_deployment")
    deploy_dir.mkdir(exist_ok=True)
    
    # Files to include
    files_to_copy = [
        "opg.py",
        "robust_mcp_wrapper.py",
        "requirements.txt",
        ".env.example",
        "README.md",
        "setup.py",
        "opg.cmd",
        "opg"
    ]
    
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy(file, deploy_dir)
    
    # Create deployment instructions
    deploy_instructions = """# OmniPrompt Gateway Deployment Instructions

1. Copy this folder to the target computer
2. Open a terminal/command prompt in this directory
3. Run: python setup.py
4. Edit .env file to add your API keys
5. Run: opg

That's it! OmniPrompt Gateway is ready to use.

## Requirements
- Python 3.8 or higher
- Node.js (for MCP features)
- Internet connection (for API access)
"""
    
    (deploy_dir / "DEPLOY.md").write_text(deploy_instructions)
    print(f"✓ Deployment package created in '{deploy_dir}' folder")

def main():
    """Run the setup process"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Create virtual environment
    create_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Set up configuration
    setup_env_file()
    
    # Set up commands
    setup_command_shortcuts()
    
    # Check Node.js
    has_node = check_node_installation()
    if has_node:
        install_mcp_servers()
    else:
        print("\n  To enable MCP features, install Node.js from:")
        print("  https://nodejs.org/")
    
    # Create deployment package
    create_deployment_package()
    
    # Final instructions
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file to add your API keys")
    print("2. Run 'opg' to start OmniPrompt Gateway")
    
    if platform.system() == "Windows":
        print("\nWindows users:")
        print("- Use 'opg.cmd' from Command Prompt")
        print("- Use '.\\opg.ps1' from PowerShell")
        print("- Add this directory to PATH for global access")
    else:
        print("\nUnix/Mac users:")
        print("- Run './opg' to start")
        print("- Add to PATH for global access")
    
    print("\nEnjoy using OmniPrompt Gateway! 🚀")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
