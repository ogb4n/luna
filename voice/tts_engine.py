import edge_tts
import os
from voice.text_optimizer import TextOptimizer
from voice.audio_processor import AudioProcessor
from config.settings import VOICE_CONFIG

class TTSEngine:
    def __init__(self):
        self.optimizer = TextOptimizer()
        self.processor = AudioProcessor()
        

        self.voice_name = "fr-FR-BrigitteNeural" 
        self.rate = "-8%"      
        self.pitch = "-3Hz"     
        self.volume = "+3%"     
    
    async def generate_voice(self, text: str, filename: str = "response.mp3") -> str:
        """Generate voice using Edge-TTS (free and natural)"""
        
        enhanced_text = self.optimizer.optimize_for_speech(text)
        enhanced_text = self.optimizer.optimize_for_fluidity(enhanced_text)
        
        # Handle very short text that might cause Edge-TTS issues
        if len(enhanced_text.strip()) < 3:
            enhanced_text = f"{enhanced_text}."  # Add punctuation to help TTS
        
        print(f"🎵 Generating voice for: '{enhanced_text}'")
        
        try:
            communicate = edge_tts.Communicate(
                enhanced_text,
                voice=self.voice_name,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume
            )
            
            # Generate MP3
            await communicate.save(filename)
            
            
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                raise Exception(f"Generated audio file is empty or doesn't exist")
            
            print(f"✅ Voice file generated: {filename}")
            
        except Exception as e:
            print(f"❌ Edge-TTS failed: {e}")
            print("🔄 Retrying with fallback settings...")
            try:
                communicate = edge_tts.Communicate(
                    enhanced_text,
                    voice="fr-FR-DeniseNeural"  # Fallback to most reliable voice
                )
                await communicate.save(filename)
                
                if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                    raise Exception("Fallback generation also failed")
                    
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
                raise Exception(f"Voice generation completely failed: {e}")
        
        # Process and convert to OGG
        ogg_filename = filename.replace('.mp3', '.ogg')
        return self.processor.process_audio(filename, ogg_filename)