#!/usr/bin/env python3

from git_manager import GitManager

def test_real_message_push():
    """Test pushing a real message to GitHub."""
    try:
        # Initialize GitManager
        git_manager = GitManager()
        
        # Create a test message
        message_content = "Test message sent at 2025-01-07T15:44:18-05:00"
        author = "TestUser"
        
        print("Creating message file...")
        filepath = git_manager.create_message_file(
            content=message_content,
            author=author
        )
        print(f"Message file created at: {filepath}")
        
        print("Pushing message to GitHub...")
        commit_hash = git_manager.push_message(
            filepath=filepath,
            commit_message="Add test message via GitManager"
        )
        
        if commit_hash:
            print(f"Success! Message pushed with commit hash: {commit_hash}")
            return True
        else:
            print("Failed to push message")
            return False
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    test_real_message_push()
