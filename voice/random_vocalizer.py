import asyncio
import random
import os
import logging
import discord
from typing import Optional, List

class RandomVocalizer:
    """Manages random voice file playback in voice channels"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.is_active = False
        self.current_task = None
        self.voicefiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voicefiles")
        self.logger = logging.getLogger(__name__)
        
        # Time range settings (in seconds)
        self.min_interval = 60    # 1 minute
        self.max_interval = 600   # 10 minutes
        
    async def start_random_vocalization(self):
        """Start the random vocalization routine"""
        if self.is_active:
            self.logger.info("Random vocalization is already running")
            return
            
        self.is_active = True
        self.logger.info("🎵 Starting random vocalization routine...")
        
        # Start the main loop
        self.current_task = asyncio.create_task(self._vocalization_loop())
        
    async def stop_random_vocalization(self):
        """Stop the random vocalization routine"""
        self.is_active = False
        
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
            self.current_task = None
            
        self.logger.info("🔇 Stopped random vocalization routine")
        
    async def _vocalization_loop(self):
        """Main loop for random vocalization"""
        while self.is_active:
            try:
                # Wait for random interval
                wait_time = random.randint(self.min_interval, self.max_interval)
                self.logger.info(f"⏰ Next vocalization in {wait_time//60}m {wait_time%60}s")
                
                await asyncio.sleep(wait_time)
                
                # Play random voice file if connected to voice
                if self._is_connected_to_voice():
                    await self._play_random_voice_file()
                else:
                    self.logger.info("🔇 Not connected to voice channel, skipping vocalization")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in vocalization loop: {e}")
                # Short delay on error to prevent spam
                await asyncio.sleep(30)
                
    def _is_connected_to_voice(self) -> bool:
        """Check if bot is currently connected to a voice channel"""
        return self.bot.voice_manager.is_connected_to_voice()
        
    def _get_random_voice_file(self) -> Optional[str]:
        """Get a random voice file from the voicefiles directory"""
        try:
            if not os.path.exists(self.voicefiles_dir):
                self.logger.warning(f"⚠️ Voicefiles directory not found: {self.voicefiles_dir}")
                return None
                
            # Get all audio files
            audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
            voice_files = []
            
            for file in os.listdir(self.voicefiles_dir):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    voice_files.append(os.path.join(self.voicefiles_dir, file))
                    
            if not voice_files:
                self.logger.warning("⚠️ No voice files found in voicefiles directory")
                return None
                
            # Return random file
            selected_file = random.choice(voice_files)
            self.logger.info(f"🎲 Selected random voice file: {os.path.basename(selected_file)}")
            return selected_file
            
        except Exception as e:
            self.logger.error(f"❌ Error getting random voice file: {e}")
            return None
            
    async def _play_random_voice_file(self):
        """Play a random voice file in the current voice channel"""
        try:
            voice_file = self._get_random_voice_file()
            
            if not voice_file:
                self.logger.warning("⚠️ No voice file available to play")
                return
                
            # Use the voice manager to play the audio
            success = await self.bot.voice_manager.play_audio_file(voice_file)
            
            if success:
                self.logger.info(f"✅ Random voice file finished playing: {os.path.basename(voice_file)}")
            else:
                self.logger.warning("⚠️ Failed to play random voice file")
            
        except Exception as e:
            self.logger.error(f"❌ Error playing random voice file: {e}")
            
    def get_status(self) -> dict:
        """Get current status of random vocalization"""
        voice_files_count = 0
        if os.path.exists(self.voicefiles_dir):
            audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
            voice_files_count = len([f for f in os.listdir(self.voicefiles_dir) 
                                   if any(f.lower().endswith(ext) for ext in audio_extensions)])
                                   
        return {
            "active": self.is_active,
            "voice_files_count": voice_files_count,
            "min_interval_minutes": self.min_interval // 60,
            "max_interval_minutes": self.max_interval // 60,
            "connected_to_voice": self._is_connected_to_voice()
        }
        
    def set_interval_range(self, min_minutes: int, max_minutes: int):
        """Set the interval range for random vocalization"""
        self.min_interval = min_minutes * 60
        self.max_interval = max_minutes * 60
        self.logger.info(f"🔧 Updated interval range: {min_minutes}-{max_minutes} minutes")
