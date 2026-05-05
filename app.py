from flask import Flask, render_template, render_template_string, request, session
import sqlite3
from pathlib import Path
from math_generator import Hero, MathDomain, generate_problem

app = Flask(__name__)
app.secret_key = "hero-academy-dev-secret"

DB_PATH = Path(__file__).with_name("hero_academy.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hero_progress (
            hero_name TEXT PRIMARY KEY,
            total_xp INTEGER NOT NULL DEFAULT 900,
            adaptive_level INTEGER NOT NULL DEFAULT 10,
            writing_xp INTEGER NOT NULL DEFAULT 0,
            writing_completed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO hero_progress
        (hero_name, total_xp, adaptive_level, writing_xp, writing_completed)
        VALUES ('Carlo', 900, 10, 0, 0)
        """
    )
    conn.commit()
    conn.close()


def load_progress():
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM hero_progress WHERE hero_name='Carlo'"
    ).fetchone()
    conn.close()
    return row


def save_progress(total_xp, adaptive_level, writing_xp, writing_completed):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE hero_progress
        SET total_xp=?, adaptive_level=?, writing_xp=?, writing_completed=?
        WHERE hero_name='Carlo'
        """,
        (total_xp, adaptive_level, writing_xp, writing_completed),
    )
    conn.commit()
    conn.close()


init_db()


UNLOCKS = [
    {"level": 10, "name": "🧠 Beast Mode Generator", "description": "Advanced mental math problems unlocked."},
    {"level": 12, "name": "⚡ Lightning Solver Badge", "description": "Fast-strike challenge status earned."},
    {"level": 15, "name": "👹 Boss Battle Mode", "description": "Multi-step monster problems unlocked."},
    {"level": 18, "name": "🥇 Rival Arena", "description": "Leaderboard pressure increases."},
    {"level": 20, "name": "👑 Genius Crown", "description": "Top-tier hero status unlocked."},
    {"level": 25, "name": "💀 Nightmare Boss Gauntlet", "description": "Extreme endgame challenge unlocked."},
]


def get_unlocked_rewards(level):
    return [unlock for unlock in UNLOCKS if level >= unlock["level"]]


def get_next_unlock(level):
    for unlock in UNLOCKS:
        if level < unlock["level"]:
            levels_needed = unlock["level"] - level
            return {
                "name": unlock["name"],
                "level": unlock["level"],
                "description": unlock["description"],
                "levels_needed": levels_needed,
            }
    return {
        "name": "🌌 Secret Impossible Mode",
        "level": level + 5,
        "description": "A hidden challenge mountain for elite heroes.",
        "levels_needed": 5,
    }


def get_hero_title(level):
    if level >= 20:
        return "👑 Genius Crown Hero"
    if level >= 18:
        return "🥇 Rival Arena Champion"
    if level >= 15:
        return "👹 Boss Battle Challenger"
    if level >= 12:
        return "⚡ Lightning Solver"
    if level >= 10:
        return "🧠 Beast Mode Hero"
    return "🌱 Hero in Training"


# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def start():
    return render_template("start.html")


# =========================================
# MATH ARENA
# =========================================
@app.route("/math-arena", methods=["GET", "POST"])
def math_arena():
    progress = load_progress()

    hero = Hero(
        name="Carlo",
        level=progress["adaptive_level"],
        xp=progress["total_xp"],
        weak_domains=[MathDomain.MULTIPLICATION],
        archetype="Warrior"
    )

    feedback = None
    unlocked_rewards = get_unlocked_rewards(progress["adaptive_level"])
    next_unlock = get_next_unlock(progress["adaptive_level"])
    hero_title = get_hero_title(progress["adaptive_level"])

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        correct = session.get("correct_answer")

        if answer.isdigit() and int(answer) == correct:
            xp_gain = session.get("xp_reward", 25)

            old_level = progress["adaptive_level"]
            new_total_xp = progress["total_xp"] + xp_gain
            new_level = min(old_level + 1, 20)
            session["total_xp"] = new_total_xp
            session["adaptive_level"] = new_level
            save_progress(
                new_total_xp,
                new_level,
                progress["writing_xp"],
                progress["writing_completed"],
            )
            progress = load_progress()
            unlocked_rewards = get_unlocked_rewards(new_level)
            next_unlock = get_next_unlock(new_level)
            hero_title = get_hero_title(new_level)

            unlock_note = ""
            newly_unlocked = [unlock for unlock in UNLOCKS if unlock["level"] == new_level]
            if newly_unlocked:
                unlock_note = f" New unlock: {newly_unlocked[0]['name']}!"

            feedback = {
                "status": "correct",
                "message": f"Correct! +{xp_gain} XP earned. Level {new_level} reached.{unlock_note}"
            }

        else:
            new_level = max(progress["adaptive_level"] - 1, 8)
            session["adaptive_level"] = new_level
            save_progress(
                progress["total_xp"],
                new_level,
                progress["writing_xp"],
                progress["writing_completed"],
            )
            progress = load_progress()
            unlocked_rewards = get_unlocked_rewards(new_level)
            next_unlock = get_next_unlock(new_level)
            hero_title = get_hero_title(new_level)

            feedback = {
                "status": "incorrect",
                "message": f"Not quite. Correct answer was {correct}."
            }

    problem = generate_problem(hero)

    session["correct_answer"] = problem.answer
    session["xp_reward"] = problem.xp_reward

    return render_template(
        "math_arena.html",
        problem=problem,
        feedback=feedback,
        total_xp=progress["total_xp"],
        adaptive_level=progress["adaptive_level"],
        unlocked_rewards=unlocked_rewards,
        next_unlock=next_unlock,
        hero_title=hero_title,
    )


# =========================================
# WRITING QUEST
# =========================================
@app.route("/writing-quest", methods=["GET", "POST"])
def writing_quest():

    prompt = "Carlo solved a hard math mission using mental shortcuts. Explain how he did it in 5 strong sentences."

    progress = load_progress()
    writing_xp = progress["writing_xp"]
    completed = progress["writing_completed"]
    last_score = session.get("last_score", 0)

    feedback = None

    if request.method == "POST":
        response = request.form.get("writing_response", "").strip()

        score = 0

        if len(response.split()) >= 40:
            score += 1
        if response.count(".") >= 4:
            score += 1
        if any(word in response.lower() for word in ["first", "next", "because", "finally"]):
            score += 1
        if any(char.isdigit() for char in response):
            score += 1

        session["last_score"] = score

        if score >= 3:
            gained = score * 15
            session["writing_xp"] = writing_xp + gained
            session["writing_completed"] = completed + 1
            save_progress(
                load_progress()["total_xp"],
                load_progress()["adaptive_level"],
                session["writing_xp"],
                session["writing_completed"],
            )

            feedback = {
                "status": "correct",
                "headline": "Quest complete!",
                "notes": [f"+{gained} Writing XP earned."]
            }
        else:
            feedback = {
                "status": "grow",
                "headline": "Good start. Sharpen it more.",
                "notes": ["Use more detail, transitions, and full sentences."]
            }

    return render_template_string("""
<!doctype html>
<html>
<head>
<title>Writing Quest</title>
<style>
body{
background:#1e1b4b;
font-family:Arial;
color:white;
padding:30px;
}
.card{
max-width:900px;
margin:auto;
background:#2e1065;
padding:30px;
border-radius:20px;
}
textarea{
width:100%;
height:220px;
font-size:18px;
padding:15px;
border-radius:15px;
}
button,a{
padding:14px 20px;
border-radius:12px;
font-weight:bold;
text-decoration:none;
margin-top:15px;
display:inline-block;
}
button{background:#d946ef;color:white;border:none;}
a{background:#444;color:white;}
</style>
</head>
<body>
<div class="card">
<h1>✍🏾 Writing Quest</h1>

<p>{{ prompt }}</p>

<p>Writing XP: {{ writing_xp }}</p>
<p>Completed: {{ completed }}</p>
<p>Last Score: {{ last_score }}/4</p>

{% if feedback %}
<h3>{{ feedback.headline }}</h3>
<ul>
{% for note in feedback.notes %}
<li>{{ note }}</li>
{% endfor %}
</ul>
{% endif %}

<form method="POST">
<textarea name="writing_response"></textarea><br>
<button type="submit">Submit Writing Quest ⚡</button>
<a href="/">⬅ Back Home</a>
</form>
</div>
</body>
</html>
""",
prompt=prompt,
writing_xp=session.get("writing_xp", 0),
completed=session.get("writing_completed", 0),
last_score=session.get("last_score", 0),
feedback=feedback
)

 
# =========================================
# BOSS BATTLE MODE
# =========================================
@app.route("/boss-battle", methods=["GET", "POST"])
def boss_battle():
    progress = load_progress()
    level = progress["adaptive_level"]

    if level < 15:
        return render_template_string("""
        <html><body style='font-family:Arial;background:#140a0a;color:white;padding:40px;'>
        <h1>👹 Boss Battle Locked</h1>
        <p>Reach Level 15 to challenge the first boss.</p>
        <p>Current Level: {{ level }}</p>
        <a href='/dashboard' style='color:#facc15;'>⬅ Return to Dashboard</a>
        </body></html>
        """, level=level)

    if "boss_stage" not in session:
        session["boss_stage"] = 1
        session["boss_wins"] = 0
        session["boss_hp"] = 3

    hero = Hero(
        name="Carlo",
        level=max(level, 15),
        xp=progress["total_xp"],
        weak_domains=[MathDomain.MULTIPLICATION],
        archetype="Warrior",
    )

    feedback = None

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        correct = session.get("boss_answer")

        if answer.replace('.', '', 1).isdigit() and str(answer) == str(correct):
            session["boss_wins"] += 1
            session["boss_stage"] += 1
            feedback = "⚔️ Direct hit! Boss staggered."
        else:
            session["boss_hp"] -= 1
            feedback = f"💥 Missed strike. Correct answer was {correct}."

    if session.get("boss_wins", 0) >= 3:
        bonus_xp = 500
        new_total = progress["total_xp"] + bonus_xp
        save_progress(new_total, progress["adaptive_level"], progress["writing_xp"], progress["writing_completed"])
        session.pop("boss_stage", None)
        session.pop("boss_wins", None)
        session.pop("boss_hp", None)
        return render_template_string("""
        <!doctype html>
        <html>
        <head>
        <title>Boss Defeated</title>
        <style>
        body{
            margin:0;
            font-family:Arial, sans-serif;
            background:radial-gradient(circle at top, #14532d, #03150b 72%);
            color:white;
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            overflow:hidden;
        }
        .victory-card{
            width:min(760px, 92vw);
            text-align:center;
            padding:42px;
            border-radius:28px;
            background:rgba(6, 78, 59, 0.88);
            border:2px solid #facc15;
            box-shadow:0 0 45px rgba(250, 204, 21, 0.35);
            animation:pulseGlow 1.8s ease-in-out infinite alternate;
            position:relative;
            z-index:2;
        }
        h1{font-size:56px;margin:0 0 18px;color:#fef08a;}
        p{font-size:26px;line-height:1.45;margin:10px 0;}
        .xp{font-size:40px;font-weight:900;color:#86efac;margin:18px 0;}
        a{
            display:inline-block;
            margin-top:22px;
            padding:16px 24px;
            border-radius:16px;
            background:linear-gradient(90deg,#f59e0b,#f97316);
            color:white;
            text-decoration:none;
            font-weight:900;
        }
        .confetti{
            position:fixed;
            top:-20px;
            width:10px;
            height:16px;
            border-radius:3px;
            animation:fall linear forwards;
            z-index:1;
        }
        @keyframes fall {
            to { transform:translateY(110vh) rotate(720deg); opacity:0; }
        }
        @keyframes pulseGlow {
            from { transform:scale(1); box-shadow:0 0 35px rgba(250,204,21,0.22); }
            to { transform:scale(1.02); box-shadow:0 0 55px rgba(250,204,21,0.55); }
        }
        </style>
        </head>
        <body>
            <div class='victory-card'>
                <h1>🏆 BOSS DEFEATED!</h1>
                <p>Carlo cleared all three elite phases.</p>
                <div class='xp'>+500 XP</div>
                <p>The arena bows to the champion.</p>
                <a href='/dashboard'>View Dashboard 👑</a>
            </div>
        <script>
        function playTone(freq, duration, type='triangle', volume=0.09){
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if(!AudioContext) return;
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.frequency.value = freq; osc.type = type;
            gain.gain.setValueAtTime(volume, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
            osc.start(); osc.stop(ctx.currentTime + duration);
        }
        function fanfare(){
            playTone(523,0.14); setTimeout(()=>playTone(659,0.14),140);
            setTimeout(()=>playTone(784,0.16),280);
            setTimeout(()=>playTone(1047,0.28),430);
        }
        function confetti(){
            const colors=['#facc15','#fb7185','#38bdf8','#86efac','#ffffff','#f97316'];
            for(let i=0;i<120;i++){
                const d=document.createElement('div');
                d.className='confetti';
                d.style.left=Math.random()*100+'vw';
                d.style.background=colors[Math.floor(Math.random()*colors.length)];
                d.style.animationDuration=(1.2+Math.random()*1.8)+'s';
                d.style.animationDelay=(Math.random()*0.4)+'s';
                document.body.appendChild(d);
                setTimeout(()=>d.remove(),3200);
            }
        }
        fanfare();
        confetti();
        </script>
        </body>
        </html>
        """)

    if session.get("boss_hp", 0) <= 0:
        session.pop("boss_stage", None)
        session.pop("boss_wins", None)
        session.pop("boss_hp", None)
        return render_template_string("""
        <html><body style='font-family:Arial;background:#1f0a0a;color:white;padding:40px;'>
        <h1>☠️ Boss Battle Failed</h1>
        <p>The boss survives today. Train harder and return stronger.</p>
        <a href='/math-arena' style='color:#fca5a5;'>Return to Arena</a>
        </body></html>
        """)

    problem = generate_problem(hero)
    session["boss_answer"] = problem.answer

    return render_template_string("""
    <!doctype html>
    <html>
    <head><title>Boss Battle</title>
    <style>
    body{background:#140a0a;color:white;font-family:Arial;padding:30px;}
    .card{max-width:850px;margin:auto;background:#2a0f0f;padding:30px;border-radius:24px;border:2px solid #ef4444;}
    input{width:100%;padding:18px;font-size:28px;border-radius:16px;margin:20px 0;}
    button,a{padding:14px 20px;border-radius:14px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px;}
    button{background:#dc2626;color:white;border:none;} a{background:#444;color:white;}
    .big{font-size:64px;font-weight:900;text-align:center;margin:25px 0;}
    </style></head>
    <body><div class='card'>
    <h1>👹 Boss Battle Mode</h1>
    <p>Phase {{ stage }} of 3 • Boss HP: {{ hp }}</p>
    {% if feedback %}<p><strong>{{ feedback }}</strong></p>{% endif %}
    <p>{{ story }}</p>
    <div class='big'>{{ question }}</div>
    <form method='POST'>
      <input name='answer' placeholder='Enter answer' autofocus>
      <button type='submit'>⚔️ Strike Boss</button>
    </form>
    <a href='/dashboard'>⬅ Retreat</a>
    </div></body></html>
    """, stage=session["boss_stage"], hp=session["boss_hp"], feedback=feedback, story=problem.story_context, question=problem.question)

# =========================================
# DASHBOARD
# =========================================
@app.route("/dashboard")
def dashboard():

    progress = load_progress()
    total_xp = progress["total_xp"]
    writing_xp = progress["writing_xp"]
    grand_total = total_xp + writing_xp

    leaderboard = [
        {"name": "Carlo", "xp": grand_total},
        {"name": "Jayden Lightning", "xp": 1380},
        {"name": "Nia Word Wizard", "xp": 1245},
        {"name": "Malik Calculator", "xp": 1175},
        {"name": "Zion Pattern King", "xp": 1040},
    ]

    leaderboard = sorted(leaderboard, key=lambda x: x["xp"], reverse=True)
    unlocked_rewards = get_unlocked_rewards(progress["adaptive_level"])
    next_unlock = get_next_unlock(progress["adaptive_level"])
    hero_title = get_hero_title(progress["adaptive_level"])

    return render_template_string("""
<!doctype html>
<html>
<head>
<title>Dashboard</title>
<style>
body{
background:#052e2b;
font-family:Arial;
color:white;
padding:30px;
}
.card{
max-width:900px;
margin:auto;
background:#064e3b;
padding:30px;
border-radius:20px;
}
.row{
padding:14px;
margin:8px 0;
background:#14532d;
border-radius:12px;
font-size:20px;
}
.gold{border:2px solid gold;}
a{
padding:14px 20px;
background:#333;
color:white;
text-decoration:none;
border-radius:12px;
display:inline-block;
margin-top:15px;
}
</style>
</head>
<body>
<div class="card">
<h1>🏆 Progress Dashboard</h1>

<p><strong>Hero Title:</strong> {{ hero_title }}</p>
<p><strong>Total XP:</strong> {{ grand_total }}</p>
<p><strong>Math Level:</strong> {{ level }}</p>

<h2>🔓 Unlocked Rewards</h2>
{% if unlocked_rewards %}
    {% for reward in unlocked_rewards %}
        <div class="row gold">{{ reward.name }} — {{ reward.description }}</div>
    {% endfor %}
{% else %}
    <div class="row">No unlocks yet. Keep training.</div>
{% endif %}

<h2>🎯 Next Unlock</h2>
<div class="row">
    {{ next_unlock.name }} at Level {{ next_unlock.level }}<br>
    {{ next_unlock.description }}<br>
    Levels needed: {{ next_unlock.levels_needed }}
</div>

<h2>🥇 School Leaderboard</h2>

{% for p in leaderboard %}
<div class="row {% if p.name == 'Carlo' %}gold{% endif %}">
#{{ loop.index }} {{ p.name }} — {{ p.xp }} XP
</div>
{% endfor %}

<a href='/boss-battle'>👹 Boss Battle</a>
<a href="/">⬅ Back Home</a>
</div>
</body>
</html>
""",
grand_total=grand_total,
level=progress["adaptive_level"],
leaderboard=leaderboard,
unlocked_rewards=unlocked_rewards,
next_unlock=next_unlock,
hero_title=hero_title
)


# =========================================
# RUN APP
# =========================================
if __name__ == "__main__":
    app.run(debug=True)