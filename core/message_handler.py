"""
Message handler for Luna bot
Manages DM message processing and responses
"""

import asyncio
import random
import discord
from core.response_algorithm import ResponseType
from config.settings import LUNA_SERVER_INVITE


class MessageHandler:
    """Handles DM message processing and responses"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_dm_message(self, message):
        """Process DM messages and generate responses"""
        print(f"📥 DM from {message.author.name}: {message.content}")

        async with message.channel.typing():
            # Get conversation context
            conversation_history = self.bot.memory.get_context(str(message.author.id), message.author.name)
            history_text = self.bot.memory.format_history(conversation_history)
            
            print(f"🧠 Conversation history for {message.author.name}: {len(conversation_history)} messages")
            
            # Decide response type using algorithm
            response_type = self.bot.memory.decide_response_type(str(message.author.id), message.content)
            print(f"🎯 Chosen response type: {response_type.value}")
            
            # Generate AI response
            response_text = await self.bot.ai.generate_response(
                message.content, 
                message.author.name, 
                history_text
            )
            print(f"🤖 AI Response: {response_text}")
            
            # Update conversation memory
            self.bot.memory.update(str(message.author.id), message.author.name, message.content, response_text)
            
            # Force text mode for server invitations (but check if user is already in server)
            if self._contains_server_invitation(response_text):
                print("🔗 Server invitation detected - forcing text mode")
                await self._send_text_response(message, response_text)
                
                # Check if user is already in the server
                is_in_server = await self.bot.discord_api.is_user_in_server(str(message.author.id))
                
                if is_in_server:
                    print("🏠 User is already in Luna's server - no need to send invite")
                elif not self.bot.memory.has_server_invite_been_sent(str(message.author.id)):
                    await self._send_server_link(message)
                    self.bot.memory.mark_server_invite_sent(str(message.author.id))
                else:
                    print("🔗 Server invite already sent to this user - skipping")
            # Send response based on algorithm decision
            elif response_type == ResponseType.VOICE:
                await self._send_voice_response(message, response_text)
            else:
                await self._send_text_response(message, response_text)
    
    async def _send_voice_response(self, message, response_text: str):
        """Send a voice response"""
        try:
            # Generate voice file
            ogg_file_path = await self.bot.tts.generate_voice(response_text)
            
            # Send as a real Discord voice message
            success = await self.bot.discord_api.send_voice_message(message.channel, ogg_file_path)
            
            if not success:
                # Fallback to regular file attachment if voice message fails
                print("🔄 Falling back to regular file attachment...")
                with open(ogg_file_path, "rb") as f:
                    await message.channel.send("🎵 Voice message:", file=discord.File(f, "voice_message.ogg"))
                # Don't fallback to text - we still sent audio
            
            # Clean up files
            try:
                import os
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
        # Small delay to feel natural
        await asyncio.sleep(1.0)
        
        # Send the actual server invite link
        await message.channel.send(LUNA_SERVER_INVITE)
