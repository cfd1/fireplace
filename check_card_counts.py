#!/usr/bin/env python

import os
import xml.etree.ElementTree as ET
import datetime
import collections
import argparse

def analyze_carddefs(backup_file=None):
    """
    Analyze and compare the CardDefs.xml file with a backup version.
    
    Args:
        backup_file: Optional path to a specific backup file to compare against.
                     If not provided, the most recent backup will be used.
    """
    print("Analyzing updated CardDefs.xml file...")
    
    # Path to the card defs file
    carddefs_path = os.path.join("fireplace", "cards", "CardDefs.xml")
    
    if not os.path.exists(carddefs_path):
        print(f"Error: {carddefs_path} not found.")
        return
    
    # Path to the backup file
    if backup_file:
        backup_path = backup_file
        if not os.path.exists(backup_path):
            print(f"Error: Specified backup file {backup_path} not found.")
            return
    else:
        backup_files = [f for f in os.listdir(os.path.join("fireplace", "cards")) 
                      if f.startswith("CardDefs.xml.backup")]
        
        if not backup_files:
            print("No backup file found. Cannot compare changes.")
            return
        
        # Use the most recent backup
        backup_files.sort(reverse=True)
        backup_path = os.path.join("fireplace", "cards", backup_files[0])
    
    print(f"Using backup file: {backup_path}")
    
    # Parse XML files
    try:
        print(f"Parsing {carddefs_path}...")
        current_tree = ET.parse(carddefs_path)
        current_root = current_tree.getroot()
        
        print(f"Parsing {backup_path}...")
        backup_tree = ET.parse(backup_path)
        backup_root = backup_tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return
    
    # Count entities
    current_entities = current_root.findall(".//Entity")
    backup_entities = backup_root.findall(".//Entity")
    
    # Get entity IDs for comparison
    current_ids = {entity.get("ID") for entity in current_entities if entity.get("ID")}
    backup_ids = {entity.get("ID") for entity in backup_entities if entity.get("ID")}
    
    # Calculate differences
    new_cards = current_ids - backup_ids
    removed_cards = backup_ids - current_ids
    
    print("\n" + "="*50)
    print("CARD COUNT COMPARISON")
    print("="*50)
    print(f"Current version:  {len(current_entities):,} cards")
    print(f"Previous version: {len(backup_entities):,} cards")
    
    diff = len(current_entities) - len(backup_entities)
    if diff > 0:
        print(f"Difference:       +{diff:,} cards")
    else:
        print(f"Difference:       {diff:,} cards")
    
    print(f"\nNew cards added:   {len(new_cards):,}")
    print(f"Cards removed:     {len(removed_cards):,}")
    
    # Print some sample new cards if any
    if new_cards and len(new_cards) <= 20:
        print("\nAll new cards:")
        for card_id in sorted(new_cards):
            print(f"- {card_id}")
    elif new_cards:
        print("\nSample of new cards (20 of {len(new_cards):,}):")
        sample = sorted(list(new_cards))[:20]
        for card_id in sample:
            print(f"- {card_id}")
    
    # Print some sample removed cards if any
    if removed_cards and len(removed_cards) <= 20:
        print("\nAll removed cards:")
        for card_id in sorted(removed_cards):
            print(f"- {card_id}")
    elif removed_cards:
        print("\nSample of removed cards (20 of {len(removed_cards):,}):")
        sample = sorted(list(removed_cards))[:20]
        for card_id in sample:
            print(f"- {card_id}")
    
    # Analyze card types in current file
    card_types = collections.Counter()
    card_sets = collections.Counter()
    
    print("\n" + "="*50)
    print("CARD TYPE AND SET ANALYSIS")
    print("="*50)
    
    for entity in current_entities:
        # Find the CardType tag (enumID="202")
        card_type_tag = entity.find(".//Tag[@enumID='202']")
        if card_type_tag is not None:
            card_type = int(card_type_tag.get("value", "0"))
            card_types[card_type] += 1
        
        # Find the CardSet tag (enumID="183")
        card_set_tag = entity.find(".//Tag[@enumID='183']")
        if card_set_tag is not None:
            card_set = int(card_set_tag.get("value", "0"))
            card_sets[card_set] += 1
    
    # Define card type names
    card_type_names = {
        1: "GAME",
        2: "PLAYER",
        3: "HERO",
        4: "MINION",
        5: "SPELL",
        6: "ENCHANTMENT",
        7: "WEAPON",
        8: "ITEM",
        10: "HERO_POWER",
        11: "BLANK",
        12: "GAME_MODE_BUTTON",
        22: "HERO_POWER_CARD_OVERRIDE",
        23: "HERO_POWER_DISABLED",
        39: "LOCATION",
        40: "BATTLEGROUND_HERO_BUDDY",
        43: "BATTLEGROUND_SPELL",
    }
    
    # Print card type stats
    print("\nCard Type Distribution:")
    print("-" * 40)
    print(f"{'Card Type':<25} {'Count':>8} {'Percentage':>12}")
    print("-" * 40)
    
    total_cards = len(current_entities)
    for card_type, count in card_types.most_common():
        type_name = card_type_names.get(card_type, f"UNKNOWN_{card_type}")
        percentage = count / total_cards * 100 if total_cards > 0 else 0
        print(f"{type_name} ({card_type}):{'':<10} {count:>7,} {percentage:>11.1f}%")
    
    # Define some common card sets
    card_set_names = {
        3: "EXPERT1",
        12: "NAXX",
        13: "GVG",
        14: "BRM",
        15: "TGT",
        17: "HERO_SKINS",
        18: "TB",
        20: "LOE",
        21: "OG",
        23: "KARA",
        25: "GANGS",
        27: "UNGORO",
        1001: "ICECROWN",
        1004: "LOOTAPALOOZA",
        1125: "GILNEAS",
        1127: "BOOMSDAY",
        1129: "TROLL",
        1130: "DALARAN",
        1158: "ULDUM",
        1347: "DRAGONS",
        1403: "YEAR_OF_THE_DRAGON",
        1414: "BLACK_TEMPLE",
        1439: "WILD_EVENT",
        1443: "SCHOLOMANCE",
        1453: "BATTLEGROUNDS",
        1466: "DARKMOON_FAIRE",
        1525: "THE_BARRENS",
        1578: "STORMWIND",
        1586: "LETTUCE",
        1626: "ALTERAC_VALLEY",
        1637: "CORE",
        1658: "THE_SUNKEN_CITY",
        1776: "RETURN_OF_THE_LICH_KING",
        1809: "BATTLE_OF_THE_BANDS",
        1858: "TITANS",
        1892: "WILD_WEST",
        1898: "WONDERS",
    }
    
    # Print top card sets
    print("\nTop Card Sets:")
    print("-" * 40)
    print(f"{'Card Set':<25} {'Count':>8} {'Percentage':>12}")
    print("-" * 40)
    
    for card_set, count in card_sets.most_common(15):
        set_name = card_set_names.get(card_set, f"UNKNOWN_{card_set}")
        percentage = count / total_cards * 100 if total_cards > 0 else 0
        print(f"{set_name} ({card_set}):{'':<10} {count:>7,} {percentage:>11.1f}%")
    
    # Print file sizes
    current_size = os.path.getsize(carddefs_path) / (1024 * 1024)  # Size in MB
    backup_size = os.path.getsize(backup_path) / (1024 * 1024)     # Size in MB
    
    print("\n" + "="*50)
    print("FILE SIZE COMPARISON")
    print("="*50)
    print(f"Current version:  {current_size:.2f} MB")
    print(f"Previous version: {backup_size:.2f} MB")
    
    size_diff = current_size - backup_size
    if size_diff > 0:
        print(f"Difference:       +{size_diff:.2f} MB ({(size_diff/backup_size)*100:.1f}% increase)")
    else:
        print(f"Difference:       {size_diff:.2f} MB ({(size_diff/backup_size)*100:.1f}% decrease)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze and compare the CardDefs.xml file with a backup version",
        epilog="""
Examples:
  python check_card_counts.py                    # Compare with the most recent backup
  python check_card_counts.py --backup-file fireplace/cards/CardDefs.xml.backup.20230101120000  # Compare with a specific backup
        """
    )
    
    parser.add_argument(
        "--backup-file", 
        help="Path to a specific backup file to compare against. If not provided, the most recent backup will be used."
    )
    
    args = parser.parse_args()
    
    analyze_carddefs(backup_file=args.backup_file) 