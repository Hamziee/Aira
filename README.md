# Aira - Anime Episode Notification Bot

Aira is a Discord bot that notifies you when new episodes of your favorite anime are released. It uses the AniList API to track anime and provide real-time notifications.

## Add to Discord

[![Add to Discord](https://img.shields.io/badge/Add%20to%20Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/api/oauth2/authorize?client_id=1392614828891443345&permissions=277025729600&scope=bot%20applications.commands%20applications.entitlements)

## Features

- **Channel-Based Notifications**: Get notified in specific channels when new episodes of subscribed anime are released
- **Quick Updates**: Free servers get notifications every 10 minutes, Donator servers get real-time notifications every minute ✨
- **Rich Embeds**: Beautiful Discord embeds with episode information, cover images, and airing schedules
- **Multiple Anime Support**: Subscribe to as many anime as you want in each channel
- **Easy Management**: Simple commands to manage channel subscriptions

## Commands

- `/subscribe [anime_name]` - Subscribe the current channel to notifications for an anime
- `/unsubscribe [anime_name]` - Unsubscribe the current channel from notifications for a specific anime
- `/unsubscribe_all` - Remove all anime subscriptions from the current channel
- `/list` - View all anime subscriptions in the current channel
- `/donator_status` - Check your server's donator status
- `/about` - Show information about the bot and its commands

## Donator Benefits ✨

Support Aira's development and get:
- **Real-time Updates**: Get notified about new episodes every minute instead of every 10 minutes
- **Donator Badge**: Show your support with a special badge on all bot messages
- Support the development of Aira and get the fastest possible notifications for your favorite anime!

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Discord bot token and SKU ID:
```env
DISCORD_TOKEN=your_token_here
PREMIUM_SKU_ID=your_sku_id_here  # Used for donator features
```

3. Set up the bot in Discord Developer Portal:
   - Enable Message Content Intent
   - Enable Server Members Intent
   - Enable Presence Intent
   - Add `bot`, `applications.commands`, and `applications.entitlements` scopes
   - Set up SKU for donator features

4. Run the bot:
```bash
python aira.py
```

## Permissions

By default, only users with the "Manage Channels" permission can use the `/subscribe`, `/unsubscribe`, and `/unsubscribe_all` commands in a channel. Server administrators can customize these permissions through Discord's integration settings.

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