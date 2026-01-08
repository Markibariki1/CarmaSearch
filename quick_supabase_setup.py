#!/usr/bin/env python3
"""
Quick Supabase Setup Script
===========================

This script helps you quickly set up Supabase for CARMA deployment.
"""

import os
import webbrowser

def open_supabase():
    """Open Supabase in browser."""
    print("🚀 Opening Supabase setup page...")
    webbrowser.open("https://supabase.com")
    print("✅ Supabase opened in browser")

def create_quick_setup():
    """Create a quick setup script."""
    setup_script = '''#!/bin/bash
# Quick Supabase Setup Script

echo "🚀 CARMA Supabase Quick Setup"
echo "============================="

echo ""
echo "📋 Follow these steps:"
echo "1. Sign up/login at https://supabase.com"
echo "2. Click 'New Project'"
echo "3. Project name: carma-vehicle-database"
echo "4. Password: Hosthunter1221!"
echo "5. Region: US East (N. Virginia)"
echo "6. Click 'Create new project'"
echo ""
echo "⏳ Wait for project to be ready (2-3 minutes)..."
echo ""
echo "📋 Get your credentials:"
echo "1. Go to Settings → Database"
echo "2. Copy the Connection string"
echo "3. Go to Settings → API"
echo "4. Copy Project URL and anon public key"
echo ""
echo "🔧 Update .env.cloud file with your credentials"
echo ""

read -p "Press Enter when you have your Supabase credentials..."

echo ""
echo "🧪 Testing connection..."
python cloud_database_manager.py

echo ""
echo "✅ Setup complete! Your CARMA system is ready for deployment."
'''
    
    with open('quick_supabase_setup.sh', 'w') as f:
        f.write(setup_script)
    
    os.chmod('quick_supabase_setup.sh', 0o755)
    print("✅ Created quick_supabase_setup.sh")

def main():
    """Main setup function."""
    print("🚀 CARMA Supabase Quick Setup")
    print("=" * 40)
    
    # Open Supabase
    open_supabase()
    
    # Create setup script
    create_quick_setup()
    
    print("\n📋 Next Steps:")
    print("1. Complete Supabase setup in browser")
    print("2. Run: ./quick_supabase_setup.sh")
    print("3. Update .env.cloud with your credentials")
    print("4. Test: python cloud_database_manager.py")
    print("5. Deploy your application!")
    
    print("\n✅ Quick setup files created!")

if __name__ == "__main__":
    main()
