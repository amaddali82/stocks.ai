"""
Script to initialize git and commit all code
"""
import subprocess
import os
import sys

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True
        )
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    repo_dir = r"c:\stocks.ai"
    os.chdir(repo_dir)
    
    # Check if git is already initialized
    if not os.path.exists('.git'):
        print("Initializing git repository...")
        if not run_command("git init", cwd=repo_dir):
            print("Failed to initialize git")
            return False
    else:
        print("Git repository already initialized")
    
    # Configure git user (if not already configured)
    run_command('git config user.name "Trading Bot"', cwd=repo_dir)
    run_command('git config user.email "trading@stocks.ai"', cwd=repo_dir)
    
    # Add all files
    print("\nAdding all files...")
    if not run_command("git add .", cwd=repo_dir):
        print("Failed to add files")
        return False
    
    # Check status
    print("\nGit status:")
    run_command("git status", cwd=repo_dir)
    
    # Commit
    print("\nCommitting files...")
    commit_msg = "feat: Add database integration for stock and options data persistence\\n\\n- Created PostgreSQL/TimescaleDB connection layer with pooling\\n- Implemented repository pattern for stocks and options\\n- Added database schema with time-series optimization\\n- Integrated database into options API\\n- Options data now persists and can be retrieved from cache\\n- Added NSE option chain data storage\\n- Updated Docker configuration"
    if not run_command(f'git commit -m "{commit_msg}"', cwd=repo_dir):
        print("Failed to commit (maybe nothing to commit or already committed)")
    
    # Show log
    print("\nGit log:")
    run_command("git log --oneline -5", cwd=repo_dir)
    
    print("\n✅ Git repository initialized and committed!")
    print("\nTo push to GitHub:")
    print("1. Create a repository on GitHub")
    print("2. Run: git remote add origin <your-repo-url>")
    print("3. Run: git branch -M main")
    print("4. Run: git push -u origin main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
