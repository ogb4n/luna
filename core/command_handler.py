"""
Command handler for Luna bot
Manages all bot commands separately from main bot logic
"""

import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.bot import LunaBot

class CommandHandler:
    """Handles all bot commands"""
    
    def __init__(self, bot):
        self.bot: 'LunaBot' = bot
    
    async def handle_command(self, message):
        """Route commands to appropriate handlers"""
        command = message.content[1:].lower().strip()  # Remove ! and normalize
        
        # Voice-related commands
        if command == "vocal" or command == "voice":
            await self._handle_voice_find(message)
        elif command.startswith("vocal ") or command.startswith("voice "):
            parts = command.split(" ", 1)
            if len(parts) > 1:
                server_id = parts[1].strip()
                await self._handle_voice_find(message, server_id)
            else:
                await self._handle_voice_find(message)
        elif command == "join" or command.startswith("join "):
            if command.startswith("join "):
                parts = command.split(" ", 1)
                server_id = parts[1].strip() if len(parts) > 1 else None
                await self._handle_voice_join(message, server_id)
            else:
                await self._handle_voice_join(message)
        elif command == "leave" or command == "quit":
            await self._handle_voice_leave(message)
        elif command == "test_voice" or command == "testvoice":
            await self._handle_voice_test(message)
        
        # Vocalization commands
        elif command == "vocalize" or command == "vocalise":
            await self._handle_vocalization_toggle(message)
        elif command.startswith("vocalize_interval ") or command.startswith("vocalise_interval "):
            parts = command.split(" ")
            if len(parts) >= 3:
                try:
                    min_minutes = int(parts[1])
                    max_minutes = int(parts[2])
                    await self._handle_vocalization_interval(message, min_minutes, max_minutes)
                except ValueError:
                    await message.channel.send("❌ Format: `!vocalise_interval <min_minutes> <max_minutes>`")
            else:
                await message.channel.send("❌ Format: `!vocalise_interval <min_minutes> <max_minutes>`")
        
        # System commands
        elif command == "servers" or command == "serveurs":
            await self._handle_list_servers(message)
        elif command == "auto" or command == "autonomous":
            await self._handle_autonomous_toggle(message)
        elif command == "status":
            await self._handle_status(message)
        elif command == "debug" or command == "diagnostic":
            await self._handle_debug(message)
        elif command == "help":
            await self._handle_help(message)
        else:
            await message.channel.send("🤖 Commande inconnue. Tape `!help` pour voir les commandes disponibles.")
    
    async def _handle_voice_find(self, message, server_id=None):
        """Command to find the most interesting voice channel to join"""
        try:
            async with message.channel.typing():
                if server_id:
                    print(f"🔍 Scouting server {server_id} for voice opportunities...")
                    channel_info = await self.bot.discord_api.get_most_filled_voice_channel(server_id)
                    
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
                    channel_info = await self.bot.discord_api.get_most_filled_voice_channel()
                    
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
    
    async def _handle_voice_join(self, message, server_id=None):
        """Command to manually join a voice channel"""
        try:
            if server_id:
                # Try to join voice channel in specific server
                channel_info = await self.bot.discord_api.get_most_filled_voice_channel(server_id)
                if channel_info and channel_info.get('estimated_members', 0) > 0:
                    success = await self.bot.voice_manager.join_voice_channel(channel_info['channel_id'], channel_info['guild_id'])
                    if success:
                        await message.channel.send(f"✅ Rejoint **{channel_info['channel_name']}** dans {channel_info['guild_name']}")
                    else:
                        await message.channel.send(f"❌ Impossible de rejoindre le vocal")
                else:
                    await message.channel.send(f"❌ Aucun vocal actif trouvé sur ce serveur")
            else:
                # Join best voice channel across all servers
                await self.bot.voice_manager.join_best_voice_channel()
                await message.channel.send("🔍 Recherche du meilleur vocal en cours...")
                
        except Exception as e:
            await message.channel.send(f"❌ Erreur : {str(e)[:100]}")
    
    async def _handle_voice_leave(self, message):
        """Command to leave current voice channel"""
        try:
            if self.bot.client.voice_clients:
                voice_client = self.bot.client.voice_clients[0]
                channel_name = voice_client.channel.name
                await voice_client.disconnect()
                await message.channel.send(f"🔌 Déconnecté de **{channel_name}**")
            else:
                await message.channel.send("ℹ️ Pas connecté à un canal vocal")
                
        except Exception as e:
            await message.channel.send(f"❌ Erreur lors de la déconnexion : {str(e)[:100]}")
    
    async def _handle_voice_test(self, message):
        """Test voice connection capabilities"""
        try:
            await message.channel.send("🔍 **Test de connexion vocale...**")
            
            # Check current voice state
            current_voice = None
            if self.bot.client.voice_clients:
                current_voice = self.bot.client.voice_clients[0]
                await message.channel.send(f"🎵 Actuellement connecté à : **{current_voice.channel.name}**")
            
            # Find a test channel
            test_channel = None
            test_guild = None
            
            for guild in self.bot.client.guilds:
                for voice_channel in guild.voice_channels:
                    if len(voice_channel.members) > 0 and not self.bot.voice_manager.is_channel_blacklisted(voice_channel.id):
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
            success = await self.bot.voice_manager.join_voice_channel_with_retry(test_channel, test_guild, max_retries=1)
            
            if success:
                await message.channel.send("✅ **Test réussi !** Connexion vocale fonctionnelle")
                # Disconnect after test
                if self.bot.client.voice_clients:
                    await asyncio.sleep(2)
                    await self.bot.client.voice_clients[0].disconnect()
                    await message.channel.send("🔌 Déconnecté du test")
            else:
                await message.channel.send("❌ **Test échoué** - Connexion vocale impossible")
                await message.channel.send("💡 Ceci peut être une limitation Discord pour les selfbots")
                
        except Exception as e:
            print(f"❌ Error in voice test: {e}")
            await message.channel.send(f"❌ Erreur durant le test : {str(e)[:100]}")
    
    async def _handle_list_servers(self, message):
        """Command to list available servers for scouting"""
        try:
            async with message.channel.typing():
                print(f"🔍 Getting available servers for scouting...")
                
                guilds = await self.bot.discord_api.get_available_guilds()
                
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
    
    async def _handle_autonomous_toggle(self, message):
        """Toggle autonomous recruitment mode"""
        try:
            if not self.bot.recruitment:
                await message.channel.send("❌ Système de recrutement autonome non initialisé")
                return
                
            if self.bot.recruitment.recruitment_active:
                await self.bot.recruitment.stop_autonomous_mode()
                await message.channel.send("🛑 **Mode autonome désactivé**\nLuna arrêtera le recrutement automatique.")
            else:
                await self.bot.recruitment.start_autonomous_mode()
                await message.channel.send("🤖 **Mode autonome activé**\nLuna va automatiquement scanner et rejoindre les canaux vocaux pour recruter.")
                
        except Exception as e:
            print(f"❌ Error toggling autonomous mode: {e}")
            await message.channel.send("❌ Erreur lors de la gestion du mode autonome")
    
    async def _handle_vocalization_toggle(self, message):
        """Toggle random vocalization mode"""
        try:
            if not self.bot.random_vocalizer:
                await message.channel.send("❌ Système de vocalisation aléatoire non initialisé")
                return
                
            if self.bot.random_vocalizer.is_active:
                await self.bot.random_vocalizer.stop_random_vocalization()
                await message.channel.send("🔇 **Vocalisation aléatoire désactivée**\nLuna arrêtera de parler automatiquement.")
            else:
                await self.bot.random_vocalizer.start_random_vocalization()
                await message.channel.send("🎵 **Vocalisation aléatoire activée**\nLuna parlera aléatoirement toutes les 1-10 minutes quand elle est en vocal.")
                
        except Exception as e:
            print(f"❌ Error toggling random vocalization: {e}")
            await message.channel.send("❌ Erreur lors de la gestion de la vocalisation")

    async def _handle_vocalization_interval(self, message, min_minutes: int, max_minutes: int):
        """Set the interval range for random vocalization"""
        try:
            if not self.bot.random_vocalizer:
                await message.channel.send("❌ Système de vocalisation aléatoire non initialisé")
                return
                
            if min_minutes < 1 or max_minutes < 1 or min_minutes >= max_minutes:
                await message.channel.send("❌ L'intervalle doit être: 1 ≤ min < max (en minutes)")
                return
                
            self.bot.random_vocalizer.set_interval_range(min_minutes, max_minutes)
            await message.channel.send(f"⏰ **Intervalle de vocalisation mis à jour**\nNouveau délai: {min_minutes}-{max_minutes} minutes")
            
        except Exception as e:
            print(f"❌ Error setting vocalization interval: {e}")
            await message.channel.send("❌ Erreur lors de la configuration de l'intervalle")
    
    async def _handle_status(self, message):
        """Show current bot status"""
        try:
            if not self.bot.recruitment:
                await message.channel.send("❌ Système de recrutement non initialisé")
                return
                
            status = self.bot.recruitment.get_status()
            
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
            total_conversations = len(self.bot.memory.user_histories)
            total_invites = sum(1 for user_id in self.bot.memory.server_invites_sent.keys())
            
            status_text += f"\n📈 **Statistiques**\n"
            status_text += f"💬 Conversations actives: {total_conversations}\n"
            status_text += f"🔗 Invitations envoyées: {total_invites}\n"
            
            # Add random vocalization status
            if self.bot.random_vocalizer:
                vocalize_status = self.bot.random_vocalizer.get_status()
                status_text += f"\n🎲 **Vocalisation Aléatoire**\n"
                status_text += f"🎵 Statut: {'🟢 Actif' if vocalize_status['active'] else '🔴 Inactif'}\n"
                status_text += f"📁 Fichiers audio: {vocalize_status['voice_files_count']}\n"
                status_text += f"⏰ Intervalle: {vocalize_status['min_interval_minutes']}-{vocalize_status['max_interval_minutes']} min\n"
                status_text += f"🔌 En vocal: {'✅' if vocalize_status['connected_to_voice'] else '❌'}\n"
            
            await message.channel.send(status_text)
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            await message.channel.send("❌ Erreur lors de la récupération du statut")
    
    async def _handle_debug(self, message):
        """Debug voice channel member detection"""
        try:
            debug_text = "🔧 **Diagnostic Luna (Selfbot)**\n\n"
            
            # Selfbot info
            debug_text += f"**🤖 Type de Bot:**\n"
            debug_text += f"• Mode: Selfbot (token utilisateur)\n"
            debug_text += f"• Permissions: Identiques à l'utilisateur\n\n"
            
            # Check guilds and voice channels
            total_guilds = len(self.bot.client.guilds)
            total_voice_channels = sum(len(guild.voice_channels) for guild in self.bot.client.guilds)
            active_voice_channels = 0
            total_voice_members = 0
            
            debug_text += f"**📊 Serveurs et Canaux:**\n"
            debug_text += f"• Serveurs accessibles: {total_guilds}\n"
            debug_text += f"• Canaux vocaux totaux: {total_voice_channels}\n"
            
            # Sample voice channel analysis
            sample_guilds = list(self.bot.client.guilds)[:3]  # First 3 guilds
            
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
            if self.bot.client.voice_clients:
                voice_client = self.bot.client.voice_clients[0]
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
    
    async def _handle_help(self, message):
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
