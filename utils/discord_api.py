import aiohttp
import base64
import os
from pydub import AudioSegment
from config.settings import DISCORD_TOKEN, LUNA_SERVER_ID

class DiscordAPI:
    def __init__(self):
        self.token = DISCORD_TOKEN
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.token}"
        }
    
    async def send_voice_message(self, channel, audio_file_path: str) -> bool:
        """Send a real Discord voice message using the Discord API"""
        try:
            file_size = os.path.getsize(audio_file_path)
            
            async with aiohttp.ClientSession() as session:
                # Request upload URL
                upload_data = {
                    "files": [{
                        "filename": "voice-message.ogg",
                        "file_size": file_size,
                        "id": "2"
                    }]
                }
                
                async with session.post(
                    f"https://discord.com/api/v10/channels/{channel.id}/attachments",
                    json=upload_data,
                    headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to get upload URL: {resp.status}")
                        return False
                        
                    upload_response = await resp.json()
                    upload_url = upload_response["attachments"][0]["upload_url"]
                    upload_filename = upload_response["attachments"][0]["upload_filename"]
                
                # Upload file
                with open(audio_file_path, 'rb') as f:
                    file_data = f.read()
                
                upload_headers = {
                    "Content-Type": "audio/ogg",
                    "Authorization": f"{self.token}"
                }
                
                async with session.put(upload_url, data=file_data, headers=upload_headers) as resp:
                    if resp.status not in [200, 201]:
                        print(f"❌ Failed to upload file: {resp.status}")
                        return False
                
                # Get audio duration and create waveform
                audio = AudioSegment.from_ogg(audio_file_path)
                duration_secs = len(audio) / 1000.0
                waveform_data = [128] * 100  # Simple flat waveform
                waveform_b64 = base64.b64encode(bytes(waveform_data)).decode('utf-8')
                
                # Send voice message
                voice_message_data = {
                    "flags": 8192,
                    "attachments": [{
                        "id": "0",
                        "filename": "voice-message.ogg",
                        "uploaded_filename": upload_filename,
                        "duration_secs": duration_secs,
                        "waveform": waveform_b64
                    }]
                }
                
                async with session.post(
                    f"https://discord.com/api/v10/channels/{channel.id}/messages",
                    json=voice_message_data,
                    headers=self.headers
                ) as resp:
                    if resp.status == 200:
                        print("✅ Voice message sent successfully!")
                        return True
                    else:
                        print(f"❌ Failed to send voice message: {resp.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error sending voice message: {e}")
            return False
        
    async def is_user_in_server(self, user_id: str) -> bool:
        """Check if a user is already a member of Luna's server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{LUNA_SERVER_ID}/members/{user_id}",
                    headers=self.headers
                ) as resp:
                    if resp.status == 200:
                        print(f"✅ User {user_id} is already in Luna's server")
                        return True
                    elif resp.status == 404:
                        print(f"❌ User {user_id} is not in Luna's server")
                        return False
                    else:
                        print(f"⚠️ Could not check server membership: {resp.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error checking server membership: {e}")
            return False  
        
    async def get_most_filled_voice_channel(self, guild_id: str = None) -> dict:
        """Get the most filled voice channel in a guild
        
        Args:
            guild_id: Server ID to check. If None, will check Luna's server
            
        Returns:
            dict with 'channel_id', 'guild_id', 'guild_name', 'channel_name', 'estimated_members'
        """
        if guild_id is None:
            from config.settings import LUNA_SERVER_ID
            guild_id = LUNA_SERVER_ID
            
        try:
            async with aiohttp.ClientSession() as session:
                # Get guild information first
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{guild_id}",
                    headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to get guild info for {guild_id}: {resp.status}")
                        return None
                    
                    guild_info = await resp.json()
                    guild_name = guild_info.get('name', 'Unknown Server')
                
                # Get all channels
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{guild_id}/channels",
                    headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to get channels for {guild_name}: {resp.status}")
                        return None
                    
                    channels = await resp.json()
                    voice_channels = [ch for ch in channels if ch['type'] == 2]  # Type 2 is voice channel
                    
                    if not voice_channels:
                        print(f"⚠️ No voice channels found in {guild_name}")
                        return None
                    
                # Get voice states to see who's actually connected
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{guild_id}/voice-states",
                    headers=self.headers
                ) as resp:
                    voice_states = []
                    if resp.status == 200:
                        voice_states = await resp.json()
                    else:
                        print(f"⚠️ Could not get voice states for {guild_name}: {resp.status}")
                        # If we can't get voice states, we can't reliably determine member counts
                        # Return None instead of guessing with empty channels
                        return None
                    
                    # Count members per voice channel
                    channel_member_counts = {}
                    for state in voice_states:
                        channel_id = state.get('channel_id')
                        if channel_id:
                            channel_member_counts[channel_id] = channel_member_counts.get(channel_id, 0) + 1
                    
                    # Find the voice channel with the most members
                    best_channel = None
                    max_members = 0
                    
                    # Only consider channels with actual members
                    for ch in voice_channels:
                        member_count = channel_member_counts.get(ch['id'], 0)
                        if member_count > max_members:
                            max_members = member_count
                            best_channel = ch
                    
                    # If no channels have members, return None (no recruitment opportunity)
                    if not best_channel or max_members == 0:
                        print(f"ℹ️ No active voice channels found in {guild_name} (all empty)")
                        return None
                    
                    actual_members = channel_member_counts.get(best_channel['id'], 0)
                    
                    result = {
                        'channel_id': best_channel['id'],
                        'channel_name': best_channel['name'],
                        'guild_id': guild_id,
                        'guild_name': guild_name,
                        'estimated_members': actual_members,
                        'position': best_channel.get('position', 0)
                    }
                    
                    print(f"🎵 Selected voice channel in {guild_name}: {best_channel['name']} ({actual_members} members connected)")
                    return result
                    
        except Exception as e:
            print(f"❌ Error getting voice channel for guild {guild_id}: {e}")
            return None
        
    async def get_available_guilds(self) -> list:
        """Get list of guilds Luna has access to for voice channel scouting"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://discord.com/api/v10/users/@me/guilds",
                    headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to get guilds: {resp.status}")
                        return []
                    
                    guilds = await resp.json()
                    
                    # Filter and format guild info
                    available_guilds = []
                    for guild in guilds:
                        guild_info = {
                            'id': guild['id'],
                            'name': guild['name'],
                            'member_count': guild.get('approximate_member_count', 'Unknown'),
                            'icon': guild.get('icon')
                        }
                        available_guilds.append(guild_info)
                    
                    print(f"🏠 Found {len(available_guilds)} available servers for voice scouting")
                    return available_guilds
                    
        except Exception as e:
            print(f"❌ Error getting available guilds: {e}")
            return []
