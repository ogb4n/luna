import discord
import os
from core.memory import ConversationMemory
from core.response_algorithm import ResponseType
from voice.tts_engine import TTSEngine
from ai.gemini_client import GeminiClient
from utils.discord_api import DiscordAPI
from config.settings import LUNA_SERVER_INVITE

class LunaBot:
    def __init__(self):
        self.memory = ConversationMemory()
        self.tts = TTSEngine()
        self.ai = GeminiClient()
        self.discord_api = DiscordAPI()
        
        # Set up Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        self.client = discord.Client(intents=intents)
        
        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
    
    async def on_ready(self):
        print(f"🤖 Bot connected as {self.client.user}")
    
    async def on_message(self, message):
        if message.author == self.client.user or not isinstance(message.channel, discord.DMChannel):
            return

        print(f"📥 DM from {message.author.name}: {message.content}")

        async with message.channel.typing():
            # Get conversation context
            conversation_history = self.memory.get_context(str(message.author.id), message.author.name)
            history_text = self.memory.format_history(conversation_history)
            
            print(f"🧠 Conversation history for {message.author.name}: {len(conversation_history)} messages")
            
            # Decide response type using algorithm
            response_type = self.memory.decide_response_type(str(message.author.id), message.content)
            print(f"🎯 Chosen response type: {response_type.value}")
            
            # Generate AI response
            response_text = await self.ai.generate_response(
                message.content, 
                message.author.name, 
                history_text
            )
            print(f"🤖 AI Response: {response_text}")
            
            # Update conversation memory
            self.memory.update(str(message.author.id), message.author.name, message.content, response_text)
            
            # Force text mode for server invitations
            if self._contains_server_invitation(response_text):
                print("🔗 Server invitation detected - forcing text mode")
                await self._send_text_response(message, response_text)
                await self._send_server_link(message)
            # Send response based on algorithm decision
            elif response_type == ResponseType.VOICE:
                await self._send_voice_response(message, response_text)
            else:
                await self._send_text_response(message, response_text)
    
    async def _send_voice_response(self, message, response_text: str):
        """Send a voice response"""
        try:
            # Generate voice file
            ogg_file_path = await self.tts.generate_voice(response_text)
            
            # Send as a real Discord voice message
            success = await self.discord_api.send_voice_message(message.channel, ogg_file_path)
            
            if not success:
                # Fallback to regular file attachment if voice message fails
                print("🔄 Falling back to regular file attachment...")
                with open(ogg_file_path, "rb") as f:
                    await message.channel.send("🎵 Voice message:", file=discord.File(f, "voice_message.ogg"))
                # Don't fallback to text - we still sent audio
            
            # Clean up files
            try:
                os.remove("response.mp3")
                os.remove(ogg_file_path)
            except:
                pass
                
        except Exception as e:
            print(f"❌ Voice generation failed: {e}")
            # Only fallback to text if voice generation completely fails
            await self._send_text_response(message, response_text)
    
    async def _send_text_response(self, message, response_text: str):
        """Send a text response with personality and realistic typing simulation"""
        import asyncio
        import random
        
        # Calculate realistic typing delay
        # Assume average typing speed of 60-80 WPM (words per minute)
        words = len(response_text.split())
        base_delay = words / 70 * 60  # 70 WPM = realistic speed
        
        # Add some randomness (±20%) and minimum delay
        variation = random.uniform(0.8, 1.2)
        typing_delay = max(1.0, base_delay * variation)  # Minimum 1 second
        
        # Cap maximum delay at 8 seconds (for very long messages)
        typing_delay = min(8.0, typing_delay)
        
        print(f"⌨️ Simulating typing for {words} words: {typing_delay:.1f}s delay")
        
        # Show typing indicator during the delay
        async with message.channel.typing():
            await asyncio.sleep(typing_delay)
        
        # Add some text-specific personality touches
        text_prefixes = [
            "",  # Most of the time no prefix
            "",
            "",
            "",
            "",
            "",
            "",
        ]
        
        prefix = random.choice(text_prefixes)
        formatted_text = f"{prefix}{response_text}"
        
        await message.channel.send(formatted_text)
    
    def _contains_server_invitation(self, text: str) -> bool:
        """Check if the response contains a server invitation"""
        invitation_keywords = [
            "mon serv", "mon serveur", "serveur", "rejoins", "viens plutôt",
            "plus cool", "sympa", "perso", "là-dessus"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in invitation_keywords)
    
    async def _send_server_link(self, message):
        """Send server invitation link as a separate message"""
        import asyncio
        
        # Small delay to feel natural
        await asyncio.sleep(1.0)
        
        # Send the actual server invite link
        await message.channel.send(LUNA_SERVER_INVITE)
    
    def run(self, token: str):
        """Start the bot"""
        self.client.run(token)
