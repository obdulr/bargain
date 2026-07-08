"""Niche category service for targeted deal scanning.

Each niche maps to Amazon category IDs (for Keepa) and eBay search
categories. This lets users subscribe to specific niches and only
receive deals in categories they care about.
"""
from dataclasses import dataclass
from typing import Optional

# Amazon category IDs (Keepa category IDs)
# These are the root category IDs used by Keepa's deal finder
AMAZON_CATEGORY_IDS = {
    "electronics": 172282,          # Electronics
    "tools_home_improvement": 228013,  # Tools & Home Improvement
    "outdoor_garden": 1055398,       # Patio, Lawn & Garden
    "toys_games": 165793011,         # Toys & Games
    "kitchen_dining": 284507,        # Kitchen & Dining
    "sports_fitness": 3375251,       # Sports & Outdoors
    "beauty_personal_care": 3760911, # Beauty & Personal Care
    "baby_nursery": 165796011,       # Baby
    "pet_supplies": 2619533011,      # Pet Supplies
    "video_games": 468642,           # Video Games
}

# eBay category IDs (for Browse API category filtering)
EBAY_CATEGORY_IDS = {
    "electronics": "293",            # Consumer Electronics
    "tools_home_improvement": "318",  # Tools
    "outdoor_garden": "115623",      # Patio & Garden
    "toys_games": "220",             # Toys & Hobbies
    "kitchen_dining": "20625",       # Kitchen, Dining & Bar
    "sports_fitness": "888",         # Sporting Goods
    "beauty_personal_care": "26395", # Health & Beauty
    "baby_nursery": "2984",          # Baby
    "pet_supplies": "1281",          # Pet Supplies
    "video_games": "1249",           # Video Games & Consoles
}


@dataclass
class Niche:
    key: str
    display_name: str
    amazon_category_id: int
    ebay_category_id: str
    emoji: str
    description: str
    typical_margin: str  # e.g. "15-35%"


NICHES = {
    "electronics": Niche(
        key="electronics",
        display_name="Electronics",
        amazon_category_id=AMAZON_CATEGORY_IDS["electronics"],
        ebay_category_id=EBAY_CATEGORY_IDS["electronics"],
        emoji="📱",
        description="Phones, tablets, headphones, smart home, accessories",
        typical_margin="15-30%",
    ),
    "tools_home_improvement": Niche(
        key="tools_home_improvement",
        display_name="Tools & Home Improvement",
        amazon_category_id=AMAZON_CATEGORY_IDS["tools_home_improvement"],
        ebay_category_id=EBAY_CATEGORY_IDS["tools_home_improvement"],
        emoji="🔧",
        description="Power tools, hand tools, hardware, plumbing, electrical",
        typical_margin="20-40%",
    ),
    "outdoor_garden": Niche(
        key="outdoor_garden",
        display_name="Outdoor & Garden",
        amazon_category_id=AMAZON_CATEGORY_IDS["outdoor_garden"],
        ebay_category_id=EBAY_CATEGORY_IDS["outdoor_garden"],
        emoji="🌿",
        description="Patio furniture, grills, garden tools, outdoor decor",
        typical_margin="25-45%",
    ),
    "toys_games": Niche(
        key="toys_games",
        display_name="Toys & Games",
        amazon_category_id=AMAZON_CATEGORY_IDS["toys_games"],
        ebay_category_id=EBAY_CATEGORY_IDS["toys_games"],
        emoji="🎲",
        description="Board games, action figures, building sets, collectibles",
        typical_margin="20-50%",
    ),
    "kitchen_dining": Niche(
        key="kitchen_dining",
        display_name="Kitchen & Dining",
        amazon_category_id=AMAZON_CATEGORY_IDS["kitchen_dining"],
        ebay_category_id=EBAY_CATEGORY_IDS["kitchen_dining"],
        emoji="🍳",
        description="Small appliances, cookware, cutlery, kitchen gadgets",
        typical_margin="15-35%",
    ),
    "sports_fitness": Niche(
        key="sports_fitness",
        display_name="Sports & Fitness",
        amazon_category_id=AMAZON_CATEGORY_IDS["sports_fitness"],
        ebay_category_id=EBAY_CATEGORY_IDS["sports_fitness"],
        emoji="💪",
        description="Exercise equipment, weights, sports gear, outdoor sports",
        typical_margin="20-40%",
    ),
    "beauty_personal_care": Niche(
        key="beauty_personal_care",
        display_name="Beauty & Personal Care",
        amazon_category_id=AMAZON_CATEGORY_IDS["beauty_personal_care"],
        ebay_category_id=EBAY_CATEGORY_IDS["beauty_personal_care"],
        emoji="💄",
        description="Skincare, hair care, cosmetics, grooming tools",
        typical_margin="25-50%",
    ),
    "baby_nursery": Niche(
        key="baby_nursery",
        display_name="Baby & Nursery",
        amazon_category_id=AMAZON_CATEGORY_IDS["baby_nursery"],
        ebay_category_id=EBAY_CATEGORY_IDS["baby_nursery"],
        emoji="👶",
        description="Strollers, car seats, monitors, baby toys, nursery decor",
        typical_margin="15-35%",
    ),
    "pet_supplies": Niche(
        key="pet_supplies",
        display_name="Pet Supplies",
        amazon_category_id=AMAZON_CATEGORY_IDS["pet_supplies"],
        ebay_category_id=EBAY_CATEGORY_IDS["pet_supplies"],
        emoji="🐾",
        description="Pet tech, beds, carriers, feeders, training gear",
        typical_margin="20-40%",
    ),
    "video_games": Niche(
        key="video_games",
        display_name="Video Games",
        amazon_category_id=AMAZON_CATEGORY_IDS["video_games"],
        ebay_category_id=EBAY_CATEGORY_IDS["video_games"],
        emoji="🎮",
        description="Consoles, games, controllers, accessories, collectibles",
        typical_margin="10-30%",
    ),
}


def get_niche(key: str) -> Optional[Niche]:
    return NICHES.get(key)


def get_all_niches() -> list[Niche]:
    return list(NICHES.values())


def get_niche_for_amazon_category(category_id: int) -> Optional[Niche]:
    """Find niche by Amazon category ID."""
    for niche in NICHES.values():
        if niche.amazon_category_id == category_id:
            return niche
    return None
