"""Database setup script for Shadow API Scanner."""

import sys
import os
from colorama import init, Fore, Style

# Set console encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Initialize colorama
init(autoreset=True)

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import test_connection, init_db, drop_db


def print_banner():
    """Print setup banner."""
    banner = f"""
{Fore.CYAN}==============================================================
              Shadow API Scanner
           Database Setup Utility
=============================================================={Style.RESET_ALL}
"""
    print(banner)


def main():
    """Main setup function."""
    print_banner()

    # Step 1: Test connection
    print(f"\n{Fore.YELLOW}[1/3] Testing PostgreSQL connection...{Style.RESET_ALL}")
    if not test_connection():
        print(f"\n{Fore.RED}[!] Database connection failed!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please ensure:{Style.RESET_ALL}")
        print("  1. PostgreSQL is installed and running")
        print("  2. Database credentials in .env are correct")
        print("  3. Database 'shadow_api_scanner' exists")
        print(f"\n{Fore.CYAN}To create the database, run:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}psql -U postgres{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}CREATE DATABASE shadow_api_scanner;{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.GREEN}[✓] Connection successful!{Style.RESET_ALL}")

    # Step 2: Ask if user wants to drop existing tables
    print(f"\n{Fore.YELLOW}[2/3] Checking existing tables...{Style.RESET_ALL}")
    response = input(f"{Fore.YELLOW}Do you want to drop existing tables? (y/N): {Style.RESET_ALL}").strip().lower()

    if response == 'y':
        print(f"{Fore.YELLOW}Dropping existing tables...{Style.RESET_ALL}")
        if drop_db():
            print(f"{Fore.GREEN}[✓] Tables dropped successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] Failed to drop tables{Style.RESET_ALL}")
            sys.exit(1)

    # Step 3: Create tables
    print(f"\n{Fore.YELLOW}[3/3] Creating database tables...{Style.RESET_ALL}")
    if init_db():
        print(f"{Fore.GREEN}[✓] Database tables created successfully!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[!] Failed to create tables{Style.RESET_ALL}")
        sys.exit(1)

    # Summary
    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[✓] Database setup completed successfully!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")

    print(f"{Fore.CYAN}Database is now ready to use.{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
    print("  1. Start the API scanner: python main.py")
    print("  2. Start the web UI: cd web-ui && npm run dev")
    print(f"\n{Fore.CYAN}Tables created:{Style.RESET_ALL}")
    print("  - scans           (스캔 기록)")
    print("  - endpoints       (발견된 엔드포인트)")
    print("  - vulnerabilities (발견된 취약점)")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Setup cancelled by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Setup failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
