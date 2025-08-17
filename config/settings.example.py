import os
from datetime import timedelta

# Bot Configuration
DISCORD_TOKEN = "" # DISCORD USER TOKEN
GEMINI_API_KEY = "" 

# Server Configuration
LUNA_SERVER_INVITE = ""  # Replace with actual invite link
LUNA_SERVER_ID = "" 

# Memory Configuration
MAX_MEMORY_MESSAGES = 10
MEMORY_TIMEOUT = timedelta(hours=2)

# Voice Configuration
VOICE_CONFIG = {
    "edge_tts": {
        "voice_name": "fr-FR-DeniseNeural",  # Best French female voice
        "rate": "-15%",      # Speech rate
        "pitch": "+3Hz",     # Voice pitch  
        "volume": "+0%"      # Volume level
    }
}

# Audio Processing Configuration
AUDIO_CONFIG = {
    "normalize_headroom": 2.0,
    "high_pass_filter": 85,
    "low_pass_filter": 7500,
    "compression": {
        "threshold": -16.0,
        "ratio": 2.0,
        "attack": 15.0,
        "release": 150.0
    },
    "volume_boost": 1,
    "export": {
        "bitrate": "128k",
        "compression_level": "10"
    }
}

# Set environment variables (only for Google Gemini AI)
# No Google Cloud TTS setup needed - using free Edge-TTS
