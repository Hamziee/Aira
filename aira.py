import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from database import Database
from anilist_api import AniListAPI
from typing import Dict
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DONATOR_SKU_ID = os.getenv('DONATOR_SKU_ID')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents
)
db = Database()
anilist = AniListAPI()

donator_cache: Dict[int, tuple[bool, float]] = {}
CACHE_DURATION = 300

async def is_donator_guild(guild_id: int) -> bool:
    current_time = time.time()
    
    if guild_id in donator_cache:
        status, timestamp = donator_cache[guild_id]
        if current_time - timestamp < CACHE_DURATION:
            return status
    
    try:
        if not DONATOR_SKU_ID:
            return False

        route = discord.http.Route('GET', f'/applications/{bot.application_id}/entitlements')
        try:
            all_entitlements = await bot.http.request(route)
            
            guild_entitlements = [
                e for e in all_entitlements 
                if str(e.get('guild_id')) == str(guild_id) and 
                str(e.get('sku_id')) == str(DONATOR_SKU_ID) and 
                not e.get('deleted', False)
            ]
            
            is_donator = len(guild_entitlements) > 0
            donator_cache[guild_id] = (is_donator, current_time)
            return is_donator
            
        except discord.NotFound:
            donator_cache[guild_id] = (False, current_time)
            return False
            
    except Exception as e:
        print(f"Error checking donator status: {str(e)}")
        return False

async def set_donator_footer(embed: discord.Embed, guild_id: int):
    is_donator = await is_donator_guild(guild_id)
    if is_donator:
        embed.set_footer(text="✨ Donator Server")

class AnimeListPaginator(discord.ui.View):
    def __init__(self, subscriptions: list, anime_data_list: list, per_page: int = 5):
        super().__init__(timeout=30)
        self.subscriptions = subscriptions
        self.anime_data_list = anime_data_list
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = max(1, (len(subscriptions) + per_page - 1) // per_page)
        
        self.update_buttons()

    def update_buttons(self):
        self.first_page_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.last_page_button.disabled = self.current_page >= self.total_pages - 1

    def get_current_page_embed(self, guild_id: int) -> discord.Embed:
        embed = discord.Embed(
            title="📺 Channel Subscriptions",
            description=f"Page {self.current_page + 1}/{self.total_pages}",
            color=discord.Color.blue()
        )

        start_idx = self.current_page * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.subscriptions))

        for i in range(start_idx, end_idx):
            sub = self.subscriptions[i]
            anime_data = self.anime_data_list[i]
            
            if anime_data:
                english_title = anime_data['title'].get('english')
                romaji_title = anime_data['title'].get('romaji', '')
                
                if english_title:
                    base_title = english_title
                    if "Season" not in english_title and "Part" not in english_title:
                        if "Season" in romaji_title or "Part" in romaji_title or "2nd" in romaji_title:
                            base_title = f"{english_title} Season {romaji_title.split('Season')[-1].strip()}"
                    display_title = f"{base_title} ({romaji_title})"
                else:
                    display_title = romaji_title

                value_parts = []
                
                if anime_data.get('episodes'):
                    value_parts.append(f"Episodes: {sub['episodes']}/{anime_data['episodes']}")
                
                if anime_data.get('nextAiringEpisode'):
                    value_parts.append(anilist.format_airing_info(anime_data['nextAiringEpisode']))
                elif anime_data.get('status') == 'FINISHED':
                    value_parts.append("Series completed")
                
                embed.add_field(
                    name=display_title,
                    value="\n".join(value_parts) or "No airing information available",
                    inline=False
                )

        return embed

    @discord.ui.button(label="≪", style=discord.ButtonStyle.grey)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        embed = self.get_current_page_embed(interaction.guild_id)
        await set_donator_footer(embed, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        embed = self.get_current_page_embed(interaction.guild_id)
        await set_donator_footer(embed, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        embed = self.get_current_page_embed(interaction.guild_id)
        await set_donator_footer(embed, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="≫", style=discord.ButtonStyle.grey)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages - 1
        self.update_buttons()
        embed = self.get_current_page_embed(interaction.guild_id)
        await set_donator_footer(embed, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot Application ID: {bot.application_id}')
    print(f'Invite URL: https://discord.com/api/oauth2/authorize?client_id={bot.application_id}&permissions=277025729600&scope=bot%20applications.commands%20applications.entitlements')
    await db.init_db()
    await bot.tree.sync()
    if not check_new_episodes.is_running():
        check_new_episodes.start()

@bot.tree.command(name='subscribe', description='Subscribe this channel to notifications for new episodes of an anime.')
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
            await interaction.followup.send(f"This channel is already subscribed to {anime['title']['romaji']}.")
            return

        await db.add_subscription(
            channel_id=channel_id,
            anime_id=anime['id'],
            title=anime['title']['romaji'],
            episodes=anime.get('episodes', 0)
        )

        embed = discord.Embed(
            title="✅ Channel Subscription Added!",
            description=f"This channel will now receive notifications for new episodes of {anime['title']['romaji']}",
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

        await set_donator_footer(embed, interaction.guild_id)
        await interaction.followup.send(embed=embed)
    else:
        select = discord.ui.Select(
            placeholder="Select an anime",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=self._format_select_label(anime),
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
                        content=f"This channel is already subscribed to {selected_anime['title']['romaji']}.",
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
                    title="✅ Channel Subscription Added!",
                    description=f"This channel will now receive notifications for new episodes of {selected_anime['title']['romaji']}",
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

                await set_donator_footer(embed, interaction.guild_id)
                await select_interaction.response.edit_message(embed=embed, view=None)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.followup.send("Multiple anime found. Please select one:", view=view)

def _format_select_label(self, anime: dict) -> str:
    english_title = anime['title'].get('english')
    romaji_title = anime['title'].get('romaji', '')
    
    if english_title:
        base_title = english_title
        if "Season" not in english_title and "Part" not in english_title:
            if "Season" in romaji_title or "Part" in romaji_title or "2nd" in romaji_title:
                base_title = f"{english_title} Season {romaji_title.split('Season')[-1].strip()}"
        display_title = f"{base_title} ({romaji_title})"
    else:
        display_title = romaji_title
    
    return display_title[:100]

@bot.tree.command(name='list', description='Lists all anime subscriptions in this channel.')
async def list_anime(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)
    subscriptions = await db.get_channel_subscriptions(channel_id)
    
    if subscriptions:
        anime_data_list = [anilist.get_anime_details(sub['id']) for sub in subscriptions]
        
        paginator = AnimeListPaginator(subscriptions, anime_data_list)
        
        embed = paginator.get_current_page_embed(interaction.guild_id)
        await set_donator_footer(embed, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=paginator)
    else:
        await interaction.response.send_message(
            "This channel has no anime subscriptions.",
            ephemeral=True
        )

@bot.tree.command(name='unsubscribe', description='Stop notifications for an anime in this channel.')
async def unsubscribe(interaction: discord.Interaction, anime_name: str):
    channel_id = str(interaction.channel.id)
    if await db.remove_subscription_by_title(channel_id, anime_name):
        await interaction.response.send_message(
            f"Successfully unsubscribed this channel from {anime_name}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Could not find a subscription for {anime_name} in this channel.",
            ephemeral=True
        )

@bot.tree.command(name='unsubscribe_all', description='Stop all anime notifications in this channel.')
async def unsubscribe_all(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)
    count = await db.remove_all_subscriptions(channel_id)
    await interaction.response.send_message(
        f"Successfully removed all {count} anime subscriptions from this channel.",
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
        value="The bot checks for new episodes every minute for premium servers and every 10 minutes for free servers. "
              "When a new episode is found for an anime that a channel is subscribed to, "
              "it will send a notification in that channel.",
        inline=False
    )

    embed.add_field(
        name="Commands",
        value="""
• `/subscribe [anime_name]` - Subscribe this channel to notifications for an anime
• `/unsubscribe [anime_name]` - Unsubscribe this channel from notifications for a specific anime
• `/unsubscribe_all` - Remove all anime subscriptions from this channel
• `/list` - Show all anime subscriptions in this channel
• `/donator_status` - Check this server's donator status
• `/about` - Show this message
        """,
        inline=False
    )

    embed.add_field(
        name="Permissions",
        value="By default, only users with the Manage Channels permission can use the /subscribe, /unsubscribe, and "
              "/unsubscribe_all commands in a channel. However, a server administrator can customize these permissions:",
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

@tasks.loop(minutes=1)
async def check_new_episodes():
    try:
        all_subscriptions = await db.get_all_subscriptions()
        
        for channel_id, subscriptions in all_subscriptions.items():
            try:
                channel = bot.get_channel(int(channel_id))
                if not channel:
                    continue

                is_donator = await is_donator_guild(channel.guild.id)
                
                if not is_donator and check_new_episodes.current_loop % 10 != 0:
                    continue
                    
                for sub in subscriptions:
                    try:
                        anime_data = anilist.get_anime_details(sub['id'])
                        if not anime_data:
                            print(f"No anime data found for ID {sub['id']}")
                            continue

                        next_episode = anime_data.get('nextAiringEpisode', {})
                        if not next_episode:
                            continue

                        current_episode = next_episode.get('episode', 0)
                        if current_episode and current_episode > sub['episodes']:
                            embed = discord.Embed(
                                title="🎬 New Episode Available!",
                                description=f"Episode {current_episode} of {anime_data['title']['romaji']} is now available!",
                                color=discord.Color.green()
                            )

                            if anime_data['title'].get('english'):
                                embed.add_field(
                                    name="English Title",
                                    value=anime_data['title']['english'],
                                    inline=True
                                )

                            if anime_data.get('nextAiringEpisode'):
                                embed.add_field(
                                    name="Next Episode",
                                    value=anilist.format_airing_info(anime_data['nextAiringEpisode']),
                                    inline=False
                                )

                            if anime_data.get('coverImage', {}).get('medium'):
                                embed.set_thumbnail(url=anime_data['coverImage']['medium'])

                            await set_donator_footer(embed, channel.guild.id)
                            await channel.send(embed=embed)
                            await db.update_episodes(sub['id'], current_episode)

                    except Exception as e:
                        print(f"Error processing anime {sub['id']}: {str(e)}")
                        continue

            except Exception as e:
                print(f"Error processing channel {channel_id}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error in check_new_episodes: {str(e)}")

@bot.tree.command(name='donator_status', description='Check the donator status of this server')
async def donator_status(interaction: discord.Interaction):
    is_donator = await is_donator_guild(interaction.guild_id)
    
    embed = discord.Embed(
        title="Donator Status",
        description="Here's your server's donator status:",
        color=discord.Color.blue() if is_donator else discord.Color.light_grey()
    )
    
    if is_donator:
        embed.add_field(
            name="✨ Donator Benefits Active",
            value="Thank you for supporting Aira!\n• Real-time notifications every minute\n• Donator server badge on all bot messages\n• More coming soon!",
            inline=False
        )
    else:
        embed.add_field(
            name="Free Plan",
            value="This server is using the free plan.\n• Notifications every 10 minutes\n\nBecome a donator for:\n• Real-time notifications every minute\n• Donator server badge on all bot messages",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN) 