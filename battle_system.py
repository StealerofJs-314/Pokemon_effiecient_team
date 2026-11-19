import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, overload


DATA_DIRECTORY = Path(__file__).resolve().parent
POKEDEX_PATH = DATA_DIRECTORY / "pokedex_with_learnsets.json"
MOVES_PATH = DATA_DIRECTORY / "moves_damage.json"
LEVEL = 100

TYPE_EFFECTIVENESS = {
    "Normal": {"Rock": 0.5, "Steel": 0.5, "Ghost": 0},
    "Fire": {
        "Fire": 0.5,
        "Water": 0.5,
        "Grass": 2,
        "Ice": 2,
        "Bug": 2,
        "Rock": 0.5,
        "Dragon": 0.5,
        "Steel": 2,
    },
    "Water": {
        "Fire": 2,
        "Water": 0.5,
        "Grass": 0.5,
        "Ground": 2,
        "Rock": 2,
        "Dragon": 0.5,
    },
    "Electric": {
        "Water": 2,
        "Electric": 0.5,
        "Grass": 0.5,
        "Ground": 0,
        "Flying": 2,
        "Dragon": 0.5,
    },
    "Grass": {
        "Fire": 0.5,
        "Water": 2,
        "Grass": 0.5,
        "Poison": 0.5,
        "Ground": 2,
        "Flying": 0.5,
        "Bug": 0.5,
        "Rock": 2,
        "Dragon": 0.5,
        "Steel": 0.5,
    },
    "Ice": {
        "Fire": 0.5,
        "Water": 0.5,
        "Grass": 2,
        "Ice": 0.5,
        "Ground": 2,
        "Flying": 2,
        "Dragon": 2,
        "Steel": 0.5,
    },
    "Fighting": {
        "Normal": 2,
        "Ice": 2,
        "Poison": 0.5,
        "Flying": 0.5,
        "Psychic": 0.5,
        "Bug": 0.5,
        "Rock": 2,
        "Ghost": 0,
        "Dark": 2,
        "Steel": 2,
        "Fairy": 0.5,
    },
    "Poison": {
        "Grass": 2,
        "Poison": 0.5,
        "Ground": 0.5,
        "Rock": 0.5,
        "Ghost": 0.5,
        "Steel": 0,
        "Fairy": 2,
    },
    "Ground": {
        "Fire": 2,
        "Grass": 0.5,
        "Electric": 2,
        "Poison": 2,
        "Flying": 0,
        "Bug": 0.5,
        "Rock": 2,
        "Steel": 2,
    },
    "Flying": {
        "Grass": 2,
        "Electric": 0.5,
        "Fighting": 2,
        "Bug": 2,
        "Rock": 0.5,
        "Steel": 0.5,
    },
    "Psychic": {
        "Fighting": 2,
        "Poison": 2,
        "Psychic": 0.5,
        "Dark": 0,
        "Steel": 0.5,
    },
    "Bug": {
        "Fire": 0.5,
        "Grass": 2,
        "Fighting": 0.5,
        "Poison": 0.5,
        "Flying": 0.5,
        "Psychic": 2,
        "Ghost": 0.5,
        "Dark": 2,
        "Steel": 0.5,
        "Fairy": 0.5,
    },
    "Rock": {
        "Fire": 2,
        "Ice": 2,
        "Fighting": 0.5,
        "Ground": 0.5,
        "Flying": 2,
        "Bug": 2,
        "Steel": 0.5,
    },
    "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
    "Dragon": {"Dragon": 2, "Steel": 0.5, "Fairy": 0},
    "Dark": {
        "Fighting": 0.5,
        "Psychic": 2,
        "Ghost": 2,
        "Dark": 0.5,
        "Fairy": 0.5,
    },
    "Steel": {
        "Fire": 0.5,
        "Water": 0.5,
        "Electric": 0.5,
        "Ice": 2,
        "Rock": 2,
        "Steel": 0.5,
        "Fairy": 2,
    },
    "Fairy": {
        "Fire": 0.5,
        "Fighting": 2,
        "Poison": 0.5,
        "Dragon": 2,
        "Dark": 2,
        "Steel": 0.5,
    },
}


@dataclass
class PokemonChosen:
    name: str | None = None
    id: int | None = None
    moves: list[str] = field(default_factory=list)
    tera_type: str | None = None

    def __post_init__(self) -> None:
        if self.name is None and self.id is None:
            raise ValueError("Provide either a Pokémon name or integer ID.")

        pokedex, _ = _load_data()
        pokemon_ids = list(pokedex)
        if self.id is not None:
            if isinstance(self.id, bool) or not isinstance(self.id, int):
                raise TypeError("PokemonChosen.id must be an integer.")
            if not 0 <= self.id < len(pokemon_ids):
                raise ValueError(
                    f"Pokémon index {self.id} is out of range; "
                    f"valid indices are 0 through {len(pokemon_ids) - 1}."
                )

        if self.name is not None:
            if not isinstance(self.name, str):
                raise TypeError("PokemonChosen.name must be a string Pokémon ID.")
            pokemon_id = self.name.casefold()
            if pokemon_id not in pokedex:
                raise ValueError(f"Unknown Pokémon ID: {self.name!r}")
            name_index = pokemon_ids.index(pokemon_id)
            if self.id is not None and self.id != name_index:
                raise ValueError(
                    f"Pokémon name {self.name!r} does not match index {self.id}."
                )
            self.name = pokemon_id
            self.id = name_index
        else:
            self.name = pokemon_ids[self.id]

        if self.tera_type is not None:
            self.tera_type = _normalize_tera_type(self.tera_type)

    def add_move(self, move_id: str) -> None:
        if not isinstance(move_id, str):
            raise TypeError("move_id must be a string.")
        move_id = move_id.casefold()
        pokemon = _get_pokemon(self.id)
        _, moves = _load_data()
        if move_id not in moves or move_id not in pokemon["movelist"]:
            raise ValueError(
                f"Move {move_id!r} is not available to Pokémon {self.name!r}."
            )
        self.moves.append(move_id)


@lru_cache(maxsize=1)
def _load_data() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    with POKEDEX_PATH.open(encoding="utf-8") as source:
        pokedex = json.load(source)
    with MOVES_PATH.open(encoding="utf-8") as source:
        moves = json.load(source)
    if not isinstance(pokedex, dict) or not isinstance(moves, dict):
        raise ValueError("Pokédex and moves JSON files must contain objects.")
    return pokedex, moves


@overload
def _get_pokemon(pokemon_id: str) -> dict[str, Any]: ...


@overload
def _get_pokemon(pokemon_id: int) -> dict[str, Any]: ...


def _get_pokemon(pokemon_id: str | int) -> dict[str, Any]:
    pokedex, _ = _load_data()
    if isinstance(pokemon_id, bool):
        raise ValueError(f"Unknown Pokémon ID: {pokemon_id!r}")
    if isinstance(pokemon_id, int):
        pokemon_entries = list(pokedex.values())
        if 0 <= pokemon_id < len(pokemon_entries):
            return pokemon_entries[pokemon_id]
        raise ValueError(
            f"Pokémon index {pokemon_id} is out of range; "
            f"valid indices are 0 through {len(pokemon_entries) - 1}."
        )
    try:
        return pokedex[pokemon_id.casefold()]
    except KeyError as error:
        raise ValueError(f"Unknown Pokémon ID: {pokemon_id!r}") from error


def _normalize_tera_type(tera_type: str) -> str:
    if not isinstance(tera_type, str):
        raise TypeError("tera_type must be a string or None.")
    for known_type in TYPE_EFFECTIVENESS:
        if tera_type.casefold() == known_type.casefold():
            return known_type
    raise ValueError(f"Unknown Tera type: {tera_type!r}")


def get_pokemon_options(pokemon_id: str | int) -> list[str]:
    """Return the eligible damaging move IDs available to a Pokémon."""
    pokemon = _get_pokemon(pokemon_id)
    return list(pokemon["movelist"])


def calculate_damage(
    attacker_id: str | int,
    defender_id: str | int,
    move_id: str,
    tera_type: str | None = None,
) -> int:
    """Calculate deterministic level-100 damage for one available move.

    Uses the standard base-damage formula, STAB, and type effectiveness.
    An optional Tera type applies Terastallization's offensive STAB rules.
    Random variation, critical hits, weather, items, and abilities are omitted.
    """
    attacker = _get_pokemon(attacker_id)
    defender = _get_pokemon(defender_id)
    if tera_type is not None:
        tera_type = _normalize_tera_type(tera_type)
    move_id = move_id.casefold()
    if move_id not in attacker["movelist"]:
        raise ValueError(
            f"Move {move_id!r} is not available to Pokémon {attacker_id!r}."
        )

    _, moves = _load_data()
    try:
        move = moves[move_id]
        power = move["power"]
        move_type = move["type"]
        attack_stat = move["attack_stat"]
        defense_stat = move["defense_stat"]
    except KeyError as error:
        raise ValueError(
            f"Move {move_id!r} is missing required data: {error.args[0]!r}"
        ) from error

    effectiveness = 1.0
    for defender_type in defender["type"]:
        effectiveness *= TYPE_EFFECTIVENESS.get(move_type, {}).get(defender_type, 1)
    if effectiveness == 0:
        return 0

    if attack_stat.startswith("target."):
        attack_value = defender["stats"][attack_stat.removeprefix("target.")]
    else:
        attack_value = attacker["stats"][attack_stat]
    defense_value = defender["stats"][defense_stat]

    damage = ((2 * LEVEL // 5 + 2) * power * attack_value // defense_value) // 50 + 2
    if tera_type is None:
        stab_multiplier = 1.5 if move_type in attacker["type"] else 1
    elif move_type == tera_type:
        stab_multiplier = 2 if tera_type in attacker["type"] else 1.5
    else:
        stab_multiplier = 1.5 if move_type in attacker["type"] else 1
    damage = int(damage * stab_multiplier)
    return int(damage * effectiveness)


def calculate_score(pokemon_id: str | int) -> int:
    """Return the Pokémon's BST score, calculated as floor(BST / 100)."""
    return _get_pokemon(pokemon_id)["bst"] // 100


def print_pokemon_choices(pokemon: list[PokemonChosen]) -> None:
    """Print the name and chosen moves for each Pokémon."""
    for choice in pokemon:
        moves = ", ".join(choice.moves) if choice.moves else "No moves chosen"
        print(f"{choice.name}: {moves}")


def calculate_total_weight(pokemon: list[PokemonChosen]) -> int:
    """Return the sum of the chosen Pokémon's scores as their total weight."""
    return sum(calculate_score(choice.id) for choice in pokemon)


def slowest_pokemon_speed(pokemon: list[PokemonChosen]) -> int:
    """Return the lowest level-100 speed among the chosen Pokémon."""
    if not pokemon:
        raise ValueError("Cannot find the slowest Pokémon in an empty list.")
    return min(_get_pokemon(choice.id)["stats"]["spe"] for choice in pokemon)


def calculate_highest_damage(
    attacker: PokemonChosen,
    defender: PokemonChosen,
) -> int:
    """Return the highest damage the attacker's chosen moves deal to a defender."""
    if not attacker.moves:
        return 0
    return max(
        calculate_damage(
            attacker.id,
            defender.id,
            move_id,
            tera_type=attacker.tera_type,
        )
        for move_id in attacker.moves
    )


def count_defeated_pokemon(
    team: list[PokemonChosen],
    enemies: list[PokemonChosen],
) -> int:
    """Count enemies at least one team member can KO in one hit."""
    return sum(
        any(
            calculate_highest_damage(member, enemy)
            >= _get_pokemon(enemy.id)["stats"]["hp"]
            for member in team
        )
        for enemy in enemies
    )
