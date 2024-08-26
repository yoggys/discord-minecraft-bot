# Discord Minecraft Bot

A Discord bot to integrate Minecraft server functionality, allowing users to link their Discord accounts with Minecraft and enabling administrators to manage players via Discord commands.

<img height="150" src="https://github.com/user-attachments/assets/8c634d17-7c53-4342-9439-558f771cc920" alt="/minecraft command example">
<img height="150" src="https://github.com/user-attachments/assets/9eb0359f-d7b1-466b-8f5e-932581e0e057" alt="/admin ban command example">

## Features

- Link your Discord account with a Minecraft server via a `/minecraft` command.
- Administrative commands for managing users, such as banning, checking user data, and whitelisting/removing users.
- Optional support for executing any Minecraft server command via Discord.
- Role-based permission checks and automatic role/server removal handling.

## Commands

### User Commands

- **/minecraft**
  - Link or unlink your Minecraft account.
  - **Arguments**:
    - `username` (optional): Your Minecraft username.

### Admin Commands

- **/admin check**
  - Check user data associated with a Discord or Minecraft account.
  - **Arguments**:
    - `user`: Discord user.
    - `username`: Minecraft username.


- **/admin ban**
  - Ban a user from the Minecraft server.
  - **Arguments**:
    - `user`: Discord user.
    - `username`: Minecraft username.
    - `reason` (optional): Reason for the ban.


- **/admin unban**
  - Unban a user from the Minecraft server.
  - **Arguments**:
    - `user`: Discord user.
    - `username`: Minecraft username.


- **/admin remove**
  - Remove a user from the whitelist.
  - **Arguments**:
    - `user`: Discord user.
    - `username`: Minecraft username.
    - `reason` (optional): Reason for the removal.


- **/admin restart**
  - Restart the connection to the Minecraft server.


- **/root** (optional)
  - Execute any command on the Minecraft server.
  - **Arguments**:
    - `command`: The command to execute.

## Environment Variables

To configure the bot, create a `.env` file in the root of your project with the following environment variables:

```properties
# Discord Bot token
BOT_TOKEN=your_bot_token

# Minecraft server RCON details
HOST=minecraft_server_host
PASSWORD=minecraft_server_password
PORT=minecraft_server_port

# Optional: Enable admin commands (set to True)
ADMIN_COMMANDS=true

# Optional: Enable role/server removal check (set to True)
EXPIRES=true
CHECK_INTERVAL=interval_in_seconds
GUILD_ID=guild_id_to_check

# Optional: Comma-separated role IDs allowed to manage Minecraft usernames
ALLOWED_ROLES=role_id1,role_id2

# Optional: Logs channel ID for tracking connections
LOGS_CHANNEL=logs_channel_id
```

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yoggys/discord-minecraft-bot.git
   cd discord-minecraft-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the `server.properties` file** within your Minecraft server directory to enable RCON access:
   ```properties
   # Enable RCON and set its properties
   rcon.port=25575                     # Set the RCON port (default: 25575)
   broadcast-rcon-to-ops=true          # Allow broadcasting RCON messages to ops
   enable-rcon=true                    # Enable RCON functionality
   rcon.password=your_password         # Set a strong password for RCON
   ```

4. **Open RCON Port** for Bot Communication:
   ```bash
   # Linux
   sudo ufw allow 25575/tcp
   
   # Windows
   netsh advfirewall firewall add rule name="Allow RCON Port" dir=in action=allow protocol=TCP localport=25575
   ```

5. **Configure the `.env` file** with your bot token, Minecraft server credentials, and other optional settings.

6. **Run the bot**:
   ```bash
   python main.py
   ```

## Requirements

- Python 3.8+
- SQLite (default database)

## Database

This bot uses SQLite as the default database. On startup, the bot will automatically generate the required schemas using Tortoise ORM.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
