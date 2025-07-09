import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from database import Database
from anilist_api import AniListAPI

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()
anilist = AniListAPI()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await db.init_db()
    await bot.tree.sync()
    if not check_new_episodes.is_running():
        check_new_episodes.start()

@bot.tree.command(name='subscribe', description='Subscribe to notifications for new episodes of an anime.')
async def subscribe(interaction: discord.Interaction, anime_name: str):
    await interaction.response.defer()
    anime_list = anilist.search_anime(anime_name)
    
    if not anime_list:
        await interaction.followup.send('Could not find any anime with that name.')
        return

    if len(anime_list) == 1:
        anime = anime_list[0]
        channel_id = str(interaction.channel.id)
        
        subs = await db.get_channel_subscriptions(channel_id)
        if any(sub['id'] == anime['id'] for sub in subs):
            await interaction.followup.send(f"You are already subscribed to {anime['title']['romaji']}.")
            return

        await db.add_subscription(
            channel_id=channel_id,
            anime_id=anime['id'],
            title=anime['title']['romaji'],
            episodes=anime.get('episodes', 0)
        )

        embed = discord.Embed(
            title="✅ Subscription Added!",
            description=f"You will now receive notifications for new episodes of {anime['title']['romaji']}",
            color=discord.Color.green()
        )

        if anime['title']['english']:
            embed.add_field(name="English Title", value=anime['title']['english'], inline=True)

        if anime.get('episodes'):
            embed.add_field(name="Total Episodes", value=str(anime['episodes']), inline=True)
        
        if anime.get('nextAiringEpisode'):
            embed.add_field(
                name="Next Episode",
                value=anilist.format_airing_info(anime['nextAiringEpisode']),
                inline=False
            )

        if anime.get('coverImage', {}).get('medium'):
            embed.set_thumbnail(url=anime['coverImage']['medium'])

        if anime.get('genres'):
            embed.add_field(name="Genres", value=", ".join(anime['genres'][:3]), inline=True)

        await interaction.followup.send(embed=embed)
    else:
        select = discord.ui.Select(
            placeholder="Select an anime",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=f"{anime['title']['romaji'][:100]}",
                    description=f"Episodes: {anime.get('episodes', '?')} | Score: {anime.get('averageScore', '?')}",
                    value=str(anime['id'])
                )
                for anime in anime_list
            ]
        )

        async def select_callback(select_interaction: discord.Interaction):
            anime_id = int(select.values[0])
            selected_anime = next((a for a in anime_list if a['id'] == anime_id), None)
            
            if selected_anime:
                channel_id = str(interaction.channel.id)
                
                subs = await db.get_channel_subscriptions(channel_id)
                if any(sub['id'] == selected_anime['id'] for sub in subs):
                    await select_interaction.response.edit_message(
                        content=f"You are already subscribed to {selected_anime['title']['romaji']}.",
                        view=None
                    )
                    return

                await db.add_subscription(
                    channel_id=channel_id,
                    anime_id=selected_anime['id'],
                    title=selected_anime['title']['romaji'],
                    episodes=selected_anime.get('episodes', 0)
                )

                embed = discord.Embed(
                    title="✅ Subscription Added!",
                    description=f"You will now receive notifications for new episodes of {selected_anime['title']['romaji']}",
                    color=discord.Color.green()
                )

                if selected_anime['title']['english']:
                    embed.add_field(
                        name="English Title",
                        value=selected_anime['title']['english'],
                        inline=True
                    )

                if selected_anime.get('episodes'):
                    embed.add_field(
                        name="Total Episodes",
                        value=str(selected_anime['episodes']),
                        inline=True
                    )
                
                if selected_anime.get('nextAiringEpisode'):
                    embed.add_field(
                        name="Next Episode",
                        value=anilist.format_airing_info(selected_anime['nextAiringEpisode']),
                        inline=False
                    )

                if selected_anime.get('coverImage', {}).get('medium'):
                    embed.set_thumbnail(url=selected_anime['coverImage']['medium'])

                if selected_anime.get('genres'):
                    embed.add_field(
                        name="Genres",
                        value=", ".join(selected_anime['genres'][:3]),
                        inline=True
                    )

                await select_interaction.response.edit_message(embed=embed, view=None)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.followup.send("Multiple anime found. Please select one:", view=view)

@bot.tree.command(name='list', description='Lists all anime subscriptions in this channel.')
async def list_anime(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)
    subscriptions = await db.get_channel_subscriptions(channel_id)
    
    if subscriptions:
        embed = discord.Embed(
            title="📺 Anime Subscriptions",
            description="Here are your current subscriptions:",
            color=discord.Color.blue()
        )

        for sub in subscriptions:
            anime_data = anilist.get_anime_details(sub['id'])
            if anime_data:
                value_parts = []
                
                if anime_data.get('episodes'):
                    value_parts.append(f"Episodes: {sub['episodes']}/{anime_data['episodes']}")
                
                if anime_data.get('nextAiringEpisode'):
                    value_parts.append(anilist.format_airing_info(anime_data['nextAiringEpisode']))
                elif anime_data.get('status') == 'FINISHED':
                    value_parts.append("Series completed")
                
                embed.add_field(
                    name=anime_data['title']['romaji'],
                    value="\n".join(value_parts) or "No airing information available",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "There are no anime subscriptions in this channel.",
            ephemeral=True
        )

@bot.tree.command(name='unsubscribe', description='Stop notifications for an anime.')
async def unsubscribe(interaction: discord.Interaction, anime_name: str):
    channel_id = str(interaction.channel.id)
    if await db.remove_subscription_by_title(channel_id, anime_name):
        await interaction.response.send_message(
            f"Successfully unsubscribed from {anime_name}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Could not find a subscription for {anime_name}.",
            ephemeral=True
        )

@bot.tree.command(name='unsubscribe_all', description='Stop all anime notifications in this channel.')
async def unsubscribe_all(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)
    count = await db.remove_all_subscriptions(channel_id)
    await interaction.response.send_message(
        f"Successfully unsubscribed from {count} anime.",
        ephemeral=True
    )

@bot.tree.command(name='about', description='Shows information about the bot and how to use it.')
async def about(interaction: discord.Interaction):
    embed = discord.Embed(
        title="About This Bot",
        description="This bot notifies you when new episodes of your favorite anime are released. Here's how it works:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="How Notifications Work",
        value="The bot checks for new episodes every 10 minutes. When a new episode is found for an anime you are subscribed to, "
              "it will send a notification in the channel where you used the /subscribe command.",
        inline=False
    )

    embed.add_field(
        name="Commands",
        value="""
• `/subscribe [anime_name]` - Subscribes to an anime for notifications in the current channel.
• `/unsubscribe [anime_name]` - Unsubscribes from a specific anime in the current channel.
• `/unsubscribe_all` - Unsubscribes from all anime in the current channel.
• `/list` - Shows all the anime you are subscribed to in the current channel.
• `/about` - Shows this message.
        """,
        inline=False
    )

    embed.add_field(
        name="Permissions",
        value="By default, only users with the Manage Channels permission can use the /subscribe, /unsubscribe, and "
              "/unsubscribe_all commands. However, a server administrator can customize these permissions:",
        inline=False
    )

    embed.add_field(
        name="How to Change Permissions",
        value="""
1. Go to your Discord server settings.
2. Navigate to Integrations.
3. Find and click on Aira (your bot's name).
4. Under Commands, you will see a list of all available slash commands.
5. Click on a command (e.g., /subscribe) to adjust its permissions.
6. You can then add or remove roles/users and specify whether they can use the command.
        """,
        inline=False
    )

    embed.add_field(
        name="Data Source",
        value="The bot uses the AniList API to get information about anime.",
        inline=False
    )

    embed.set_footer(text="Hosted with ❤️ by heo-systems.net")
    
    await interaction.response.send_message(embed=embed)

@tasks.loop(minutes=10)
async def check_new_episodes():
    all_subscriptions = await db.get_all_subscriptions()
    
    for channel_id, subs in all_subscriptions.items():
        for sub in subs:
            anime_data = anilist.get_anime_details(sub['id'])
            if not anime_data:
                continue

            current_episodes = sub.get('episodes', 0)
            latest_episodes = 0

            if anime_data.get('episodes') is not None:
                latest_episodes = anime_data.get('episodes')
            elif anime_data.get('nextAiringEpisode') is not None:
                latest_episodes = anime_data.get('nextAiringEpisode', {}).get('episode', 1) - 1

            if latest_episodes > current_episodes:
                await db.update_episodes(sub['id'], latest_episodes)
                
                channel = bot.get_channel(int(channel_id))
                if channel:
                    embed = anilist.get_episode_update_embed(anime_data, latest_episodes)
                    await channel.send(embed=discord.Embed.from_dict(embed))

bot.run(TOKEN) 