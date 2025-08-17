from datetime import datetime
from config.settings import MAX_MEMORY_MESSAGES, MEMORY_TIMEOUT
from core.response_algorithm import ResponseAlgorithm, ResponseType

class ConversationMemory:
    def __init__(self):
        self.memory = {}
        self.response_algorithm = ResponseAlgorithm()
    
    def get_context(self, user_id: str, user_name: str) -> list:
        """Get conversation history for a user"""
        if user_id not in self.memory:
            self.memory[user_id] = {
                'messages': [],
                'last_activity': datetime.now(),
                'user_name': user_name,
                'server_invite_sent': False  # Track if server invite was already sent
            }
        
        if datetime.now() - self.memory[user_id]['last_activity'] > MEMORY_TIMEOUT:
            self.memory[user_id]['messages'] = []
            self.memory[user_id]['server_invite_sent'] = False  # Reset invite tracking
        
        return self.memory[user_id]['messages']
    
    def update(self, user_id: str, user_name: str, user_message: str, ai_response: str):
        """Update conversation memory with new exchange"""
        if user_id not in self.memory:
            self.memory[user_id] = {
                'messages': [],
                'last_activity': datetime.now(),
                'user_name': user_name,
                'server_invite_sent': False
            }
        
        # Add new exchange
        self.memory[user_id]['messages'].append({
            'user': user_message,
            'luna': ai_response,
            'timestamp': datetime.now()
        })
        
        # Keep only last MAX_MEMORY_MESSAGES
        if len(self.memory[user_id]['messages']) > MAX_MEMORY_MESSAGES:
            self.memory[user_id]['messages'] = self.memory[user_id]['messages'][-MAX_MEMORY_MESSAGES:]
        
        # Update last activity
        self.memory[user_id]['last_activity'] = datetime.now()
    
    def format_history(self, messages: list) -> str:
        """Format conversation history for AI prompt"""
        if not messages:
            return "Première conversation avec cet utilisateur."
        
        history = "Historique récent de la conversation:\n"
        for msg in messages[-5:]:  # Only show last 5 exchanges
            history += f"Utilisateur: {msg['user']}\n"
            history += f"Luna: {msg['luna']}\n\n"
        
        return history
    
    def decide_response_type(self, user_id: str, user_message: str) -> ResponseType:
        """Decide whether to respond with text or voice using the algorithm"""
        conversation_history = self.get_context(user_id, "")
        return self.response_algorithm.decide_response_type(user_id, user_message, conversation_history)
    
    def force_response_type(self, user_id: str, response_type: ResponseType) -> ResponseType:
        """Force a specific response type for testing or special cases"""
        return self.response_algorithm.force_response_type(user_id, response_type)
    
    def get_user_response_stats(self, user_id: str) -> dict:
        """Get user's response type statistics"""
        return self.response_algorithm.get_user_stats(user_id)
    
    def has_server_invite_been_sent(self, user_id: str) -> bool:
        """Check if server invite has already been sent to this user"""
        if user_id not in self.memory:
            return False
        return self.memory[user_id].get('server_invite_sent', False)
    
    def mark_server_invite_sent(self, user_id: str):
        """Mark that server invite has been sent to this user"""
        if user_id in self.memory:
            self.memory[user_id]['server_invite_sent'] = True
            print(f"🔗 Server invite marked as sent for user {user_id}")
