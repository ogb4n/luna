# 🚀 Luna Quick Start Guide

## Startup Behavior

When Luna starts, she will automatically:

1. **🔍 Scan All Servers** (takes ~5 seconds)

   - Analyzes every Discord server she has access to
   - Looks for voice channels with active members
   - Calculates recruitment scores for each channel

2. **🎯 Select Best Target**

   - Prioritizes channels with most members
   - Considers server size as bonus factor
   - Chooses the highest-scoring active voice channel

3. **🎵 Auto-Join Channel**

   - Immediately connects to the best voice channel found
   - Sends a casual greeting in associated text channel
   - Begins recruitment conversation

4. **🤖 Start Autonomous Mode**
   - Activates the autonomous recruitment system
   - Continues current recruitment session
   - Plans future channel rotations

## Example Startup Sequence

```
🤖 Bot connected as Luna#1234
🔍 Searching for the most active voice channel to join...

📊 CoolServer - General Voice: 5 members (score: 5.3)
📊 GameCommunity - Gaming Chat: 3 members (score: 4.1)
📊 MusicLovers - Listening Party: 7 members (score: 7.8)

🎯 Best target found: Listening Party in MusicLovers (7 members)
🎵 Connected to voice channel: Listening Party
✅ Successfully joined Listening Party in MusicLovers
💬 Sent startup greeting: Hey tout le monde ! Comment ça va ? 😊

🤖 Autonomous recruitment system activated!
🔄 Starting recruitment cycle...
🎵 Already connected to Listening Party in MusicLovers
🎯 Continuing recruitment for 23 minutes
```

## Key Features

### ⚡ Immediate Action

- No waiting period - Luna joins a channel within 10 seconds
- Smart targeting - always picks the most active channel
- Cross-server analysis - considers ALL accessible servers

### 🎭 Natural Integration

- Context-aware greetings based on time of day
- Randomized message timing (8-20 seconds delay)
- Authentic conversation style from the start

### 🧠 Smart Scoring System

```python
score = member_count + min(server_size/1000, 5)
```

- Primary factor: number of voice channel members
- Bonus factor: server size (up to +5 points)
- Result: Luna joins the most promising recruitment target

### 🔄 Seamless Transition

- Startup recruitment session integrates with autonomous system
- Natural transition from initial join to ongoing recruitment
- Server cooldowns apply after first session ends

## Testing Your Setup

Run the startup test to see what Luna would choose:

```bash
python test_startup.py
```

This shows:

- All available servers and their voice channels
- Member counts and calculated scores
- Which channel Luna would select and why

## Customization

Edit `core/bot.py` to adjust startup behavior:

```python
# Startup delays
await asyncio.sleep(5)  # Initialization delay
await asyncio.sleep(8, 20)  # Greeting delay range

# Scoring weights
server_bonus = min(guild['member_count'] / 1000, 5)  # Server size bonus
score = member_count + server_bonus  # Total score calculation
```

## Troubleshooting

### "No active voice channels found"

- Ensure Luna has access to servers with active voice channels
- Check that voice channels have at least 1 member
- Verify Luna has permission to view and join voice channels

### "Failed to join voice channel"

- Check Luna has voice channel permissions on target server
- Ensure the voice channel isn't full or restricted
- Verify Luna isn't already connected to another voice channel

### Connection issues

- Confirm Discord token is valid and has voice permissions
- Check internet connection and Discord API status
- Review console logs for specific error messages

---

**🎯 Result**: Luna becomes immediately active and starts recruiting from the moment she comes online, maximizing efficiency and minimizing downtime.
