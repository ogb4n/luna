#!/usr/bin/env python3
"""
Luna Voice Bot - Main Entry Point

A sophisticated Discord voice bot powered by Google Gemini AI and Google Cloud Text-to-Speech.
Features natural conversation memory, SSML support, and high-quality audio processing.
"""

import sys
import os

import discord

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
    except discord.errors.LoginFailure:
        print("❌ Discord token is invalid or expired!")
        print("🔧 Please update your token using: python update_token.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if "token" in str(e).lower():
            print("🔧 This looks like a token issue.")
        sys.exit(1)

if __name__ == "__main__":
    main()
