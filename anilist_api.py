import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

ANILIST_URL = 'https://graphql.anilist.co'

class AniListAPI:
    @staticmethod
    def _make_request(query: str, variables: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to the AniList API."""
        response = requests.post(ANILIST_URL, json={'query': query, 'variables': variables})
        if response.status_code == 200:
            return response.json().get('data')
        return None

    def search_anime(self, search: str) -> List[Dict]:
        """Search for anime with enhanced information."""
        query = '''
        query ($search: String) {
            Page(page: 1, perPage: 5) {
                media(search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    coverImage {
                        medium
                    }
                    episodes
                    status
                    season
                    seasonYear
                    genres
                    averageScore
                    popularity
                    nextAiringEpisode {
                        episode
                        airingAt
                        timeUntilAiring
                    }
                    description
                }
            }
        }
        '''
        data = self._make_request(query, {'search': search})
        return data['Page']['media'] if data else []

    def get_anime_details(self, anime_id: int) -> Optional[Dict]:
        """Get detailed information about an anime."""
        query = '''
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                }
                coverImage {
                    medium
                    large
                }
                bannerImage
                episodes
                status
                season
                seasonYear
                genres
                averageScore
                popularity
                nextAiringEpisode {
                    episode
                    airingAt
                    timeUntilAiring
                }
                description
                studios(isMain: true) {
                    nodes {
                        name
                    }
                }
                externalLinks {
                    site
                    url
                }
                airingSchedule(notYetAired: true, page: 1, perPage: 1) {
                    nodes {
                        episode
                        airingAt
                    }
                }
            }
        }
        '''
        data = self._make_request(query, {'id': anime_id})
        return data['Media'] if data else None

    def format_time_until_airing(self, seconds: int) -> str:
        """Format time until airing in a human-readable way."""
        if seconds < 0:
            return "already aired"
            
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 and days == 0:  # Only show minutes if less than a day
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        return ", ".join(parts)

    def format_airing_info(self, next_episode: Dict) -> str:
        """Format next episode airing information."""
        if not next_episode:
            return "No airing information available"

        airing_time = datetime.fromtimestamp(next_episode['airingAt'])
        time_until = self.format_time_until_airing(next_episode['timeUntilAiring'])
        
        return (f"Episode {next_episode['episode']} airs "
                f"<t:{next_episode['airingAt']}:F> "
                f"({time_until} from now)")

    def get_episode_update_embed(self, anime_data: Dict, new_episode: int) -> Dict:
        """Create a rich embed for episode updates."""
        embed = {
            "title": f"New Episode of {anime_data['title']['romaji']}!",
            "description": f"Episode {new_episode} has been released!",
            "color": 0x2E51A2,  # AniList's blue color
            "fields": []
        }

        # Add English title if different
        if (anime_data['title']['english'] and 
            anime_data['title']['english'] != anime_data['title']['romaji']):
            embed["fields"].append({
                "name": "English Title",
                "value": anime_data['title']['english'],
                "inline": True
            })

        # Add episode progress
        if anime_data.get('episodes'):
            embed["fields"].append({
                "name": "Episode Progress",
                "value": f"Episode {new_episode}/{anime_data['episodes']}",
                "inline": True
            })

        # Add next episode info if available
        if anime_data.get('nextAiringEpisode'):
            embed["fields"].append({
                "name": "Next Episode",
                "value": self.format_airing_info(anime_data['nextAiringEpisode']),
                "inline": False
            })

        # Add cover image if available
        if anime_data.get('coverImage', {}).get('medium'):
            embed["thumbnail"] = {"url": anime_data['coverImage']['medium']}

        return embed 