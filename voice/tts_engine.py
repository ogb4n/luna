import edge_tts
from voice.text_optimizer import TextOptimizer
from voice.audio_processor import AudioProcessor
from config.settings import VOICE_CONFIG

class TTSEngine:
    def __init__(self):
        self.optimizer = TextOptimizer()
        self.processor = AudioProcessor()
        # Edge-TTS configuration
        self.voice_name = "fr-FR-DeniseNeural"  # Fallback to more reliable voice
        self.rate = "-10%"      # Slightly slower for intimacy
        self.pitch = "+0Hz"     # Natural pitch (not too high)
        self.volume = "+0%"     # Normal volume, processed later
    
    async def generate_voice(self, text: str, filename: str = "response.mp3") -> str:
        """Generate voice using Edge-TTS (free and natural)"""
        
        # Optimize text for speech (no SSML needed for Edge-TTS)
        enhanced_text = self.optimizer.optimize_for_speech(text)
        
        # Use Edge-TTS with optimized settings
        communicate = edge_tts.Communicate(
            enhanced_text,
            voice=self.voice_name,
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume
        )
        
        # Generate MP3
        await communicate.save(filename)
        
        # Process and convert to OGG
        ogg_filename = filename.replace('.mp3', '.ogg')
        return self.processor.process_audio(filename, ogg_filename)
    
    def get_available_voices(self) -> list:
        """Get list of available French voices for Edge-TTS"""
        # Common French voices available in Edge-TTS
        return [
            ("fr-FR-BrigitteNeural", "female"),  # Mature, warm (RECOMMENDED)
            ("fr-FR-EloiseNeural", "female"),    # Gentle, conversational  
            ("fr-FR-DeniseNeural", "female"),    # Young, can sound childish
            ("fr-FR-JosephineNeural", "female"), # Energetic, young
            ("fr-FR-HenriNeural", "male"),       # Professional male
            ("fr-FR-AlainNeural", "male"),       # Casual male
        ]
    
    def change_voice(self, voice_name: str):
        """Change the voice for future generations"""
        self.voice_name = voice_name
        print(f"🎵 Voice changed to: {voice_name}")
    
    def adjust_speech_rate(self, rate: str):
        """Adjust speech rate (e.g., '-20%', '+10%')"""
        self.rate = rate
        print(f"🎵 Speech rate changed to: {rate}")
    
    def adjust_pitch(self, pitch: str):
        """Adjust pitch (e.g., '+5Hz', '-2Hz')"""
        self.pitch = pitch
        print(f"🎵 Pitch changed to: {pitch}")
