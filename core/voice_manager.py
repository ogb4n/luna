"""
Voice connection manager for Luna bot
Centralizes all voice-related functionality
"""

import asyncio
import random
import os
import discord
from typing import Optional, List
from config.autonomous_config import BLACKLISTED_CHANNEL_IDS, AUTONOMOUS_RECRUITMENT, ALLOWED_SERVER_IDS


class VoiceManager:
    """Manages voice connections and audio playback"""
    
    def __init__(self, bot):
        self.bot = bot
        self.blacklisted_channel_ids = BLACKLISTED_CHANNEL_IDS
    
    def is_channel_blacklisted(self, channel_id: str) -> bool:
        """Check if a channel ID is in the blacklist"""
        if not channel_id:
            return False
            
        # Convert to string to ensure consistent comparison
        channel_id_str = str(channel_id)
        
        # Check if the channel ID is in the blacklist
        is_blacklisted = channel_id_str in self.blacklisted_channel_ids
        if is_blacklisted:
            print(f"🚫 Skipping blacklisted channel ID: {channel_id_str}")
        
        return is_blacklisted
    
    async def join_voice_channel(self, channel_id: str, guild_id: str) -> bool:
        """Join a specific voice channel"""
        try:
            guild = self.bot.client.get_guild(int(guild_id))
            if not guild:
                print(f"❌ Could not find guild {guild_id}")
                return False
                
            channel = guild.get_channel(int(channel_id))
            if not channel:
                print(f"❌ Could not find channel {channel_id}")
                return False
                
            # Use the improved retry logic
            return await self.join_voice_channel_with_retry(channel, guild)
            
        except Exception as e:
            print(f"❌ Failed to join voice channel: {e}")
            return False
    
    async def join_voice_channel_with_retry(self, voice_channel, guild, max_retries=None):
        """Join a voice channel with retry logic and better error handling"""
        if max_retries is None:
            max_retries = AUTONOMOUS_RECRUITMENT.get("voice_retry_attempts", 3)
            
        timeout = AUTONOMOUS_RECRUITMENT.get("voice_connection_timeout", 10)
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries} to join {voice_channel.name}...")
                
                # Check if we're already connected somewhere and disconnect first
                if self.bot.client.voice_clients:
                    print("🔌 Disconnecting from current voice channel...")
                    for vc in self.bot.client.voice_clients:
                        await vc.disconnect()
                    await asyncio.sleep(2)  # Wait a bit after disconnecting
                
                # Add a small delay between attempts
                if attempt > 0:
                    delay = 2 ** attempt  # Exponential backoff
                    print(f"⏳ Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                
                # Try to connect
                voice_client = await voice_channel.connect(timeout=timeout, reconnect=False)
                print(f"✅ Successfully joined {voice_channel.name} in {guild.name}")
                
                # Play the greeting audio
                await self.play_greeting_audio(voice_client)
                
                # Send a casual greeting
                await self.send_startup_greeting(guild, voice_channel)
                return True
                
            except discord.errors.ConnectionClosed as e:
                if "4006" in str(e):
                    print(f"⚠️ Discord error 4006 (Session invalid) - Attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        print("❌ All retry attempts failed due to session issues")
                        print("💡 This might be a Discord API limitation for selfbots")
                        return False
                else:
                    print(f"⚠️ Connection closed error: {e}")
            except discord.errors.ClientException as e:
                print(f"⚠️ Client error: {e}")
                if "already connected" in str(e).lower():
                    print("🔌 Already connected to a voice channel, trying to disconnect first...")
                    continue
            except Exception as e:
                print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    print("❌ All retry attempts failed")
                    return False
        
        return False
    
    async def join_best_voice_channel(self):
        """Find and join the most active voice channel across allowed servers"""
        try:
            print("🔍 Searching for the most active voice channel to join...")
            
            # Get all available servers using Discord client
            all_guilds = self.bot.client.guilds
            
            if not all_guilds:
                print("❌ No servers available for voice channel search")
                return
            
            # Filter guilds based on allowed server IDs
            if ALLOWED_SERVER_IDS:
                # Convert allowed server IDs to integers for comparison
                allowed_ids = [int(server_id) for server_id in ALLOWED_SERVER_IDS]
                guilds = [guild for guild in all_guilds if guild.id in allowed_ids]
                print(f"🎯 Filtering to {len(guilds)} allowed servers out of {len(all_guilds)} total servers")
                
                if not guilds:
                    print(f"❌ None of the allowed servers are available. Allowed IDs: {ALLOWED_SERVER_IDS}")
                    return
            else:
                # If no allowed servers specified, use all servers (legacy behavior)
                guilds = all_guilds
                print(f"ℹ️ No server filtering configured - searching all {len(guilds)} servers")
            
            best_channel = None
            best_score = 0
            best_guild_info = None
            
            # Search through filtered servers for the best voice channel
            for guild in guilds:
                try:
                    print(f"🔍 Analyzing {guild.name} (ID: {guild.id}) - {len(guild.voice_channels)} voice channels...")
                    
                    best_guild_channel = None
                    max_members = 0
                    
                    # Check each voice channel directly using Discord client
                    for voice_channel in guild.voice_channels:
                        # Skip blacklisted channels
                        if self.is_channel_blacklisted(voice_channel.id):
                            continue
                            
                        member_count = len(voice_channel.members)
                        
                        if member_count > max_members:
                            max_members = member_count
                            best_guild_channel = voice_channel
                    
                    # Only consider channels with members
                    if not best_guild_channel or max_members == 0:
                        print(f"  ℹ️ No active voice channels found")
                        continue
                        
                    # Calculate a simple score: member count + server size bonus
                    server_bonus = min(len(guild.members) / 1000, 5)  # Max 5 point bonus
                    score = max_members + server_bonus
                    
                    print(f"📊 {guild.name} - {best_guild_channel.name}: {max_members} members (score: {score:.1f})")
                    
                    if score > best_score:
                        best_score = score
                        best_channel = best_guild_channel
                        best_guild_info = guild
                        
                except Exception as e:
                    print(f"⚠️ Error analyzing {guild.name}: {e}")
                    continue
            
            # Join the best channel found
            if best_channel and best_score > 0:
                print(f"🎯 Best target found: {best_channel.name} ({best_channel.id}) in {best_guild_info.name} ({len(best_channel.members)} members)")
                
                # Join the channel with retry logic and better error handling
                await self.join_voice_channel_with_retry(best_channel, best_guild_info)
            else:
                print("ℹ️ No active voice channels found to join")
                
        except Exception as e:
            print(f"❌ Error in startup voice channel search: {e}")
    
    async def play_greeting_audio(self, voice_client):
        """Play the 0809.mp3 file when joining a voice channel"""
        try:
            # Path to the audio file
            audio_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "0809.mp3")
            
            if not os.path.exists(audio_file_path):
                print(f"❌ Audio file not found: {audio_file_path}")
                return
                
            print(f"🎵 Playing greeting audio: {audio_file_path}")
            
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(audio_file_path)
            
            # Check if already playing something
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)  # Brief pause
                
            # Play the audio
            voice_client.play(audio_source)
            
            # Wait for the audio to finish playing
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            print("✅ Greeting audio finished playing")
            
        except Exception as e:
            print(f"❌ Error playing greeting audio: {e}")
    
    async def send_startup_greeting(self, guild, voice_channel):
        """Send a casual greeting when joining a channel using direct Discord objects"""
        try:
            # Look for an appropriate text channel
            text_channel = None
            
            # Try to find a general text channel
            for channel in guild.text_channels:
                if any(name in channel.name.lower() for name in ['general', 'chat', 'discussion', 'main']):
                    text_channel = channel
                    break
                    
            if text_channel:
                startup_greetings = [
                    "Salut ! Je viens de me connecter 👋",
                    "Hey tout le monde ! Comment ça va ? 😊",
                    "Coucou ! Quelqu'un dans le vocal ? 🎵",
                    "Hello ! Belle journée n'est-ce pas ? ✨",
                    "Salut ! Ça discute par ici ? 💬"
                ]
                
                greeting = random.choice(startup_greetings)
                
                # Wait a natural amount of time before greeting
                await asyncio.sleep(random.randint(8, 20))
                await text_channel.send(greeting)
                
                print(f"💬 Sent startup greeting: {greeting}")
                
        except Exception as e:
            print(f"⚠️ Could not send startup greeting: {e}")
    
    async def play_audio_file(self, audio_file_path: str) -> bool:
        """Play an audio file in the current voice channel"""
        try:
            if not self.bot.client.voice_clients:
                print("⚠️ No voice clients available")
                return False
                
            voice_client = self.bot.client.voice_clients[0]
            
            if not os.path.exists(audio_file_path):
                print(f"❌ Audio file not found: {audio_file_path}")
                return False
                
            print(f"🎵 Playing audio file: {os.path.basename(audio_file_path)}")
            
            # Stop current audio if playing
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)
                
            # Create audio source and play
            audio_source = discord.FFmpegPCMAudio(audio_file_path)
            voice_client.play(audio_source)
            
            # Wait for audio to finish
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            print("✅ Audio file finished playing")
            return True
            
        except Exception as e:
            print(f"❌ Error playing audio file: {e}")
            return False
    
    def is_connected_to_voice(self) -> bool:
        """Check if bot is currently connected to a voice channel"""
        return bool(self.bot.client.voice_clients)
    
    def get_current_voice_channel(self) -> Optional[discord.VoiceChannel]:
        """Get the current voice channel if connected"""
        if self.bot.client.voice_clients:
            return self.bot.client.voice_clients[0].channel
        return None
