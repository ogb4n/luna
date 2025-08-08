import aiohttp
import base64
import os
from pydub import AudioSegment
from config.settings import DISCORD_TOKEN

class DiscordAPI:
    def __init__(self):
        self.token = DISCORD_TOKEN
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bot {self.token}"
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
                    "Authorization": f"Bot {self.token}"
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
