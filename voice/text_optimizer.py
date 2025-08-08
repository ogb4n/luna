import re

class TextOptimizer:
    def __init__(self):
        self.replacements = {
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
            't\'es': 'tu es',
            'y\'a': 'il y a'
        }
        
        # Phonetic corrections for young slang in voice synthesis
        self.phonetic_corrections = {
            'wsh': 'wesh',
            'pk': 'pourquoi',
            'tkt': "t'inquiète",
            'oklm': 'au calme',
            'mdr': 'mdr',
            'ptdr': 'ptdr',
            'jsp': 'je sais pas',
            'jpp': 'j\'en peux plus',
            'bg': 'bg',
            'meuf': 'meuf',
            'mec': 'mec',
            'frérot': 'frérot',
            'fréro': 'frérot',
            'srx': 'sérieux',
            'cv': 'ça va',
            'cc': 'coucou',
            'slt': 'salut',
            'bsr': 'bonsoir',
            'bjr': 'bonjour',
            'dac': 'd\'accord',
            'genre': 'genre',
            'ça va ou quoi': 'ça va ou quoi',
            'sa dit quoi': 'ça dit quoi',
            'tes chaud': "t'es chaud",
            'tes bizarre': "t'es bizarre",
            'tes mystérieux': "t'es mystérieux"
        }
        
        self.emphasis_words = ['vraiment', 'absolument', 'complètement']
    
    def optimize_for_speech(self, text: str) -> str:
        """Clean and optimize text for natural speech synthesis"""
        # Remove any existing SSML or break tags
        text = re.sub(r'<break[^>]*>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Apply phonetic corrections for young slang FIRST
        text = self.apply_phonetic_corrections(text)
        
        # Replace abbreviations
        for abbrev, full in self.replacements.items():
            text = text.replace(abbrev, full)
        
        # Add natural pauses
        text = text.replace('...', '... ')
        text = text.replace('..', '.. ')
        
        # Ensure proper spacing after punctuation
        text = re.sub(r',(?!\s)', ', ', text)
        text = re.sub(r'\.(?!\s)', '. ', text)
        text = re.sub(r'\?(?!\s)', '? ', text)
        text = re.sub(r'!(?!\s)', '! ', text)
        
        # Add emphasis to conversation words
        for word in self.emphasis_words:
            text = re.sub(f'\\b{word}\\b', f' {word}', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def apply_phonetic_corrections(self, text: str) -> str:
        """Apply phonetic corrections for young slang and speech patterns"""
        # Apply corrections case-insensitively
        for slang, phonetic in self.phonetic_corrections.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(slang) + r'\b'
            text = re.sub(pattern, phonetic, text, flags=re.IGNORECASE)
        
        return text
    
    def optimize_with_ssml(self, text: str) -> str:
        """Optimize text with SSML support for Google TTS"""
        # Clean up any existing malformed SSML first
        text = re.sub(r'<[^>]*>', '', text)
        
        # Apply basic optimizations
        for abbrev, full in self.replacements.items():
            text = text.replace(abbrev, full)
        
        # Ensure proper spacing
        text = re.sub(r',(?!\s)', ', ', text)
        text = re.sub(r'\.(?!\s)', '. ', text)
        text = re.sub(r'\?(?!\s)', '? ', text)
        text = re.sub(r'!(?!\s)', '! ', text)
        
        # Clean up extra spaces
        text = ' '.join(text.split()).strip()
        
        # Wrap in SSML with natural prosody
        ssml_text = f'''<speak>
            <prosody rate="0.9" pitch="-1st" volume="medium">
                {text}
            </prosody>
        </speak>'''
        
        return ssml_text
