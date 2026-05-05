# ============================================================
# Hero Academy — Math Challenge Generator
# Developer: Sommer Turner
# Purpose:   Dynamically generates math problems calibrated to
#            a hero's current level, weak areas, and story context.
#            Problems are wrapped in narrative drawn from Black
#            hero archetypes to keep engagement high.
# ============================================================

import random
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────────
# Domain Models
# ─────────────────────────────────────────────

class Difficulty(Enum):
    APPRENTICE = 1   # Level 1–3:  single-digit operations
    WARRIOR    = 2   # Level 4–6:  double-digit, intro to fractions
    CHAMPION   = 3   # Level 7–9:  multi-step, decimals, basic algebra
    LEGEND     = 4   # Level 10+:  word problems, ratios, pre-algebra


class MathDomain(Enum):
    ADDITION       = "addition"
    SUBTRACTION    = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION       = "division"
    FRACTIONS      = "fractions"
    ALGEBRA        = "algebra"
    PERCENTAGES    = "percentages"
    PATTERNS       = "patterns"
    POWERS         = "powers"


@dataclass
class Hero:
    name: str
    level: int
    xp: int = 0
    weak_domains: list[MathDomain] = field(default_factory=list)
    archetype: str = "Warrior"   # e.g. Warrior, Scholar, Guardian, Explorer


@dataclass
class MathProblem:
    question: str
    answer: float
    domain: MathDomain
    difficulty: Difficulty
    story_context: str
    xp_reward: int
    hint: Optional[str] = None


# ─────────────────────────────────────────────
# Narrative Engine
# ─────────────────────────────────────────────

# Story fragments keyed by hero archetype.
# Each problem is wrapped in a narrative beat so math
# feels like part of an adventure, not a worksheet.
STORY_CONTEXTS = {
    "Warrior": [
        "Your blade is sharp, but your mind must be sharper.",
        "The enemy fortress has {n} guards on each of its {m} towers.",
        "You must divide your {n} warriors across {m} battalions equally.",
        "Your shield can absorb {n} hits before it breaks. You've taken {m} already.",
    ],
    "Scholar": [
        "The ancient scroll reveals a hidden equation.",
        "The library holds {n} books across {m} shelves — how many per shelf?",
        "You need {n} spell components but only have {m}. How many more?",
        "The potion requires exactly {n} drops split into {m} vials.",
    ],
    "Guardian": [
        "The village is counting on you. Think carefully.",
        "You must protect {n} civilians across {m} safe houses.",
        "Your supply cache holds {n} rations for {m} days — daily share?",
        "The wall needs {n} stones per section across {m} sections.",
    ],
    "Explorer": [
        "Uncharted territory. Every calculation matters out here.",
        "Your map shows {n} miles split across {m} days of travel.",
        "You've collected {n} artifacts from {m} ruins — average per site?",
        "The river is {n} feet wide. Your rope is {m} feet. Difference?",
    ],
}


def _get_story_context(archetype: str, a: int, b: int) -> str:
    """Pull a narrative fragment for this hero's archetype and fill in numbers."""
    fragments = STORY_CONTEXTS.get(archetype, STORY_CONTEXTS["Warrior"])
    template = random.choice(fragments)
    return template.format(n=a, m=b)


# ─────────────────────────────────────────────
# Difficulty Resolver
# ─────────────────────────────────────────────

def _resolve_difficulty(level: int) -> Difficulty:
    if level <= 3:
        return Difficulty.APPRENTICE
    elif level <= 6:
        return Difficulty.WARRIOR
    elif level <= 9:
        return Difficulty.CHAMPION
    return Difficulty.LEGEND


def _resolve_operand_range(difficulty: Difficulty) -> tuple[int, int]:
    """Return (min, max) for random operand generation per difficulty."""
    ranges = {
        Difficulty.APPRENTICE: (1, 9),
        Difficulty.WARRIOR:    (10, 49),
        Difficulty.CHAMPION:   (10, 99),
        Difficulty.LEGEND:     (12, 199),
    }
    return ranges[difficulty]


# ─────────────────────────────────────────────
# Problem Generators (one per domain)
# ─────────────────────────────────────────────

def _gen_addition(difficulty: Difficulty, archetype: str) -> MathProblem:
    lo, hi = _resolve_operand_range(difficulty)
    a, b = random.randint(lo, hi), random.randint(lo, hi)
    return MathProblem(
        question=f"{a} + {b} = ?",
        answer=a + b,
        domain=MathDomain.ADDITION,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, b),
        xp_reward=difficulty.value * 10,
        hint=f"Start with {a}, then count up {b} more.",
    )


def _gen_subtraction(difficulty: Difficulty, archetype: str) -> MathProblem:
    lo, hi = _resolve_operand_range(difficulty)
    a = random.randint(lo, hi)
    b = random.randint(lo, a)   # ensure non-negative result
    return MathProblem(
        question=f"{a} - {b} = ?",
        answer=a - b,
        domain=MathDomain.SUBTRACTION,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, b),
        xp_reward=difficulty.value * 10,
        hint=f"Start at {a} and count back {b}.",
    )


def _gen_multiplication(difficulty: Difficulty, archetype: str) -> MathProblem:
    lo, hi = _resolve_operand_range(difficulty)

    if difficulty == Difficulty.LEGEND:
        special = random.choice(["near_1000", "times_125", "double_digits"])
        if special == "near_1000":
            a = random.choice([989, 997, 996, 1001, 1003])
            b = random.randint(21, 99)
        elif special == "times_125":
            a = 125
            b = random.randint(12, 96)
        else:
            a = random.randint(21, 99)
            b = random.randint(21, 99)
    else:
        a = random.randint(2, min(hi, 12))
        b = random.randint(lo, hi)

    return MathProblem(
        question=f"{a} × {b} = ?",
        answer=a * b,
        domain=MathDomain.MULTIPLICATION,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, b),
        xp_reward=difficulty.value * 25,
        hint=f"Look for shortcuts: distribute, break apart, or use place value.",
    )


def _gen_division(difficulty: Difficulty, archetype: str) -> MathProblem:
    lo, hi = _resolve_operand_range(difficulty)

    b = random.randint(2, min(hi, 12))
    quotient = random.randint(2, max(2, hi // b))
    a = b * quotient

    return MathProblem(
        question=f"{a} ÷ {b} = ?",
        answer=a // b,
        domain=MathDomain.DIVISION,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, b),
        xp_reward=difficulty.value * 15,
        hint=f"How many times does {b} fit into {a}?",
    )


def _gen_fractions(difficulty: Difficulty, archetype: str) -> MathProblem:
    """Simple fraction addition with common denominators for now."""
    denom = random.choice([2, 3, 4, 5, 8, 10])
    a = random.randint(1, denom - 1)
    b = random.randint(1, denom - 1)
    answer = round((a + b) / denom, 4)
    return MathProblem(
        question=f"{a}/{denom} + {b}/{denom} = ?",
        answer=answer,
        domain=MathDomain.FRACTIONS,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, b),
        xp_reward=difficulty.value * 20,
        hint=f"The bottom number stays {denom}. Just add the tops.",
    )


def _gen_algebra(difficulty: Difficulty, archetype: str) -> MathProblem:
    """One-step linear equation: x + b = c  or  a * x = c."""
    a = random.randint(2, 12)
    x = random.randint(1, 20)
    c = a * x
    return MathProblem(
        question=f"{a} × n = {c} — what is n?",
        answer=x,
        domain=MathDomain.ALGEBRA,
        difficulty=difficulty,
        story_context=_get_story_context(archetype, a, c),
        xp_reward=difficulty.value * 25,
        hint=f"Divide {c} by {a} to find n.",
    )


def _gen_percentages(difficulty: Difficulty, archetype: str) -> MathProblem:
    percent = random.choice([10, 12, 15, 18, 20, 25, 40])
    base = random.choice([120, 240, 360, 480, 750, 900])
    answer = round((percent / 100) * base, 2)
    return MathProblem(
        question=f"{percent}% of {base} = ?",
        answer=answer,
        domain=MathDomain.PERCENTAGES,
        difficulty=difficulty,
        story_context="A merchant offers a strategic discount. Calculate fast.",
        xp_reward=difficulty.value * 30,
        hint="Convert the percent to a fraction or decimal.",
    )


def _gen_powers(difficulty: Difficulty, archetype: str) -> MathProblem:
    base = random.choice([12, 15, 24, 36, 48, 144])
    if base == 144:
        exponent = 2
    else:
        exponent = 2
    answer = base ** exponent
    return MathProblem(
        question=f"{base}^{exponent} = ?",
        answer=answer,
        domain=MathDomain.POWERS,
        difficulty=difficulty,
        story_context="The energy crystal amplifies by powers.",
        xp_reward=difficulty.value * 35,
        hint="Square the number carefully.",
    )


def _gen_patterns(difficulty: Difficulty, archetype: str) -> MathProblem:
    start = random.randint(3, 15)
    step = random.randint(4, 18)
    terms = [start + step * i for i in range(4)]
    answer = start + step * 4
    return MathProblem(
        question=f"{terms[0]}, {terms[1]}, {terms[2]}, {terms[3]}, ?",
        answer=answer,
        domain=MathDomain.PATTERNS,
        difficulty=difficulty,
        story_context="Decode the hidden number pattern.",
        xp_reward=difficulty.value * 28,
        hint="Find how much each term increases.",
    )


# ─────────────────────────────────────────────
# Domain Selector — favors weak areas
# ─────────────────────────────────────────────

DOMAIN_GENERATORS = {
    MathDomain.ADDITION:       _gen_addition,
    MathDomain.SUBTRACTION:    _gen_subtraction,
    MathDomain.MULTIPLICATION: _gen_multiplication,
    MathDomain.DIVISION:       _gen_division,
    MathDomain.FRACTIONS:      _gen_fractions,
    MathDomain.ALGEBRA:        _gen_algebra,
    MathDomain.PERCENTAGES:    _gen_percentages,
    MathDomain.PATTERNS:       _gen_patterns,
    MathDomain.POWERS:         _gen_powers,
}

# Domains unlocked per difficulty tier
DOMAINS_BY_DIFFICULTY = {
    Difficulty.APPRENTICE: [MathDomain.ADDITION, MathDomain.SUBTRACTION],
    Difficulty.WARRIOR:    [MathDomain.ADDITION, MathDomain.SUBTRACTION,
                            MathDomain.MULTIPLICATION, MathDomain.DIVISION],
    Difficulty.CHAMPION:   [MathDomain.MULTIPLICATION, MathDomain.DIVISION,
                            MathDomain.FRACTIONS],
    Difficulty.LEGEND:     [MathDomain.MULTIPLICATION, MathDomain.FRACTIONS,
                            MathDomain.ALGEBRA, MathDomain.PERCENTAGES,
                            MathDomain.PATTERNS, MathDomain.POWERS],
}


def _select_domain(hero: Hero, difficulty: Difficulty) -> MathDomain:
    """
    Selects a math domain for this problem.
    If the hero has weak domains that are available at this difficulty,
    we weight toward those — extra practice where it's needed most.
    """
    available = DOMAINS_BY_DIFFICULTY[difficulty]
    weak_and_available = [d for d in hero.weak_domains if d in available]

    # 60% chance to pull from weak domains if any exist
    if weak_and_available and random.random() < 0.6:
        return random.choice(weak_and_available)

    return random.choice(available)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def generate_problem(hero: Hero) -> MathProblem:
    """
    Generate a single math problem calibrated to the hero's level,
    weighted toward their weak areas, wrapped in story context.

    Args:
        hero: The Hero object representing the current player.

    Returns:
        A MathProblem ready to display in the UI.
    """
    difficulty = _resolve_difficulty(hero.level)
    domain = _select_domain(hero, difficulty)
    generator = DOMAIN_GENERATORS[domain]
    return generator(difficulty, hero.archetype)


def generate_challenge_set(hero: Hero, count: int = 5) -> list[MathProblem]:
    """
    Generate a balanced set of problems for a full challenge session.
    Ensures variety — no domain repeats back-to-back.

    Args:
        hero:  The current player's Hero object.
        count: Number of problems to generate (default 5).

    Returns:
        A list of MathProblem objects, varied by domain.
    """
    problems = []
    last_domain = None

    for _ in range(count):
        problem = generate_problem(hero)
        # Avoid consecutive same-domain problems
        attempts = 0
        while problem.domain == last_domain and attempts < 5:
            problem = generate_problem(hero)
            attempts += 1
        problems.append(problem)
        last_domain = problem.domain

    return problems


def calculate_xp_reward(problem: MathProblem, correct: bool,
                         time_seconds: float) -> int:
    """
    Calculate final XP awarded after answering a problem.
    Bonuses for speed; no penalty for wrong answers (growth mindset).

    Args:
        problem:       The problem that was answered.
        correct:       Whether the answer was correct.
        time_seconds:  How long the hero took to answer.

    Returns:
        XP integer to add to the hero's total.
    """
    if not correct:
        return 0

    base_xp = problem.xp_reward

    # Speed bonus: full bonus under 10s, scaled reduction after
    if time_seconds <= 10:
        speed_bonus = int(base_xp * 0.5)
    elif time_seconds <= 20:
        speed_bonus = int(base_xp * 0.25)
    else:
        speed_bonus = 0

    return base_xp + speed_bonus


# ─────────────────────────────────────────────
# Demo — run directly to preview output
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate Carlo: Level 4 Warrior, weak in multiplication
    carlo = Hero(
        name="Carlo",
        level=4,
        xp=340,
        weak_domains=[MathDomain.MULTIPLICATION],
        archetype="Warrior",
    )

    print("=" * 58)
    print(f"  HERO ACADEMY — Challenge Generator Demo")
    print(f"  Hero: {carlo.name} | Level {carlo.level} | Archetype: {carlo.archetype}")
    print("=" * 58)

    challenge_set = generate_challenge_set(carlo, count=5)

    for i, problem in enumerate(challenge_set, 1):
        print(f"\n  Problem {i} [{problem.domain.value.upper()} | "
              f"{problem.difficulty.name}]")
        print(f"  Story:    {problem.story_context}")
        print(f"  Question: {problem.question}")
        print(f"  Answer:   {problem.answer}")
        print(f"  Hint:     {problem.hint}")
        print(f"  XP:       +{problem.xp_reward} base "
              f"(+{int(problem.xp_reward * 0.5)} speed bonus if under 10s)")

    print("\n" + "=" * 58)
    print("  Generator running cleanly. Ready for Flask integration.")
    print("=" * 58)
