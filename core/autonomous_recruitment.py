"""
Autonomous recruitment system for Luna
Automatically scouts servers and joins voice channels for recruitment
"""

import asyncio
import random
import logging
import os
import discord
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from config.autonomous_config import AUTONOMOUS_RECRUITMENT, BLACKLISTED_CHANNEL_IDS, ALLOWED_SERVER_IDS


class AutonomousRecruitment:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.discord_api = bot_instance.discord_api
        self.current_voice_channel = None
        self.recruitment_active = False
        self.last_scan_time = None
        
        # Load configuration from config file
        config = AUTONOMOUS_RECRUITMENT
        self.scan_interval = config["scan_interval"]
        self.min_members_threshold = config["min_members_threshold"]
        self.max_members_threshold = config["max_members_threshold"]
        self.optimal_member_range = config["optimal_member_range"]
        self.server_cooldown_hours = config["server_cooldown_hours"]
        self.min_recruitment_time = config["min_recruitment_time"]
        self.max_recruitment_time = config["max_recruitment_time"]
        
        # Server cooldowns and blacklist
        self.recruitment_cooldown = {}
        self.blacklisted_channel_ids = BLACKLISTED_CHANNEL_IDS
        self.logger = logging.getLogger(__name__)
        
    async def start_autonomous_mode(self):
        """Start the autonomous recruitment system"""
        self.recruitment_active = True
        self.logger.info("🤖 Starting autonomous recruitment mode...")
        
        # Start the main recruitment loop
        asyncio.create_task(self._recruitment_loop())
        
    async def stop_autonomous_mode(self):
        """Stop autonomous recruitment"""
        self.recruitment_active = False
        if self.current_voice_channel:
            await self._leave_voice_channel()
        self.logger.info("🛑 Stopped autonomous recruitment mode")
        
    async def _recruitment_loop(self):
        """Main loop for autonomous recruitment"""
        while self.recruitment_active:
            try:
                await self._execute_recruitment_cycle()
                
                wait_time = self.scan_interval + random.randint(-60, 60)
                self.logger.info(f"⏰ Next recruitment cycle in {wait_time} seconds")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"❌ Error in recruitment loop: {e}")
                await asyncio.sleep(30)  # Short delay on error
                
    async def _execute_recruitment_cycle(self):
        """Execute one complete recruitment cycle"""
        self.logger.info("🔄 Starting recruitment cycle...")
        
        # Check if already connected to a voice channel from startup
        if self.bot.client.voice_clients:
            current_voice = self.bot.client.voice_clients[0]
            self.current_voice_channel = current_voice
            self.logger.info(f"🎵 Already connected to {current_voice.channel.name} in {current_voice.guild.name}")
            
            recruitment_duration = random.randint(self.min_recruitment_time, self.max_recruitment_time)
            self.logger.info(f"🎯 Continuing recruitment for {recruitment_duration//60} minutes")
            
            await asyncio.sleep(recruitment_duration)
            
            # Leave and continue with normal cycle
            await self._leave_voice_channel()
            self._set_server_cooldown(str(current_voice.guild.id))
            return
        
        # Step 1: Find the best target
        target = await self._find_best_recruitment_target()
        
        if not target:
            self.logger.info("🔍 No suitable recruitment targets found")
            return
            
        # Step 2: Join the target channel
        success = await self._join_target_channel(target)
        
        if not success:
            self.logger.warning(f"❌ Failed to join target channel: {target['channel_name']}")
            return
            
        # Step 3: Stay and recruit for a period
        recruitment_duration = random.randint(self.min_recruitment_time, self.max_recruitment_time)
        self.logger.info(f"🎯 Recruiting in {target['channel_name']} for {recruitment_duration//60} minutes")
        
        await asyncio.sleep(recruitment_duration)
        
        # Step 4: Leave the channel
        await self._leave_voice_channel()
        
        # Step 5: Set cooldown for this server
        self._set_server_cooldown(target['guild_id'])
        
    async def _find_best_recruitment_target(self) -> Optional[Dict]:
        """Find the best voice channel for recruitment"""
        try:
            # Get all available servers
            all_guilds = await self.discord_api.get_available_guilds()
            
            if not all_guilds:
                return None
            
            # Filter guilds based on allowed server IDs
            if ALLOWED_SERVER_IDS:
                # Convert allowed server IDs to strings for comparison (API returns string IDs)
                allowed_ids = [str(server_id) for server_id in ALLOWED_SERVER_IDS]
                guilds = [guild for guild in all_guilds if str(guild['id']) in allowed_ids]
                self.logger.info(f"🎯 Filtering to {len(guilds)} allowed servers out of {len(all_guilds)} total servers")
                
                if not guilds:
                    self.logger.warning(f"❌ None of the allowed servers are available. Allowed IDs: {ALLOWED_SERVER_IDS}")
                    return None
            else:
                # If no allowed servers specified, use all servers (legacy behavior)
                guilds = all_guilds
                self.logger.info(f"ℹ️ No server filtering configured - searching all {len(guilds)} servers")
                
            best_target = None
            best_score = 0
            
            for guild in guilds:
                guild_id = guild['id']
                
                # Skip if server is on cooldown
                if self._is_server_on_cooldown(guild_id):
                    continue
                    
                # Skip Luna's own server (we want to recruit TO it, not FROM it)
                from config.settings import LUNA_SERVER_ID
                if str(guild_id) == str(LUNA_SERVER_ID):
                    continue
                    
                # Scout this server for voice channels
                channel_info = await self.discord_api.get_most_filled_voice_channel(guild_id)
                
                if not channel_info:
                    continue
                    
                member_count = channel_info.get('estimated_members', 0)
                
                # Check if channel meets our criteria
                if member_count < self.min_members_threshold or member_count > self.max_members_threshold:
                    continue
                
                # Skip blacklisted channels
                channel_id_to_check = channel_info.get('channel_id', '')
                self.logger.info(f"🔍 Checking channel {channel_info.get('channel_name')} with ID: {channel_id_to_check} (type: {type(channel_id_to_check)})")
                self.logger.info(f"🔍 Blacklisted IDs: {self.blacklisted_channel_ids}")
                
                if self._is_channel_blacklisted(channel_id_to_check):
                    self.logger.info(f"🚫 Skipping blacklisted channel: {channel_info.get('channel_name')} (ID: {channel_id_to_check})")
                    continue
                    
                # Calculate recruitment score
                score = self._calculate_recruitment_score(channel_info, guild)
                
                if score > best_score:
                    best_score = score
                    best_target = channel_info
                    best_target['guild_id'] = guild_id
                    
            if best_target:
                self.logger.info(f"🎯 Best target: {best_target['channel_name']} ({best_target['estimated_members']} members)")
                
            return best_target
            
        except Exception as e:
            self.logger.error(f"❌ Error finding recruitment target: {e}")
            return None
            
    def _calculate_recruitment_score(self, channel_info: Dict, guild_info: Dict) -> float:
        """Calculate recruitment potential score for a channel"""
        member_count = channel_info.get('estimated_members', 0)
        guild_member_count = guild_info.get('member_count', 0)
        
        # Base score from member count (using optimal range from config)
        optimal_min, optimal_max = self.optimal_member_range
        if optimal_min <= member_count <= optimal_max:
            member_score = 100
        elif member_count < optimal_min:
            member_score = member_count * 20
        else:
            member_score = max(0, 100 - (member_count - optimal_max) * 10)
            
        # Bonus for larger servers (more potential recruits)
        server_bonus = min(50, guild_member_count / 100)
        
        # Random factor to avoid always targeting the same channels
        random_factor = random.uniform(0.8, 1.2)
        
        total_score = (member_score + server_bonus) * random_factor
        
        self.logger.debug(f"📊 Score for {channel_info['channel_name']}: {total_score:.1f}")
        
        return total_score
        
    async def _join_target_channel(self, target: Dict) -> bool:
        """Join the target voice channel"""
        try:
            guild_id = target['guild_id']
            channel_id = target['channel_id']
            
            # Get the guild and channel objects
            guild = self.bot.client.get_guild(int(guild_id))
            if not guild:
                self.logger.error(f"❌ Could not find guild {guild_id}")
                return False
                
            channel = guild.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"❌ Could not find channel {channel_id}")
                return False
                
            # Leave current channel if connected
            if self.current_voice_channel:
                await self._leave_voice_channel()
                
            # Connect to the new channel
            voice_client = await channel.connect()
            self.current_voice_channel = voice_client
            
            self.logger.info(f"✅ Joined voice channel: {target['channel_name']} in {target['guild_name']}")
            
            # Play the 0809.mp3 file
            await self._play_greeting_audio()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to join voice channel: {e}")
            return False
            
    async def _play_greeting_audio(self):
        """Play the 0809.mp3 file when joining a voice channel"""
        if not self.current_voice_channel:
            self.logger.warning("⚠️ No voice client available to play audio")
            return
            
        try:
            # Path to the audio file
            audio_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "0809.mp3")
            
            if not os.path.exists(audio_file_path):
                self.logger.error(f"❌ Audio file not found: {audio_file_path}")
                return
                
            self.logger.info(f"🎵 Playing greeting audio: {audio_file_path}")
            
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(audio_file_path)
            
            # Check if already playing something
            if self.current_voice_channel.is_playing():
                self.current_voice_channel.stop()
                await asyncio.sleep(0.5)  # Brief pause
                
            # Play the audio
            self.current_voice_channel.play(audio_source)
            
            # Wait for the audio to finish playing
            while self.current_voice_channel.is_playing():
                await asyncio.sleep(0.5)
                
            self.logger.info("✅ Greeting audio finished playing")
            
        except Exception as e:
            self.logger.error(f"❌ Error playing greeting audio: {e}")
            
    async def _leave_voice_channel(self):
        """Leave the current voice channel"""
        if self.current_voice_channel:
            try:
                await self.current_voice_channel.disconnect()
                self.logger.info("👋 Left voice channel")
            except Exception as e:
                self.logger.error(f"❌ Error leaving voice channel: {e}")
            finally:
                self.current_voice_channel = None
    
    def _is_channel_blacklisted(self, channel_id: str) -> bool:
        """Check if a channel ID is in the blacklist"""
        if not channel_id:
            return False
            
        # Convert to string to ensure consistent comparison
        channel_id_str = str(channel_id)
        
        self.logger.info(f"🔍 Checking if channel ID '{channel_id_str}' is blacklisted")
        self.logger.info(f"🔍 Blacklist contains: {self.blacklisted_channel_ids}")
        
        # Check if the channel ID is in the blacklist
        is_blacklisted = channel_id_str in self.blacklisted_channel_ids
        self.logger.info(f"🔍 Channel ID '{channel_id_str}' blacklisted: {is_blacklisted}")
        
        return is_blacklisted
                   
    def _is_server_on_cooldown(self, guild_id: str) -> bool:
        """Check if a server is on cooldown"""
        if guild_id not in self.recruitment_cooldown:
            return False
            
        cooldown_end = self.recruitment_cooldown[guild_id]
        return datetime.now() < cooldown_end
        
    def _set_server_cooldown(self, guild_id: str, hours: int = None):
        """Set cooldown for a server"""
        if hours is None:
            hours = self.server_cooldown_hours
        cooldown_end = datetime.now() + timedelta(hours=hours)
        self.recruitment_cooldown[guild_id] = cooldown_end
        self.logger.info(f"⏰ Set {hours}h cooldown for server {guild_id}")
        
    def get_status(self) -> Dict:
        """Get current recruitment status"""
        return {
            "active": self.recruitment_active,
            "current_channel": self.current_voice_channel.channel.name if self.current_voice_channel else None,
            "current_guild": self.current_voice_channel.guild.name if self.current_voice_channel else None,
            "cooldowns": len(self.recruitment_cooldown),
            "last_scan": self.last_scan_time.isoformat() if self.last_scan_time else None
        }
