from app.models.community import CommunityPost, SocialProfile, SocialLink
from app.models.user import User
from datetime import datetime, timedelta
from typing import List

class CommunityBrain:
    @staticmethod
    async def rank_feed(user_email: str) -> List[CommunityPost]:
        """
        Neural Feed Ranking: Prioritizes elite engagement, relevant links, and interests.
        """
        all_posts = await CommunityPost.find_all().sort("-timestamp").limit(100).to_list()
        profile = await SocialProfile.find_one(SocialProfile.userEmail == user_email)
        
        following = profile.following if profile else []
        interests = profile.interests if profile else {}

        def score_post(post):
            score = 0
            # 1. Following Bonus
            if post.userEmail in following: score += 100
            
            # 2. Interest Alignment Bonus
            if hasattr(post, 'tags') and post.tags:
                for tag in post.tags:
                    score += interests.get(tag, 0) * 10
            
            # 3. Engagement Score
            score += len(post.likes) * 10
            score += len(post.comments) * 5
            score += getattr(post, 'views', 0) * 0.1
            
            return score

        all_posts.sort(key=score_post, reverse=True)
        return all_posts

    @staticmethod
    async def track_interest(user_email: str, tags: List[str], weight: float = 1.0):
        """
        Neural Interest Tracker: Updates member interest matrix based on actions.
        """
        profile = await SocialProfile.find_one(SocialProfile.userEmail == user_email)
        if not profile: return
        
        if profile.interests is None: profile.interests = {}
        for tag in tags:
            current = profile.interests.get(tag, 0)
            profile.interests[tag] = round(current + weight, 2)
        
        await profile.save()

    @staticmethod
    async def suggest_links(user_email: str) -> List[dict]:
        """
        Neural Recommendations: Suggests members based on shared gym activity.
        """
        # Suggest users who are not already linked
        profile = await SocialProfile.find_one(SocialProfile.userEmail == user_email)
        following = profile.following if profile else []
        
        all_users = await User.find(User.email != user_email).limit(10).to_list()
        suggestions = []
        for u in all_users:
            if u.email not in following:
                suggestions.append({
                    "name": f"{u.firstName} {u.lastName}",
                    "email": u.email,
                    "avatar": u.profilePicture,
                    "reason": "Elite Member"
                })
        return suggestions

    @staticmethod
    async def get_analytics(user_email: str) -> dict:
        """
        Neural Dashboard: Calculates reach and engagement stats.
        """
        profile = await SocialProfile.find_one(SocialProfile.userEmail == user_email)
        if not profile: return {"posts": 0, "followers": 0, "following": 0, "views": 0}

        return {
            "posts": profile.postsCount,
            "followers": len(profile.followers),
            "following": len(profile.following),
            "views": profile.views30Days
        }

    @staticmethod
    def moderate_content(content: str) -> bool:
        """
        Autonomous Moderation: Ensures content meets Elite Gym standards.
        """
        banned_words = ["toxic", "hate", "spam"] # Simplified for now
        for word in banned_words:
            if word in content.lower(): return False
        return True
