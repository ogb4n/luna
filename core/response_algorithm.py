import random
from datetime import datetime, timedelta
from enum import Enum

class ResponseType(Enum):
    TEXT = "text"
    VOICE = "voice"

class ResponseAlgorithm:
    def __init__(self):
        # Base probabilities (can be adjusted)
        self.base_voice_probability = 0.8  # 80% chance for voice by default (re-enabled)
        
        # Factors that influence response type
        self.factors = {
            "user_preference": 1.0,      # User seems to prefer voice/text
            "message_length": 1.0,       # Long messages = more likely voice
            "conversation_flow": 1.0,    # Alternate between types
            "time_since_last": 1.0,      # Time since last voice message
            "message_type": 1.0,         # Question vs statement
            "emotional_context": 1.0     # Emotional messages get voice
        }
        
        # Track response history per user
        self.user_response_history = {}
    
    def decide_response_type(self, user_id: str, user_message: str, conversation_history: list) -> ResponseType:
        """
        Intelligent algorithm to decide between text and voice response
        """
        # Initialize user history if needed
        if user_id not in self.user_response_history:
            self.user_response_history[user_id] = {
                'last_responses': [],  # List of (type, timestamp)
                'voice_count': 0,
                'text_count': 0,
                'user_seems_to_prefer': None
            }
        
        user_history = self.user_response_history[user_id]
        
        # Calculate various factors
        factors = self._calculate_factors(user_message, conversation_history, user_history)
        
        # Calculate final voice probability
        voice_probability = self.base_voice_probability
        
        for factor_name, factor_value in factors.items():
            voice_probability *= factor_value
        
        # Ensure probability stays within bounds
        voice_probability = max(0.1, min(0.9, voice_probability))
        
        # Make decision
        random_value = random.random()
        response_type = ResponseType.VOICE if random_value < voice_probability else ResponseType.TEXT
        
        # Update user history
        self._update_user_history(user_id, response_type)
        
        print(f"🎲 Response algorithm: {voice_probability:.2f} voice probability (random: {random_value:.2f}) → {response_type.value}")
        print(f"📊 Factors: {factors}")
        
        return response_type
    
    def _calculate_factors(self, user_message: str, conversation_history: list, user_history: dict) -> dict:
        """Calculate all factors that influence response type decision"""
        factors = {}
        
        # 1. Message length factor
        # Longer messages are more likely to get voice responses (more personal)
        message_length = len(user_message)
        if message_length > 100:
            factors["message_length"] = 1.3
        elif message_length > 50:
            factors["message_length"] = 1.1
        elif message_length < 20:
            factors["message_length"] = 0.8
        else:
            factors["message_length"] = 1.0
        
        # 2. Conversation flow factor
        # Alternate between voice and text to keep variety
        recent_responses = user_history['last_responses'][-3:]  # Last 3 responses
        if len(recent_responses) >= 2:
            last_two_types = [resp[0] for resp in recent_responses[-2:]]
            if last_two_types == [ResponseType.VOICE, ResponseType.VOICE]:
                factors["conversation_flow"] = 0.4  # Less likely to use voice again
            elif last_two_types == [ResponseType.TEXT, ResponseType.TEXT]:
                factors["conversation_flow"] = 1.6  # More likely to use voice
            else:
                factors["conversation_flow"] = 1.0
        else:
            factors["conversation_flow"] = 1.0
        
        # 3. Time since last voice message
        # If it's been a while since voice, increase chance
        if recent_responses:
            last_voice_time = None
            for resp_type, timestamp in reversed(recent_responses):
                if resp_type == ResponseType.VOICE:
                    last_voice_time = timestamp
                    break
            
            if last_voice_time:
                time_diff = datetime.now() - last_voice_time
                if time_diff > timedelta(minutes=10):
                    factors["time_since_last"] = 1.4
                elif time_diff > timedelta(minutes=5):
                    factors["time_since_last"] = 1.2
                else:
                    factors["time_since_last"] = 1.0
            else:
                factors["time_since_last"] = 1.3  # No recent voice message
        else:
            factors["time_since_last"] = 1.0
        
        # 4. Message type factor
        # Questions and emotional messages are more likely to get voice
        message_lower = user_message.lower()
        if any(word in message_lower for word in ['?', 'comment', 'pourquoi', 'que', 'quoi', 'où', 'quand']):
            factors["message_type"] = 1.2  # Questions get more voice
        elif any(word in message_lower for word in ['salut', 'bonjour', 'merci', 'désolé', 'pardon']):
            factors["message_type"] = 1.3  # Greetings and politeness get voice
        else:
            factors["message_type"] = 1.0
        
        # 5. Emotional context factor
        # Emotional words increase voice probability
        emotional_words = [
            'content', 'heureux', 'triste', 'énervé', 'excité', 'surpris',
            'déçu', 'inquiet', 'stressé', 'relaxé', 'amoureux', 'jaloux',
            'fier', 'honte', 'peur', 'courage', 'espoir', 'désespoir',
            'ça va pas', 'super', 'génial', 'nul', 'horrible', 'magnifique'
        ]
        
        if any(word in message_lower for word in emotional_words):
            factors["emotional_context"] = 1.4
        else:
            factors["emotional_context"] = 1.0
        
        # 6. User preference factor (based on conversation history)
        # If user seems to respond more to voice or text, adapt
        total_responses = user_history['voice_count'] + user_history['text_count']
        if total_responses >= 5:  # Enough data to analyze preference
            voice_ratio = user_history['voice_count'] / total_responses
            if voice_ratio > 0.7:
                factors["user_preference"] = 1.1  # User seems to like voice
            elif voice_ratio < 0.3:
                factors["user_preference"] = 0.7  # User seems to prefer text
            else:
                factors["user_preference"] = 1.0
        else:
            factors["user_preference"] = 1.0
        
        return factors
    
    def _update_user_history(self, user_id: str, response_type: ResponseType):
        """Update user response history"""
        user_history = self.user_response_history[user_id]
        
        # Add to response history
        user_history['last_responses'].append((response_type, datetime.now()))
        
        # Keep only last 10 responses
        if len(user_history['last_responses']) > 10:
            user_history['last_responses'] = user_history['last_responses'][-10:]
        
        # Update counters
        if response_type == ResponseType.VOICE:
            user_history['voice_count'] += 1
        else:
            user_history['text_count'] += 1
    
    def force_response_type(self, user_id: str, response_type: ResponseType):
        """Force a specific response type (for testing or special cases)"""
        if user_id not in self.user_response_history:
            self.user_response_history[user_id] = {
                'last_responses': [],
                'voice_count': 0,
                'text_count': 0,
                'user_seems_to_prefer': None
            }
        
        self._update_user_history(user_id, response_type)
        return response_type
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a user's response preferences"""
        if user_id not in self.user_response_history:
            return {"voice_count": 0, "text_count": 0, "total": 0, "voice_ratio": 0.0}
        
        user_history = self.user_response_history[user_id]
        total = user_history['voice_count'] + user_history['text_count']
        voice_ratio = user_history['voice_count'] / total if total > 0 else 0.0
        
        return {
            "voice_count": user_history['voice_count'],
            "text_count": user_history['text_count'],
            "total": total,
            "voice_ratio": voice_ratio
        }
