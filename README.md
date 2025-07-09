# Aira - Anime Episode Notification Bot

Aira is a Discord bot that notifies you when new episodes of your favorite anime are released. It uses the AniList API to track anime and provide real-time notifications.

## Add to Discord

[![Add to Discord](https://img.shields.io/badge/Add%20to%20Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1392614828891443345&permissions=277025729600&integration_type=0&scope=bot)

## Features

- **Episode Notifications**: Get notified when new episodes of your subscribed anime are released
- **Quick Updates**: Checks for new episodes every 10 minutes
- **Rich Embeds**: Beautiful Discord embeds with episode information, cover images, and airing schedules
- **Multiple Anime Support**: Subscribe to as many anime as you want per channel
- **Easy Management**: Simple commands to manage your subscriptions

## Commands

- `/subscribe [anime_name]` - Subscribe to notifications for an anime in the current channel
- `/unsubscribe [anime_name]` - Unsubscribe from notifications for a specific anime
- `/unsubscribe_all` - Unsubscribe from all anime notifications in the current channel
- `/list` - View all your current anime subscriptions
- `/about` - Show information about the bot and its commands

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Discord bot token:
```env
DISCORD_TOKEN=your_token_here
```

3. Run the bot:
```bash
python aira.py
```

## Permissions

By default, only users with the "Manage Channels" permission can use the `/subscribe`, `/unsubscribe`, and `/unsubscribe_all` commands. Server administrators can customize these permissions through Discord's integration settings.

### How to Change Permissions

1. Go to your Discord server settings
2. Navigate to Integrations
3. Find and click on Aira
4. Under Commands, you will see a list of all available slash commands
5. Click on a command to adjust its permissions
6. Add or remove roles/users and specify whether they can use the command

## Data Source

Aira uses the [AniList API](https://anilist.co/graphiql) to fetch anime information, ensuring accurate and up-to-date data about airing schedules and episodes.

## Hosting

Hosted with ❤️ by [heo-systems.net](https://heo-systems.net)

## Support

If you encounter any issues or have questions, please make an issue