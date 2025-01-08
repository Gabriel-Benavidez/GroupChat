#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional

class EnvManager:
    def __init__(self, env_file: str = ".env", template_file: str = ".env.template"):
        self.env_file = Path(env_file)
        self.template_file = Path(template_file)
        
    def load_env(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
        
    def get_template_vars(self) -> Dict[str, Optional[str]]:
        """Get variables from .env.template with their descriptions."""
        template_vars = {}
        if self.template_file.exists():
            with open(self.template_file) as f:
                lines = f.readlines()
                last_comment = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('#'):
                        last_comment = line[1:].strip()
                    elif line and not line.startswith('#'):
                        key = line.split('=', 1)[0].strip()
                        template_vars[key] = last_comment
                        last_comment = None
        return template_vars
        
    def list_vars(self):
        """List all environment variables and their values."""
        env_vars = self.load_env()
        template_vars = self.get_template_vars()
        
        print("\nCurrent Environment Variables:")
        print("-" * 50)
        for key in template_vars:
            value = env_vars.get(key, "Not set")
            description = template_vars[key]
            print(f"\n{key}:")
            if description:
                print(f"Description: {description}")
            print(f"Value: {value}")
        print("\n")
        
    def get_var(self, key: str) -> Optional[str]:
        """Get the value of a specific environment variable."""
        env_vars = self.load_env()
        if key in env_vars:
            return env_vars[key]
        return None
        
    def set_var(self, key: str, value: str):
        """Set or update a specific environment variable."""
        env_vars = self.load_env()
        template_vars = self.get_template_vars()
        
        if key not in template_vars:
            print(f"Warning: '{key}' is not defined in {self.template_file}")
            confirm = input("Do you want to add it anyway? (y/N): ")
            if confirm.lower() != 'y':
                return
        
        env_vars[key] = value
        
        # Write back all variables
        with open(self.env_file, 'w') as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
        print(f"Successfully updated {key}")

def main():
    parser = argparse.ArgumentParser(description="Manage environment variables")
    parser.add_argument('action', choices=['list', 'get', 'set'], help='Action to perform')
    parser.add_argument('key', nargs='?', help='Environment variable key')
    parser.add_argument('value', nargs='?', help='Value to set')
    
    args = parser.parse_args()
    
    env_manager = EnvManager()
    
    if args.action == 'list':
        env_manager.list_vars()
    elif args.action == 'get':
        if not args.key:
            parser.error("get requires a key")
        value = env_manager.get_var(args.key)
        if value is not None:
            print(f"{args.key}={value}")
        else:
            print(f"{args.key} is not set")
    elif args.action == 'set':
        if not args.key or not args.value:
            parser.error("set requires both key and value")
        env_manager.set_var(args.key, args.value)

if __name__ == "__main__":
    main()
