#!/usr/bin/env python

import os
import requests
import shutil
import xml.etree.ElementTree as ET
import tempfile
from datetime import datetime

# Define supported card types
SUPPORTED_CARD_TYPES = [1, 3, 4, 5, 6, 7, 10]  # HERO, MINION, SPELL, ENCHANTMENT, WEAPON, HERO_POWER
CARD_TYPE_ENUM_ID = "202"  # The enumID for CardType in the XML

def update_carddefs(selective_update=False, filter_card_types=True, update_existing_only=False):
    """
    Update the CardDefs.xml file from the latest HearthstoneJSON API.
    
    Args:
        selective_update: If True, update only the entries that exist in both files,
                          preserving any custom entries in the original.
        filter_card_types: If True, filters out card types not supported by the current codebase.
        update_existing_only: If True, only update cards that already exist in the current file
                              without adding any new cards from the API.
    """
    print("Updating CardDefs.xml from the latest HearthstoneJSON API...")
    
    # URL to fetch from
    url = "https://api.hearthstonejson.com/v1/latest/CardDefs.xml"
    
    # Target path
    target_path = os.path.join("fireplace", "cards", "CardDefs.xml")
    
    # Backup the existing file
    if os.path.exists(target_path):
        backup_name = f"CardDefs.xml.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_path = os.path.join("fireplace", "cards", backup_name)
        print(f"Creating backup at {backup_path}")
        shutil.copy2(target_path, backup_path)
    
    # Download new file to a temporary location
    temp_path = os.path.join("fireplace", "cards", "CardDefs.xml.temp")
    print(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    if (selective_update or filter_card_types or update_existing_only) and os.path.exists(target_path):
        print("Performing selective update with type filtering...")
        try:
            # Parse both XML files
            current_tree = ET.parse(target_path)
            current_root = current_tree.getroot()
            
            new_tree = ET.parse(temp_path)
            new_root = new_tree.getroot()
            
            # Create a dictionary of entities by ID from the current file
            current_entities = {}
            for entity in current_root.findall(".//Entity"):
                entity_id = entity.get("ID")
                if entity_id:
                    current_entities[entity_id] = entity
            
            # Create a dictionary of new entities, filtering by card type if needed
            new_entities = {}
            filtered_count = 0
            skipped_count = 0
            
            for entity in new_root.findall(".//Entity"):
                entity_id = entity.get("ID")
                if not entity_id:
                    continue
                
                # Skip new cards if update_existing_only is True
                if update_existing_only and entity_id not in current_entities:
                    skipped_count += 1
                    continue
                
                # Check if this entity should be filtered based on card type
                if filter_card_types:
                    # Look for a Tag with enumID="202" (CardType)
                    card_type_tag = entity.find(f".//Tag[@enumID='{CARD_TYPE_ENUM_ID}']")
                    if card_type_tag is not None:
                        card_type = int(card_type_tag.get("value", "0"))
                        if card_type not in SUPPORTED_CARD_TYPES:
                            filtered_count += 1
                            continue
                
                new_entities[entity_id] = entity
            
            # Create a new XML tree with the same root
            merged_root = ET.Element(current_root.tag, attrib=current_root.attrib)
            
            # Process all CardDefs children - they should be Entity elements
            update_count = 0
            new_count = 0
            preserved_count = 0
            
            # First, copy all the non-Entity elements from the current root
            for child in current_root:
                if child.tag != "Entity":
                    merged_root.append(ET.fromstring(ET.tostring(child, encoding='unicode')))
            
            # Process all Entity elements
            processed_ids = set()
            
            # Add entities from current file that aren't in the new file (preserved)
            if selective_update or update_existing_only:
                for entity_id, entity in current_entities.items():
                    if entity_id not in new_entities:
                        # This is a custom entity not in the new file - keep it
                        merged_root.append(ET.fromstring(ET.tostring(entity, encoding='unicode')))
                        preserved_count += 1
                        processed_ids.add(entity_id)
            
            # Add/update entities from new file
            for entity_id, entity in new_entities.items():
                if entity_id not in processed_ids:
                    if (selective_update or update_existing_only) and entity_id in current_entities:
                        # This is an update to an existing entity
                        update_count += 1
                    else:
                        # This is a new entity
                        new_count += 1
                    
                    # Add the entity to the merged root
                    merged_root.append(ET.fromstring(ET.tostring(entity, encoding='unicode')))
                    processed_ids.add(entity_id)
            
            # Create a new tree with the merged root
            merged_tree = ET.ElementTree(merged_root)
            
            # Write the merged tree to the target path
            with open(target_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                merged_tree.write(f, encoding="utf-8")
            
            print(f"Update complete.")
            if selective_update or update_existing_only:
                print(f"- {update_count} entities updated")
                print(f"- {new_count} new entities added")
                print(f"- {preserved_count} original entities preserved")
            if update_existing_only:
                print(f"- {skipped_count} new entities skipped (update_existing_only=True)")
            if filter_card_types:
                print(f"- {filtered_count} entities filtered out due to unsupported card types")
            
        except Exception as e:
            print(f"Error during selective update: {e}")
            print("Falling back to full replacement...")
            shutil.copy2(temp_path, target_path)
    else:
        # Simple full replacement
        shutil.copy2(temp_path, target_path)
        print(f"Successfully updated {target_path} (full replacement)")
    
    # Clean up temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    print("To incorporate changes, restart your application or reinitialize the card database.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update CardDefs.xml from the HearthstoneJSON API",
        epilog="""
Examples:
  python update_carddefs.py                    # Update all cards (full replacement)
  python update_carddefs.py --selective        # Update cards but preserve custom entries
  python update_carddefs.py --update-existing-only  # Update only existing cards, don't add new ones
  python update_carddefs.py --no-filter        # Update without filtering out unsupported card types
        """
    )
    
    parser.add_argument(
        "--selective", 
        action="store_true", 
        help="Perform a selective update that preserves any custom entries in the current file that don't exist in the API data"
    )
    
    parser.add_argument(
        "--no-filter", 
        action="store_true", 
        help="Do not filter out unsupported card types (such as LOCATION) that might cause errors in the codebase"
    )
    
    parser.add_argument(
        "--update-existing-only", 
        action="store_true", 
        help="Only update cards that already exist in the current file, don't add any new cards from the API"
    )
    
    args = parser.parse_args()
    
    update_carddefs(
        selective_update=args.selective, 
        filter_card_types=not args.no_filter,
        update_existing_only=args.update_existing_only
    ) 