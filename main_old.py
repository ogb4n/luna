import discord
import asyncio
import os
import google.generativeai as genai
from google.cloud import texttospeech
import aiohttp
import base64
import io
from pydub import AudioSegment
from datetime import datetime, timedelta

TOKEN = "MTM5MTUzNTI1MjIwNzQzNTkyOQ.GIGazN.TcKdOhhs4iC--jvfBds2dcAsa1-0xlW8ooh124"
GEMINI_API_KEY = "AIzaSyDVu05I2xPRHXyHIyF-eYHx8Ue8whnfgQA"

# Configure Google services
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Set Google Cloud credentials - use the same API key for TTS
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""  # Leave empty to use API key
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Conversation memory storage
conversation_memory = {}
MAX_MEMORY_MESSAGES = 10  # Keep last 10 messages per user
MEMORY_TIMEOUT = timedelta(hours=2)  # Clear memory after 2 hours of inactivity

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

client = discord.Client(intents=intents)

async def generate_voice(text, filename="response.mp3"):
    """Generate voice using Google Cloud Text-to-Speech with SSML support"""
    
    # Clean and enhance the text for more natural speech with SSML
    enhanced_text = optimize_text_for_speech_with_ssml(text)
    
    # Initialize Google TTS client
    client = texttospeech.TextToSpeechClient()
    
    # Configure voice selection - French female voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name="fr-FR-Neural2-A",  # High-quality neural voice (female, warm)
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    
    # Configure audio output
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85,  # Slightly slower for natural conversation
        pitch=-2.0,          # Slightly lower pitch for warmth
        volume_gain_db=2.0,  # Slight volume boost
        sample_rate_hertz=24000,  # High quality
    )
    
    # Set input text (can be SSML or plain text)
    synthesis_input = texttospeech.SynthesisInput(ssml=enhanced_text)
    
    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    # Save the MP3 file
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    
    # Convert MP3 to OGG with enhanced audio processing
    ogg_filename = filename.replace('.mp3', '.ogg')
    audio = AudioSegment.from_mp3(filename)
    
    # Enhanced audio processing for more natural sound
    # Normalize volume first with some headroom
    audio = audio.normalize(headroom=2.0)
    
    # Apply gentle high-pass filter to remove low-frequency noise
    audio = audio.high_pass_filter(85)
    
    # Apply very gentle compression with natural settings
    audio = audio.compress_dynamic_range(
        threshold=-16.0,  # Less aggressive threshold
        ratio=2.0,        # Very gentle compression ratio
        attack=15.0,      # Slower attack for natural dynamics
        release=150.0     # Longer release for smoother sound
    )
    
    # Gentle low-pass filter to remove harsh high frequencies
    audio = audio.low_pass_filter(7500)  # Slightly lower for warmer sound
    
    # Very subtle volume boost for clarity
    audio = audio + 1  # +1dB boost (reduced since Google TTS already has volume_gain_db)
    
    # Export with high quality settings for better voice reproduction
    audio.export(ogg_filename, format="ogg", codec="libopus", 
                 parameters=[
                     "-b:a", "128k",         # High bitrate for excellent quality
                     "-vbr", "on",           # Variable bitrate for efficiency
                     "-application", "audio", # Audio application for best quality
                     "-compression_level", "10"  # Maximum compression quality
                 ])
    
    return ogg_filename

async def send_voice_message(channel, audio_file_path):
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
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bot {TOKEN}"
            }
            
            async with session.post(
                f"https://discord.com/api/v10/channels/{channel.id}/attachments",
                json=upload_data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    print(f"❌ Failed to get upload URL: {resp.status}")
                    return False
                    
                upload_response = await resp.json()
                upload_url = upload_response["attachments"][0]["upload_url"]
                upload_filename = upload_response["attachments"][0]["upload_filename"]
            
            with open(audio_file_path, 'rb') as f:
                file_data = f.read()
            
            upload_headers = {
                "Content-Type": "audio/ogg",
                "Authorization": f"Bot {TOKEN}"
            }
            
            async with session.put(upload_url, data=file_data, headers=upload_headers) as resp:
                if resp.status not in [200, 201]:
                    print(f"❌ Failed to upload file: {resp.status}")
                    return False
            
            audio = AudioSegment.from_ogg(audio_file_path)
            duration_secs = len(audio) / 1000.0
            
            # waveform
            waveform_data = [128] * 100  # Simple flat
            waveform_b64 = base64.b64encode(bytes(waveform_data)).decode('utf-8')
            

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
            
            message_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bot {TOKEN}"
            }
            
            async with session.post(
                f"https://discord.com/api/v10/channels/{channel.id}/messages",
                json=voice_message_data,
                headers=message_headers
            ) as resp:
                if resp.status == 200:
                    print("✅ Voice message sent successfully!")
                    return True
                else:
                    print(f"❌ Failed to send voice message: {resp.status}")
                    response_text = await resp.text()
                    print(f"Response: {response_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error sending voice message: {e}")
        return False

def get_conversation_context(user_id, user_name):
    """Get conversation history for a user"""
    if user_id not in conversation_memory:
        conversation_memory[user_id] = {
            'messages': [],
            'last_activity': datetime.now(),
            'user_name': user_name
        }
    
    # Check if conversation is too old and should be reset
    if datetime.now() - conversation_memory[user_id]['last_activity'] > MEMORY_TIMEOUT:
        conversation_memory[user_id]['messages'] = []
    
    return conversation_memory[user_id]['messages']

def update_conversation_memory(user_id, user_name, user_message, ai_response):
    """Update conversation memory with new exchange"""
    if user_id not in conversation_memory:
        conversation_memory[user_id] = {
            'messages': [],
            'last_activity': datetime.now(),
            'user_name': user_name
        }
    
    # Add new exchange
    conversation_memory[user_id]['messages'].append({
        'user': user_message,
        'luna': ai_response,
        'timestamp': datetime.now()
    })
    
    # Keep only last MAX_MEMORY_MESSAGES
    if len(conversation_memory[user_id]['messages']) > MAX_MEMORY_MESSAGES:
        conversation_memory[user_id]['messages'] = conversation_memory[user_id]['messages'][-MAX_MEMORY_MESSAGES:]
    
    # Update last activity
    conversation_memory[user_id]['last_activity'] = datetime.now()

def format_conversation_history(messages):
    """Format conversation history for the AI prompt"""
    if not messages:
        return "Première conversation avec cet utilisateur."
    
    history = "Historique récent de la conversation:\n"
    for msg in messages[-5:]:  # Only show last 5 exchanges to avoid prompt bloat
        history += f"Utilisateur: {msg['user']}\n"
        history += f"Luna: {msg['luna']}\n\n"
    
    return history

def optimize_text_for_speech_with_ssml(text):
    """Optimize text for Google TTS with SSML support for more natural speech"""
    import re
    
    # Clean up any existing malformed SSML first
    text = re.sub(r'<[^>]*>', '', text)  # Remove any existing tags
    
    # Replace common abbreviations with full words for better pronunciation
    replacements = {
        'Mr.': 'Monsieur',
        'Mme.': 'Madame', 
        'Dr.': 'Docteur',
        'etc.': 'et cetera',
        '&': 'et',
        '%': 'pour cent',
        '@': 'arobase',
        'www.': 'w w w point',
        '.com': 'point com',
        '.fr': 'point f r',
        't\'es': 'tu es',    # Some contractions are better expanded
        'y\'a': 'il y a'
    }
    
    for abbrev, full in replacements.items():
        text = text.replace(abbrev, full)
    
    # Ensure proper spacing after punctuation for natural rhythm
    text = re.sub(r',(?!\s)', ', ', text)  # Space after commas
    text = re.sub(r'\.(?!\s)', '. ', text)  # Space after periods
    text = re.sub(r'\?(?!\s)', '? ', text)  # Space after questions
    text = re.sub(r'!(?!\s)', '! ', text)   # Space after exclamations
    
    # Clean up extra spaces
    text = ' '.join(text.split())
    text = text.strip()
    
    # Wrap in SSML with natural prosody for conversational speech
    ssml_text = f'''<speak>
        <prosody rate="0.9" pitch="-1st" volume="medium">
            {text}
        </prosody>
    </speak>'''
    
    return ssml_text

def optimize_text_for_speech(text):
    """Clean and optimize text for natural speech synthesis"""
    import re
    
    # Remove any existing SSML or break tags that might have been added by AI
    text = re.sub(r'<break[^>]*>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace common abbreviations with full words for better pronunciation
    replacements = {
        'Mr.': 'Monsieur',
        'Mme.': 'Madame', 
        'Dr.': 'Docteur',
        'etc.': 'et cetera',
        '&': 'et',
        '%': 'pour cent',
        '@': 'arobase',
        'www.': 'w w w point',
        '.com': 'point com',
        '.fr': 'point f r',
        'c\'est': 'c\'est',  # Keep contractions natural
        'j\'ai': 'j\'ai',
        't\'es': 'tu es',    # Some contractions are better expanded
        'y\'a': 'il y a'
    }
    
    for abbrev, full in replacements.items():
        text = text.replace(abbrev, full)
    
    # Add natural pauses using simple punctuation instead of SSML
    # Replace ellipsis with longer pauses (multiple periods)
    text = text.replace('...', '... ')
    text = text.replace('..', '.. ')
    
    # Ensure proper spacing after punctuation for natural rhythm
    text = re.sub(r',(?!\s)', ', ', text)  # Space after commas
    text = re.sub(r'\.(?!\s)', '. ', text)  # Space after periods
    text = re.sub(r'\?(?!\s)', '? ', text)  # Space after questions
    text = re.sub(r'!(?!\s)', '! ', text)   # Space after exclamations
    
    # Add slight emphasis to common conversation words by repeating them slightly
    emphasis_words = ['vraiment', 'absolument', 'complètement']
    for word in emphasis_words:
        # Add a slight pause before emphasis words
        text = re.sub(f'\\b{word}\\b', f' {word}', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces and normalize
    text = ' '.join(text.split())  # Remove extra whitespace
    text = text.strip()
    
    # Return clean text without SSML - kept for compatibility
    return text

async def generate_ai_response(user_message, user_name, user_id):
    """Generate AI response using Google Gemini with conversation context"""
    try:
        # Get conversation history
        conversation_history = get_conversation_context(user_id, user_name)
        history_text = format_conversation_history(conversation_history)
        
        print(f"🧠 Conversation history for {user_name} ({user_id}): {len(conversation_history)} messages")
        print(f"📜 History context: {history_text}")
        
        prompt = f"""
Tu es Luna, une assistante vocale féminine charmante et séduisante. Tu réponds aux messages de manière chaleureuse, joueuse et légèrement coquette. Tu parles exclusivement en français naturel.

{history_text}

Traits de personnalité essentiels :
- Chaleureuse et amicale avec une pointe de sensualité
- Joueuse et taquine, mais jamais vulgaire
- Bienveillante et à l'écoute
- Tu utilises un langage parlé naturel avec des contractions (j'ai, c'est, t'es, etc.)
- Tu évites ABSOLUMENT les émojis, balises HTML, et caractères spéciaux
- Tu utilises rarement de petites interjections naturelles (oh, eh bien, dis donc, etc.)
- Tu peux faire de légères pauses dans tes phrases avec des virgules
- Tu utilises parfois des expressions familières françaises
- Tu peux répéter certains mots pour l'emphase comme dans la vraie conversation
- Évite les phrases trop longues, privilégie des phrases courtes et rythmées
- Utilise des mots de liaison parlés comme "alors", "bon", "eh bien", "tu vois"

IMPORTANT: Utilise l'historique de conversation pour:
- Te rappeler de ce dont vous avez parlé
- Faire référence aux sujets précédents naturellement
- Maintenir une continuité dans la conversation
- Adapter ton ton selon l'évolution de votre relation

L'utilisateur s'appelle {user_name} et vient de t'envoyer ce message : "{user_message}"

Important pour la synthèse vocale :
- JAMAIS D'EMOJIS, de balises HTML ou de caractères spéciaux
- Tutoie TOUJOURS l'utilisateur
- Écris comme tu parlerais vraiment à l'oral (langage parlé naturel)
- Garde tes réponses très courtes (maximum 2 phrases courtes)
- Privilégie un ton conversationnel et intime
- Écris en français correct sans abréviations bizarres
- Utilise juste de la ponctuation normale (points, virgules, points d'interrogation)
"""
        
        # Make the API call in an executor to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        raw_text = response.text.strip()
        
        print(f"🤖 Generated response: {raw_text}")
        
        # Update conversation memory
        update_conversation_memory(user_id, user_name, user_message, raw_text)
        print(f"💾 Updated memory. Now has {len(conversation_memory[user_id]['messages'])} messages")
        
        return raw_text
        
    except Exception as e:
        print(f"❌ Error with Gemini API: {e}")
        # Fallback response if API fails
        return f"Désolée {user_name}, j'ai un petit souci technique là, mais je suis toujours là pour toi !"

@client.event
async def on_ready():
    print(f"🤖 Bot connecté en tant que {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user or not isinstance(message.channel, discord.DMChannel):
        return

    print(f"📥 DM from {message.author.name}: {message.content}")

    # Add a "typing" indicator to show the bot is working
    async with message.channel.typing():
        # Generate AI response using Gemini with conversation context
        response_text = await generate_ai_response(message.content, message.author.name, message.author.id)
        print(f"🤖 AI Response: {response_text}")

        # Generate voice file (returns .ogg path)
        ogg_file_path = await generate_voice(response_text)

    # Send as a real Discord voice message
    success = await send_voice_message(message.channel, ogg_file_path)
    
    if not success:
        # Fallback to regular file attachment if voice message fails
        print("🔄 Falling back to regular file attachment...")
        with open(ogg_file_path, "rb") as f:
            await message.channel.send("🎵 Voice message:", file=discord.File(f, "voice_message.ogg"))
    
    # Clean up files
    try:
        os.remove("response.mp3")
        os.remove(ogg_file_path)
    except:
        pass

client.run(TOKEN)

async def generate_voice_alternative(text, filename="response.mp3"):
    """Alternative voice generation with different Google TTS voice models"""
    enhanced_text = optimize_text_for_speech_with_ssml(text)
    
    # Initialize Google TTS client
    client = texttospeech.TextToSpeechClient()
    
    # Try different French female voices:
    # voice_options = [
    #     "fr-FR-Neural2-A",       # Natural, warm (current choice)
    #     "fr-FR-Neural2-B",       # Professional, clear
    #     "fr-FR-Neural2-C",       # Young, energetic
    #     "fr-FR-Wavenet-A",       # High-quality WaveNet (female)
    #     "fr-FR-Wavenet-B",       # High-quality WaveNet (male)
    #     "fr-FR-Wavenet-C",       # High-quality WaveNet (female)
    #     "fr-FR-Wavenet-D",       # High-quality WaveNet (male)
    #     "fr-FR-Standard-A",      # Standard quality (female)
    #     "fr-FR-Standard-B",      # Standard quality (male)
    #     "fr-FR-Standard-C",      # Standard quality (female)
    #     "fr-FR-Standard-D"       # Standard quality (male)
    # ]
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name="fr-FR-Neural2-C",  # Alternative energetic voice
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.9,
        pitch=0.0,  # Natural pitch
        volume_gain_db=3.0,
        sample_rate_hertz=24000,
    )
    
    synthesis_input = texttospeech.SynthesisInput(ssml=enhanced_text)
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    
    # Same audio processing as main function
    ogg_filename = filename.replace('.mp3', '.ogg')
    audio = AudioSegment.from_mp3(filename)
    
    audio = audio.normalize(headroom=3.0)
    audio = audio.high_pass_filter(80)
    audio = audio.compress_dynamic_range(
        threshold=-18.0, ratio=2.5, attack=10.0, release=100.0
    )
    audio = audio.low_pass_filter(8000)
    
    audio.export(ogg_filename, format="ogg", codec="libopus", 
                 parameters=["-b:a", "96k", "-vbr", "on", "-application", "audio", "-compression_level", "10"])
    
    return ogg_filename

async def test_voice_quality(test_text="Salut ! Comment ça va ? J'espère que tu passes une bonne journée."):
    """Test function to compare different Google TTS voice settings"""
    print("🎵 Testing voice quality with different Google TTS settings...")
    
    # Test original Neural2-A (warm, natural)
    print("Testing fr-FR-Neural2-A (recommended - warm & natural)...")
    file1 = await generate_voice(test_text, "test_neural2a.mp3")
    
    # Test alternative Neural2-C (energetic)
    print("Testing fr-FR-Neural2-C (energetic alternative)...")
    file2 = await generate_voice_alternative(test_text, "test_neural2c.mp3")
    
    print(f"✅ Generated test files: {file1} and {file2}")
    print("🎧 Listen to both and choose your preferred Google TTS voice!")
    print("💡 Available voices: Neural2-A/B/C (best quality), Wavenet-A/B/C/D (high quality), Standard-A/B/C/D (basic)")
    
    return file1, file2
