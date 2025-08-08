#!/usr/bin/env python3
"""
Luna Voice Bot - Main Entry Point

A sophisticated Discord voice bot powered by Google Gemini AI and Google Cloud Text-to-Speech.
Features natural conversation memory, SSML support, and high-quality audio processing.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.bot import LunaBot
from config.settings import DISCORD_TOKEN

def main():
    """Main entry point for Luna Voice Bot"""
    print("🚀 Starting Luna Voice Bot...")
    print("=" * 50)
    print("🎯 Features:")
    print("  • Google Gemini AI responses")
    print("  • Edge-TTS voice synthesis")
    print("  • Smart text/voice response algorithm")
    print("  • Conversation memory")
    print("  • High-quality audio processing")
    print("  • Discord voice messages")
    print("=" * 50)
    
    try:
        # Initialize and start the bot
        bot = LunaBot()
        bot.run(DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
