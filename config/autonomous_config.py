"""
Configuration file for Luna's autonomous recruitment system
"""

# Autonomous recruitment settings
AUTONOMOUS_RECRUITMENT = {
    # Timing settings (in seconds)
    "scan_interval": 600,  # 10 minutes between scans
    "min_recruitment_time": 600,  # 10 minutes minimum in channel
    "max_recruitment_time": 1800,  # 30 minutes maximum in channel
    
    # Channel selection criteria
    "min_members_threshold": 2,  # Minimum members to consider joining
    "max_members_threshold": 7,  # Maximum members to avoid overcrowded channels
    "optimal_member_range": (3, 8),  # Sweet spot for recruitment
    
    # Voice connection settings
    "auto_voice_connect": True,  # Enable/disable automatic voice connection
    "voice_retry_attempts": 3,  # Number of retry attempts for voice connection
    "voice_connection_timeout": 10,  # Timeout for voice connection in seconds
    
    # Cooldown settings (in hours)
    "server_cooldown_hours": 1,  # Cooldown after visiting a server
    
    # Scoring weights for channel selection
    "scoring": {
        "member_count_weight": 1.0,
        "server_size_bonus_weight": 0.5,
        "random_factor_range": (0.8, 1.2)
    }
}

# Liste des serveurs autorisés pour la recherche de salons vocaux
# Si cette liste est vide, Luna cherchera dans tous les serveurs disponibles
# Ajoutez les IDs des serveurs où Luna devrait chercher des salons vocaux
ALLOWED_SERVER_IDS = [
    # Exemple: "1234567890123456789",  # ID du serveur autorisé
    # Ajoutez ici les IDs des serveurs où Luna peut chercher des salons vocaux
    "1038108273703919746",  # Shibuya Farm
    "1392123083422302339",  # Kayuna
    "1348410886741557280",  # Kayuma Admin
    "1244629180847624234",  # Yuka
    "1285003543228579911",  # Tropico
    "1253029604021633065",  # K3MINE
    "1399797077030076486",  # Abysse
    "1403011044133310514",  # Shibuya Farm
 
]
# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "luna_recruitment.log"
}

BLACKLISTED_CHANNEL_IDS = [
            # Add specific channel IDs here that Luna should avoid
            # Example: "123456789012345678",  # AFK channel ID
            "1314009824026951680",  # Shibuya Farm tokens
            "1249445642699276318",  # Shibuya Speed Dating
            "1308171005352611941",  # Yuka Admin AFK
]