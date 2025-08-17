import discord
import os
import logging
import asyncio
import random
from core.memory import ConversationMemory
from core.response_algorithm import ResponseType
from voice.tts_engine import TTSEngine
from ai.gemini_client import GeminiClient
from utils.discord_api import DiscordAPI
from config.settings import LUNA_SERVER_INVITE
from config.autonomous_config import BLACKLISTED_CHANNEL_IDS, AUTONOMOUS_RECRUITMENT, ALLOWED_SERVER_IDS
from core.autonomous_recruitment import AutonomousRecruitment
from voice.random_vocalizer import RandomVocalizer

class LunaBot:
    def __init__(self):
        self.memory = ConversationMemory()
        self.tts = TTSEngine()
        self.ai = GeminiClient()
        self.discord_api = DiscordAPI()
        
        # Blacklist of channel IDs that Luna should avoid
        self.blacklisted_channel_ids = BLACKLISTED_CHANNEL_IDS
        
        # Initialize autonomous recruitment
        self.recruitment = None
        
        # Initialize random vocalizer
        self.random_vocalizer = None
        
        # Create selfbot client (no special intents needed for selfbots)
        self.client = discord.Client()
        
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
    
    async def on_ready(self):
        print(f"🤖 Bot connected as {self.client.user}")
        
        # Initialize autonomous recruitment system
        self.recruitment = AutonomousRecruitment(self)
        
        # Initialize random vocalizer
        self.random_vocalizer = RandomVocalizer(self)
        
        await asyncio.sleep(5)  # Shorter delay for faster startup
        
        # Check if auto voice connection is enabled
        if AUTONOMOUS_RECRUITMENT.get("auto_voice_connect", True):
            # Find and join the most active voice channel immediately
            await self._join_best_voice_channel_on_startup()
        else:
            print("🔇 Auto voice connection disabled in config")
        
        # Start autonomous recruitment system
        await asyncio.sleep(5)  # Additional delay before starting autonomous mode
        await self.recruitment.start_autonomous_mode()
        print("🎯 Autonomous recruitment system activated!")
        
        # Start random vocalization (will only work when connected to voice)
        await self.random_vocalizer.start_random_vocalization()
        print("🎵 Random vocalization system activated!")
    
    async def on_message(self, message):
        # For selfbot: respond to DMs from others, not from self
        if message.author == self.client.user or not isinstance(message.channel, discord.DMChannel):
            return

        print(f"📥 DM from {message.author.name}: {message.content}")

        # Check for commands first
        if message.content.startswith('!'):
            await self._handle_command(message)
            return

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
            
            # Force text mode for server invitations (but check if user is already in server)
            if self._contains_server_invitation(response_text):
                print("🔗 Server invitation detected - forcing text mode")
                await self._send_text_response(message, response_text)
                
                # Check if user is already in the server
                is_in_server = await self.discord_api.is_user_in_server(str(message.author.id))
                
                if is_in_server:
                    print("🏠 User is already in Luna's server - no need to send invite")
                elif not self.memory.has_server_invite_been_sent(str(message.author.id)):
                    await self._send_server_link(message)
                    self.memory.mark_server_invite_sent(str(message.author.id))
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
    
    async def _join_best_voice_channel_on_startup(self):
        """Find and join the most active voice channel across allowed servers on startup"""
        try:
            print("🔍 Searching for the most active voice channel to join...")
            
            # Get all available servers using Discord client
            all_guilds = self.client.guilds
            
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
                        if self._is_channel_blacklisted(voice_channel.id):
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
                await self._join_voice_channel_with_retry(best_channel, best_guild_info)
            else:
                print("ℹ️ No active voice channels found to join")
                
        except Exception as e:
            print(f"❌ Error in startup voice channel search: {e}")
    
    def _is_channel_blacklisted(self, channel_id: str) -> bool:
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
    
    async def _join_voice_channel(self, channel_id: str, guild_id: str) -> bool:
        """Join a specific voice channel"""
        try:
            guild = self.client.get_guild(int(guild_id))
            if not guild:
                print(f"❌ Could not find guild {guild_id}")
                return False
                
            channel = guild.get_channel(int(channel_id))
            if not channel:
                print(f"❌ Could not find channel {channel_id}")
                return False
                
            # Use the improved retry logic
            return await self._join_voice_channel_with_retry(channel, guild)
            
        except Exception as e:
            print(f"❌ Failed to join voice channel: {e}")
            return False
    
    async def _join_voice_channel_with_retry(self, voice_channel, guild, max_retries=None):
        """Join a voice channel with retry logic and better error handling"""
        if max_retries is None:
            max_retries = AUTONOMOUS_RECRUITMENT.get("voice_retry_attempts", 3)
            
        timeout = AUTONOMOUS_RECRUITMENT.get("voice_connection_timeout", 10)
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries} to join {voice_channel.name}...")
                
                # Check if we're already connected somewhere and disconnect first
                if self.client.voice_clients:
                    print("🔌 Disconnecting from current voice channel...")
                    for vc in self.client.voice_clients:
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
                await self._play_greeting_audio(voice_client)
                
                # Send a casual greeting
                await self._send_startup_greeting_direct(guild, voice_channel)
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
            
    async def _send_startup_greeting(self, guild_id: str, channel_id: str):
        """Send a casual greeting when joining a channel on startup"""
        try:
            guild = self.client.get_guild(int(guild_id))
            if not guild:
                return
                
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

    async def _send_startup_greeting_direct(self, guild, voice_channel):
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

    async def _play_greeting_audio(self, voice_client):
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

    async def _handle_command(self, message):
        """Handle bot commands"""
        command = message.content[1:].lower().strip()  # Remove ! and normalize
        
        if command == "vocal" or command == "voice":
            await self._command_find_voice_channel(message)
        elif command.startswith("vocal ") or command.startswith("voice "):
            # Extract server ID from command
            parts = command.split(" ", 1)
            if len(parts) > 1:
                server_id = parts[1].strip()
                await self._command_find_voice_channel(message, server_id)
            else:
                await self._command_find_voice_channel(message)
        elif command == "join" or command.startswith("join "):
            # Join voice channel command
            if command.startswith("join "):
                parts = command.split(" ", 1)
                server_id = parts[1].strip() if len(parts) > 1 else None
                await self._command_join_voice(message, server_id)
            else:
                await self._command_join_voice(message)
        elif command == "leave" or command == "quit":
            await self._command_leave_voice(message)
        elif command == "test_voice" or command == "testvoice":
            await self._command_test_voice_connection(message)
        elif command == "servers" or command == "serveurs":
            await self._command_list_servers(message)
        elif command == "auto" or command == "autonomous":
            await self._command_toggle_autonomous(message)
        elif command == "vocalize" or command == "vocalise":
            await self._command_toggle_random_vocalization(message)
        elif command.startswith("vocalize_interval ") or command.startswith("vocalise_interval "):
            # Extract interval parameters
            parts = command.split(" ")
            if len(parts) >= 3:
                try:
                    min_minutes = int(parts[1])
                    max_minutes = int(parts[2])
                    await self._command_set_vocalization_interval(message, min_minutes, max_minutes)
                except ValueError:
                    await message.channel.send("❌ Format: `!vocalise_interval <min_minutes> <max_minutes>`")
            else:
                await message.channel.send("❌ Format: `!vocalise_interval <min_minutes> <max_minutes>`")
        elif command == "status":
            await self._command_status(message)
        elif command == "debug" or command == "diagnostic":
            await self._command_debug(message)
        elif command == "help":
            await self._command_help(message)
        else:
            await message.channel.send("🤖 Commande inconnue. Tape `!help` pour voir les commandes disponibles.")
    
    async def _command_find_voice_channel(self, message, server_id=None):
        """Command to find the most interesting voice channel to join"""
        try:
            async with message.channel.typing():
                if server_id:
                    print(f"🔍 Scouting server {server_id} for voice opportunities...")
                    channel_info = await self.discord_api.get_most_filled_voice_channel(server_id)
                    
                    if channel_info:
                        # Check if any members are actually connected
                        if channel_info['estimated_members'] == 0:
                            await message.channel.send(
                                f"🏠 **{channel_info['guild_name']}**\n"
                                f"❌ Aucun vocal actif trouvé (tous vides)\n"
                                f"💡 Essaie plus tard quand il y aura du monde !"
                            )
                            return
                        
                        await message.channel.send(
                            f"🎯 **Mission de recrutement :**\n\n"
                            f"🏠 **Serveur :** {channel_info['guild_name']}\n"
                            f"🎵 **Vocal cible :** {channel_info['channel_name']}\n"
                            f"👥 **Membres connectés :** {channel_info['estimated_members']}\n"
                            f"🔗 **ID :** `{channel_info['channel_id']}`\n\n"
                            f"💡 **Stratégie :** Rejoins ce vocal et ramène des gens sur mon serveur !"
                        )
                    else:
                        await message.channel.send(f"❌ Impossible de scanner le serveur `{server_id}` ou aucun vocal trouvé")
                        
                else:
                    print(f"🔍 Looking for voice channels in Luna's server...")
                    channel_info = await self.discord_api.get_most_filled_voice_channel()
                    
                    if channel_info:
                        if channel_info['estimated_members'] == 0:
                            await message.channel.send(
                                f"🏠 **{channel_info['guild_name']}**\n"
                                f"❌ Aucun vocal actif (tous vides)\n"
                                f"💡 Utilise `!servers` pour scouter d'autres serveurs !"
                            )
                            return
                            
                        await message.channel.send(
                            f"🎵 **{channel_info['guild_name']}**\n"
                            f"Vocal principal : **{channel_info['channel_name']}**\n"
                            f"👥 Membres connectés : {channel_info['estimated_members']}\n"
                            f"🔗 ID : `{channel_info['channel_id']}`\n"
                            f"💡 Va voir si il y a du monde !"
                        )
                    else:
                        await message.channel.send(
                            f"❌ Aucun vocal actif trouvé sur mon serveur\n"
                            f"💡 Utilise `!servers` pour scouter d'autres serveurs !"
                        )
                    
        except Exception as e:
            print(f"❌ Error in voice command: {e}")
            await message.channel.send("❌ Erreur lors de la recherche du vocal")
    
    async def _command_help(self, message):
        """Show available commands"""
        help_text = """🤖 **Commandes Luna disponibles :**

**🎵 Vocal :**
`!vocal` ou `!voice` - Trouve le vocal le plus intéressant sur mon serveur
`!vocal <ID>` ou `!voice <ID>` - Scout un serveur spécifique
`!join [ID]` - Rejoint un canal vocal
`!leave` ou `!quit` - Quitte le canal vocal

**🎲 Vocalisation Aléatoire :**
`!vocalise` ou `!vocalize` - Active/désactive la vocalisation aléatoire
`!vocalise_interval <min> <max>` - Configure l'intervalle (en minutes)

**🤖 Mode Autonome :**
`!auto` ou `!autonomous` - Active/désactive le mode autonome
`!status` - Affiche l'état de Luna et ses statistiques
`!debug` - Diagnostic des permissions et détection vocale

**🕵️ Recrutement :**
`!servers` ou `!serveurs` - Liste les serveurs disponibles pour recrutement

**💡 Aide :**
`!help` - Affiche cette aide

Pour une conversation normale, écris juste sans le ! 😊

**🎯 Mode Autonome :**
Luna peut fonctionner en mode complètement autonome ! Elle va :
- Scanner automatiquement tous les serveurs accessibles
- Rejoindre les canaux vocaux avec 2-15 membres
- Rester 10-30 minutes pour recruter naturellement
- Passer au canal suivant automatiquement
- Éviter les serveurs récemment visités (cooldown 2h)

**🎵 Vocalisation Aléatoire :**
Luna peut parler aléatoirement en utilisant des fichiers audio :
- Place tes fichiers audio dans le dossier `voicefiles/`
- Active avec `!vocalise`
- Configure l'intervalle avec `!vocalise_interval 1 10` (1-10 minutes)
- Fonctionne uniquement quand Luna est connectée en vocal

Use `!auto` pour activer le mode autonome et `!status` pour surveiller l'activité."""
        
        await message.channel.send(help_text)
    
    async def _command_test_voice_connection(self, message):
        """Test voice connection capabilities"""
        try:
            await message.channel.send("🔍 **Test de connexion vocale...**")
            
            # Check current voice state
            current_voice = None
            if self.client.voice_clients:
                current_voice = self.client.voice_clients[0]
                await message.channel.send(f"🎵 Actuellement connecté à : **{current_voice.channel.name}**")
            
            # Find a test channel
            test_channel = None
            test_guild = None
            
            for guild in self.client.guilds:
                for voice_channel in guild.voice_channels:
                    if len(voice_channel.members) > 0 and not self._is_channel_blacklisted(voice_channel.id):
                        test_channel = voice_channel
                        test_guild = guild
                        break
                if test_channel:
                    break
            
            if not test_channel:
                await message.channel.send("❌ Aucun canal vocal avec des membres trouvé pour le test")
                return
            
            await message.channel.send(f"🎯 Test sur : **{test_channel.name}** ({len(test_channel.members)} membres)")
            
            # Disconnect from current if connected
            if current_voice:
                await current_voice.disconnect()
                await asyncio.sleep(1)
            
            # Test connection
            success = await self._join_voice_channel_with_retry(test_channel, test_guild, max_retries=1)
            
            if success:
                await message.channel.send("✅ **Test réussi !** Connexion vocale fonctionnelle")
                # Disconnect after test
                if self.client.voice_clients:
                    await asyncio.sleep(2)
                    await self.client.voice_clients[0].disconnect()
                    await message.channel.send("🔌 Déconnecté du test")
            else:
                await message.channel.send("❌ **Test échoué** - Connexion vocale impossible")
                await message.channel.send("💡 Ceci peut être une limitation Discord pour les selfbots")
                
        except Exception as e:
            print(f"❌ Error in voice test: {e}")
            await message.channel.send(f"❌ Erreur durant le test : {str(e)[:100]}")
    
    async def _command_join_voice(self, message, server_id=None):
        """Command to manually join a voice channel"""
        try:
            if server_id:
                # Try to join voice channel in specific server
                channel_info = await self.discord_api.get_most_filled_voice_channel(server_id)
                if channel_info and channel_info.get('estimated_members', 0) > 0:
                    success = await self._join_voice_channel(channel_info['channel_id'], channel_info['guild_id'])
                    if success:
                        await message.channel.send(f"✅ Rejoint **{channel_info['channel_name']}** dans {channel_info['guild_name']}")
                    else:
                        await message.channel.send(f"❌ Impossible de rejoindre le vocal")
                else:
                    await message.channel.send(f"❌ Aucun vocal actif trouvé sur ce serveur")
            else:
                # Join best voice channel across all servers
                await self._join_best_voice_channel_on_startup()
                await message.channel.send("🔍 Recherche du meilleur vocal en cours...")
                
        except Exception as e:
            await message.channel.send(f"❌ Erreur : {str(e)[:100]}")
    
    async def _command_leave_voice(self, message):
        """Command to leave current voice channel"""
        try:
            if self.client.voice_clients:
                voice_client = self.client.voice_clients[0]
                channel_name = voice_client.channel.name
                await voice_client.disconnect()
                await message.channel.send(f"🔌 Déconnecté de **{channel_name}**")
            else:
                await message.channel.send("ℹ️ Pas connecté à un canal vocal")
                
        except Exception as e:
            await message.channel.send(f"❌ Erreur lors de la déconnexion : {str(e)[:100]}")

    async def _command_list_servers(self, message):
        """Command to list available servers for scouting"""
        try:
            async with message.channel.typing():
                print(f"🔍 Getting available servers for scouting...")
                
                guilds = await self.discord_api.get_available_guilds()
                
                if not guilds:
                    await message.channel.send("❌ Aucun serveur disponible")
                    return
                
                # Format server list
                server_list = "🏠 **Serveurs disponibles pour le recrutement :**\n\n"
                for guild in guilds[:10]:  # Limit to first 10 servers
                    member_count = guild['member_count']
                    server_list += f"• **{guild['name']}** (ID: `{guild['id']}`)\n"
                    server_list += f"  👥 {member_count} membres\n\n"
                
                server_list += "💡 Utilise `!scout <ID>` pour scanner un serveur spécifique"
                
                await message.channel.send(server_list)
                    
        except Exception as e:
            print(f"❌ Error in servers command: {e}")
            await message.channel.send("❌ Erreur lors de la récupération des serveurs")

    async def _command_toggle_autonomous(self, message):
        """Toggle autonomous recruitment mode"""
        try:
            if not self.recruitment:
                await message.channel.send("❌ Système de recrutement autonome non initialisé")
                return
                
            if self.recruitment.recruitment_active:
                await self.recruitment.stop_autonomous_mode()
                await message.channel.send("🛑 **Mode autonome désactivé**\nLuna arrêtera le recrutement automatique.")
            else:
                await self.recruitment.start_autonomous_mode()
                await message.channel.send("🤖 **Mode autonome activé**\nLuna va automatiquement scanner et rejoindre les canaux vocaux pour recruter.")
                
        except Exception as e:
            print(f"❌ Error toggling autonomous mode: {e}")
            await message.channel.send("❌ Erreur lors de la gestion du mode autonome")

    async def _command_status(self, message):
        """Show current bot status"""
        try:
            if not self.recruitment:
                await message.channel.send("❌ Système de recrutement non initialisé")
                return
                
            status = self.recruitment.get_status()
            
            status_text = "📊 **État de Luna**\n\n"
            status_text += f"🤖 Mode autonome: {'🟢 Actif' if status['active'] else '🔴 Inactif'}\n"
            
            if status['current_channel']:
                status_text += f"🎵 Canal vocal: **{status['current_channel']}**\n"
                status_text += f"🏠 Serveur: **{status['current_guild']}**\n"
            else:
                status_text += "🎵 Canal vocal: Aucun\n"
                
            status_text += f"⏰ Serveurs en cooldown: {status['cooldowns']}\n"
            
            if status['last_scan']:
                status_text += f"🔍 Dernier scan: {status['last_scan']}\n"
                
            # Add conversation stats
            total_conversations = len(self.memory.user_histories)
            total_invites = sum(1 for user_id in self.memory.server_invites_sent.keys())
            
            status_text += f"\n📈 **Statistiques**\n"
            status_text += f"💬 Conversations actives: {total_conversations}\n"
            status_text += f"🔗 Invitations envoyées: {total_invites}\n"
            
            # Add random vocalization status
            if self.random_vocalizer:
                vocalize_status = self.random_vocalizer.get_status()
                status_text += f"\n🎲 **Vocalisation Aléatoire**\n"
                status_text += f"🎵 Statut: {'🟢 Actif' if vocalize_status['active'] else '🔴 Inactif'}\n"
                status_text += f"📁 Fichiers audio: {vocalize_status['voice_files_count']}\n"
                status_text += f"⏰ Intervalle: {vocalize_status['min_interval_minutes']}-{vocalize_status['max_interval_minutes']} min\n"
                status_text += f"🔌 En vocal: {'✅' if vocalize_status['connected_to_voice'] else '❌'}\n"
            
            await message.channel.send(status_text)
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            await message.channel.send("❌ Erreur lors de la récupération du statut")

    async def _command_debug(self, message):
        """Debug voice channel member detection"""
        try:
            debug_text = "🔧 **Diagnostic Luna (Selfbot)**\n\n"
            
            # Selfbot info
            debug_text += f"**🤖 Type de Bot:**\n"
            debug_text += f"• Mode: Selfbot (token utilisateur)\n"
            debug_text += f"• Permissions: Identiques à l'utilisateur\n\n"
            
            # Check guilds and voice channels
            total_guilds = len(self.client.guilds)
            total_voice_channels = sum(len(guild.voice_channels) for guild in self.client.guilds)
            active_voice_channels = 0
            total_voice_members = 0
            
            debug_text += f"**📊 Serveurs et Canaux:**\n"
            debug_text += f"• Serveurs accessibles: {total_guilds}\n"
            debug_text += f"• Canaux vocaux totaux: {total_voice_channels}\n"
            
            # Sample voice channel analysis
            sample_guilds = list(self.client.guilds)[:3]  # First 3 guilds
            
            for guild in sample_guilds:
                active_in_guild = 0
                members_in_guild = 0
                
                for voice_channel in guild.voice_channels:
                    member_count = len(voice_channel.members)
                    if member_count > 0:
                        active_in_guild += 1
                        members_in_guild += member_count
                        total_voice_members += member_count
                        
                active_voice_channels += active_in_guild
                debug_text += f"• {guild.name}: {active_in_guild} actifs, {members_in_guild} membres\n"
            
            debug_text += f"\n**🎵 Activité Vocale:**\n"
            debug_text += f"• Canaux actifs: {active_voice_channels}\n"
            debug_text += f"• Membres en vocal: {total_voice_members}\n"
            
            # Check current voice connection
            if self.client.voice_clients:
                voice_client = self.client.voice_clients[0]
                debug_text += f"• Connecté à: {voice_client.channel.name} ({len(voice_client.channel.members)} membres)\n"
            else:
                debug_text += f"• Pas connecté en vocal\n"
            
            if total_voice_members > 0:
                debug_text += f"\n✅ **Détection fonctionnelle !**"
            else:
                debug_text += f"\n⚠️ **Aucune activité vocale détectée**\n"
                debug_text += f"💡 Assure-toi que des gens sont connectés en vocal"
            
            await message.channel.send(debug_text)
            
        except Exception as e:
            print(f"❌ Error in debug command: {e}")
            await message.channel.send("❌ Erreur lors du diagnostic")

    async def _command_toggle_random_vocalization(self, message):
        """Toggle random vocalization mode"""
        try:
            if not self.random_vocalizer:
                await message.channel.send("❌ Système de vocalisation aléatoire non initialisé")
                return
                
            if self.random_vocalizer.is_active:
                await self.random_vocalizer.stop_random_vocalization()
                await message.channel.send("🔇 **Vocalisation aléatoire désactivée**\nLuna arrêtera de parler automatiquement.")
            else:
                await self.random_vocalizer.start_random_vocalization()
                await message.channel.send("🎵 **Vocalisation aléatoire activée**\nLuna parlera aléatoirement toutes les 1-10 minutes quand elle est en vocal.")
                
        except Exception as e:
            print(f"❌ Error toggling random vocalization: {e}")
            await message.channel.send("❌ Erreur lors de la gestion de la vocalisation")

    async def _command_set_vocalization_interval(self, message, min_minutes: int, max_minutes: int):
        """Set the interval range for random vocalization"""
        try:
            if not self.random_vocalizer:
                await message.channel.send("❌ Système de vocalisation aléatoire non initialisé")
                return
                
            if min_minutes < 1 or max_minutes < 1 or min_minutes >= max_minutes:
                await message.channel.send("❌ L'intervalle doit être: 1 ≤ min < max (en minutes)")
                return
                
            self.random_vocalizer.set_interval_range(min_minutes, max_minutes)
            await message.channel.send(f"⏰ **Intervalle de vocalisation mis à jour**\nNouveau délai: {min_minutes}-{max_minutes} minutes")
            
        except Exception as e:
            print(f"❌ Error setting vocalization interval: {e}")
            await message.channel.send("❌ Erreur lors de la configuration de l'intervalle")

    def run(self, token: str):
        """Start the bot"""
        self.client.run(token)
