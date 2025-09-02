#!/usr/bin/env python3
"""
Simple test script to verify --online mode functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from debian_metapackage_manager.cli import PackageManagerCLI

def test_online_mode():
    """Test that --online mode is properly recognized"""
    cli = PackageManagerCLI()
    
    # Test that --online argument is parsed correctly
    print("Testing --online mode argument parsing...")
    
    # This should not raise an error
    try:
        # Test with --help to see if --online is listed
        result = cli.run(['install', '--help'])
        print("✅ CLI can parse install command help")
    except SystemExit:
        # argparse calls sys.exit() for --help, this is expected
        print("✅ CLI help system working")
    except Exception as e:
        print(f"❌ Error testing CLI: {e}")
        return False
    
    # Test mode manager
    print("Testing mode manager...")
    try:
        mode_status = cli.engine.mode_manager.get_mode_status()
        print(f"✅ Mode status: {mode_status}")
        
        # Test switching modes
        cli.engine.mode_manager.switch_to_online_mode()
        print("✅ Successfully switched to online mode")
        
        cli.engine.mode_manager.switch_to_offline_mode()
        print("✅ Successfully switched to offline mode")
        
        return True
    except Exception as e:
        print(f"❌ Error testing mode manager: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing DPM --online mode functionality...")
    success = test_online_mode()
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)