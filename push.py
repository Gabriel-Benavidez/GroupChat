#!/usr/bin/env python3

import subprocess
import sys

def push_to_github():
    """Push the current repository to GitHub."""
    try:
        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Try to commit
        try:
            subprocess.run(['git', 'commit', '-m', 'Update repository'], check=True)
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in str(e.stderr):
                print("Nothing to commit")
                return True
            print(f"Error during commit: {e.stderr}")
            return False
        
        # Push to remote
        subprocess.run(['git', 'push'], check=True)
        print("Successfully pushed changes")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if push_to_github() else 1)
