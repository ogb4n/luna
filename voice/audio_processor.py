from pydub import AudioSegment
from config.settings import AUDIO_CONFIG

class AudioProcessor:
    def __init__(self):
        self.config = AUDIO_CONFIG
    
    def process_audio(self, input_file: str, output_file: str) -> str:
        """Process audio with normalization, filtering, and compression"""
        # Load audio
        audio = AudioSegment.from_mp3(input_file)
        
        # Normalize volume with headroom
        audio = audio.normalize(headroom=self.config["normalize_headroom"])
        
        # Apply high-pass filter to remove low-frequency noise
        audio = audio.high_pass_filter(self.config["high_pass_filter"])
        
        # Apply gentle compression
        compression = self.config["compression"]
        audio = audio.compress_dynamic_range(
            threshold=compression["threshold"],
            ratio=compression["ratio"],
            attack=compression["attack"],
            release=compression["release"]
        )
        
        # Apply low-pass filter for warmth
        audio = audio.low_pass_filter(self.config["low_pass_filter"])
        
        # Subtle volume boost
        audio = audio + self.config["volume_boost"]
        
        # Export to OGG with high quality
        export_config = self.config["export"]
        audio.export(output_file, format="ogg", codec="libopus", 
                     parameters=[
                         "-b:a", export_config["bitrate"],
                         "-vbr", "on",
                         "-application", "audio",
                         "-compression_level", export_config["compression_level"]
                     ])
        
        return output_file
