# Fireplace Implementation Plan: Patch 16.6.0 to 32.0.0

This document outlines the strategy for updating the Fireplace Hearthstone simulator from Patch 16.6.0 to the current Patch 32.0.0.

## Overview

The implementation will be approached in stages, focusing on core mechanics first, followed by expansions and card implementations.

## Key Expansions Released
1. **Murder at Castle Nathria** (24.0.0)
2. **March of the Lich King** (25.0.0)
3. **Festival of Legends** (26.0.0)
4. **Titans** (27.0.0)
5. **Showdown in the Badlands** (28.0.0)
6. **Whizbang's Workshop** (29.0.0)
7. **Azeroth United** (30.0.0)
8. **The Great Dark Beyond** (31.0.0)
9. **Into the Emerald Dream** (32.0.0)

## Implementation Priorities

### Phase 1: Core Mechanics
1. **Location Cards** (24.0.0)
   - Complete the implementation of Location class
   - Implement cooldown mechanism
   - Create comprehensive test suite

2. **Death Knight Class & Runes** (25.0.0)
   - Implement rune system for deck building
   - Create Death Knight hero class
   - Implement Blood, Frost, and Unholy rune types

3. **New Card Types**
   - Hero Equipment (27.0.0)
   - Tools (29.0.0)

4. **Dual-Type Minions** (25.0.0)
   - Update minion class to support multiple types
   - Implement type-checking functions

### Phase 2: Key Mechanics by Expansion

1. **Murder at Castle Nathria** (24.0.0)
   - Implement Infuse mechanic
   - Implement Suspicious cards

2. **March of the Lich King** (25.0.0)
   - Implement Manathirst mechanic
   - Implement Corpse mechanic
   - Implement Reborn mechanic updates

3. **Festival of Legends** (26.0.0)
   - Implement Finale mechanic
   - Implement Overheal mechanic

4. **Titans** (27.0.0)
   - Implement Empower mechanic
   - Implement Titan minion type

5. **Showdown in the Badlands** (28.0.0)
   - Implement Excavate mechanic
   - Implement Tradeable mechanic updates

6. **Whizbang's Workshop** (29.0.0)
   - Implement Creation mechanic
   - Implement Contraptions

7. **Azeroth United** (30.0.0)
   - Implement Twist format support
   - Implement Cycle mechanic

8. **The Great Dark Beyond** (31.0.0)
   - Implement Portal mechanic
   - Implement persistent minion effects

9. **Into the Emerald Dream** (32.0.0)
   - Implement Verdant Dreams mechanic
   - Implement Druid-specific mechanics

### Phase 3: Format & System Updates

1. **Core Set Rotation**
   - Update Core set cards for each year
   - Implement yearly rotation mechanism

2. **Format Updates**
   - Implement Twist format
   - Update Wild format rules

3. **Battlegrounds Updates** (if applicable)
   - Implement Battlegrounds mechanics (lower priority)

## Testing Strategy

For each implementation phase:

1. **Unit Tests**
   - Basic functionality tests
   - Edge case handling
   - Individual card behavior

2. **Integration Tests**
   - Mechanic interactions
   - Cross-expansion interactions
   - Game flow tests

3. **Regression Tests**
   - Ensure existing functionality works
   - Verify bug fixes from patches

## Documentation Updates

1. Update README.md with implementation progress
2. Document new mechanics in wiki
3. Add examples for complex mechanics

## Timeline

- **Phase 1:** Focus on Location cards implementation first
- **Phase 2:** Implement Death Knight and Runes
- **Phase 3:** Proceed with other mechanics in chronological order
- **Phase 4:** Expansion-specific cards implementation
- **Phase 5:** Final testing and documentation

## Tracking

Progress will be tracked by:
1. Implementation status in README.md
2. Test coverage metrics
3. GitHub issues for specific features/bugs 