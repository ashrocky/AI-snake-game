import streamlit as st
import time
import random
import sqlite3
import pandas as pd

# DB Functions
def init_db():
    conn = sqlite3.connect("snake_leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()

def insert_score(name, score):
    conn = sqlite3.connect("snake_leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leaderboard (name, score) VALUES (?, ?)", (name, score))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect("snake_leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_score_data():
    conn = sqlite3.connect("snake_leaderboard.db")
    df = pd.read_sql_query("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 10", conn)
    conn.close()
    return df

# Page setup
st.set_page_config(page_title="AI Snake Game", layout="centered")
st.title("🤖 AI Snake Game")
init_db()

# Game control state
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'game_paused' not in st.session_state:
    st.session_state.game_paused = False

# --- Sidebar Controls ---
# 🎯 Level
level = st.sidebar.selectbox("🎯 Level", ["Easy", "Medium", "Hard"])
speed_map = {"Easy": 0.3, "Medium": 0.2, "Hard": 0.1}
game_speed = speed_map[level]

theme = st.sidebar.radio("🌗 Theme", ["Dark", "Light"])
BG = "⬛" if theme == "Dark" else "⬜"

# 🛑 Game Control Buttons
if not st.session_state.game_started:
    if st.sidebar.button("▶️ Start Game"):
        st.session_state.game_started = True
        st.session_state.game_paused = False
        st.rerun()
else:
    if not st.session_state.game_paused:
        if st.sidebar.button("⏸️ Pause Game"):
            st.session_state.game_paused = True
    else:
        if st.sidebar.button("🔄 Resume Game"):
            st.session_state.game_paused = False

    if st.sidebar.button("🛑 End Game"):
        st.session_state.game_over = True
        st.session_state.game_started = False
        st.sidebar.warning("Game ended manually.")

snake_skin = st.sidebar.selectbox("🐍 Snake Emoji", ["🟩", "🟢", "🧪", "🟦"])
food_emoji = st.sidebar.selectbox("🍏 Food Emoji", ["🍎", "🍇", "🍒", "🍉"])

with st.sidebar.expander("📘 Instructions"):
    st.markdown("""
    - 🤖 Snake moves automatically using basic AI.
    - 🍎 Eat the food to grow and score points.
    - 💥 Game ends if the snake hits itself or the wall.

    ### Controls:
    - 🎮 Select theme, difficulty, and emojis in sidebar.
    - 💾 Save your name after game over.
    - 🔁 Restart anytime.
    """)

with st.sidebar.expander("ℹ️ About This Game"):
    st.markdown("""
    - 🐍 A fun AI-powered Snake game built with **Streamlit**.
    - 💡 Snake uses logic to chase food.
    - 🧠 Great for showcasing AI behavior visually.
    - 🏆 Scoreboard stores top players (locally using SQLite).
    """)

st.sidebar.subheader("📊 Score Chart")
df_scores = get_score_data()
if not df_scores.empty:
    st.sidebar.bar_chart(df_scores.set_index("name"))
else:
    st.sidebar.info("No scores yet!")

# --- Game Logic ---
WIDTH, HEIGHT = 20, 20

if 'snake' not in st.session_state:
    st.session_state.snake = [[10, 10]]
    st.session_state.food = [random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)]
    st.session_state.direction = "RIGHT"
    st.session_state.score = 0
    st.session_state.game_over = False

def ai_decide(snake, food):
    head = snake[0]
    if food[0] < head[0]:
        return "LEFT"
    elif food[0] > head[0]:
        return "RIGHT"
    elif food[1] < head[1]:
        return "UP"
    else:
        return "DOWN"

def move(snake, direction):
    head = snake[0].copy()
    if direction == "UP":
        head[1] -= 1
    elif direction == "DOWN":
        head[1] += 1
    elif direction == "LEFT":
        head[0] -= 1
    elif direction == "RIGHT":
        head[0] += 1
    return [head] + snake[:-1]

def check_collision(snake):
    head = snake[0]
    return (
        head in snake[1:] or
        head[0] < 0 or head[0] >= WIDTH or
        head[1] < 0 or head[1] >= HEIGHT
    )

# Run game only if started and not paused
if st.session_state.game_started and not st.session_state.game_paused and not st.session_state.game_over:
    st.session_state.direction = ai_decide(st.session_state.snake, st.session_state.food)
    st.session_state.snake = move(st.session_state.snake, st.session_state.direction)

    if check_collision(st.session_state.snake):
        st.session_state.game_over = True
    elif st.session_state.snake[0] == st.session_state.food:
        st.session_state.snake.append(st.session_state.snake[-1])
        st.session_state.score += 1
        st.session_state.food = [random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)]

# 🎞️ Grid Rendering
grid = [[BG for _ in range(WIDTH)] for _ in range(HEIGHT)]
for x, y in st.session_state.snake:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        grid[y][x] = snake_skin
fx, fy = st.session_state.food
grid[fy][fx] = food_emoji

canvas = st.empty()
canvas.markdown("<br>".join(["".join(row) for row in grid]), unsafe_allow_html=True)
st.markdown(f"### Score: {st.session_state.score}")

# 💬 Show status
if not st.session_state.game_started:
    st.info("Game not started. Click ▶️ Start Game to begin.")
elif st.session_state.game_paused:
    st.warning("⏸️ Game paused. Click 🔄 Resume to continue.")

# 💀 Game Over Controls
if st.session_state.game_over:
    st.session_state.game_started = False
    st.session_state.game_paused = False
    st.sidebar.error("💀 Game Over!")
    name = st.sidebar.text_input("👤 Your Name to Save Score:")
    if st.sidebar.button("💾 Save Score"):
        if name:
            insert_score(name, st.session_state.score)
            st.sidebar.success("✅ Score saved!")
        else:
            st.sidebar.warning("Please enter your name.")

    if st.sidebar.button("🔁 Restart Game"):
        st.session_state.update({
            "snake": [[10, 10]],
            "food": [random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)],
            "direction": "RIGHT",
            "score": 0,
            "game_over": False
        })
        st.rerun()
else:
    if st.session_state.game_started and not st.session_state.game_paused:
        time.sleep(game_speed)
        st.rerun()

if st.sidebar.button("🔁 Restart Fresh Game"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 🏅 Leaderboard
st.subheader("🏅 Top Players")
leaderboard = get_leaderboard()
for i, (name, scr) in enumerate(leaderboard, 1):
    st.write(f"{i}. {name} - {scr}")

def clear_leaderboard():
    conn = sqlite3.connect("snake_leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leaderboard")
    conn.commit()
    conn.close()

if st.sidebar.button("🗑️ Clear All Scores"):
    clear_leaderboard()
    st.sidebar.success("✅ Leaderboard cleared!")

# -- Sidebar: Admin Access --
with st.sidebar.expander("🔐 Admin Login"):
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if admin_pass == "admin123":
        st.success("✅ Access Granted")
        st.subheader("⚙️ Admin Tools")
        if st.button("🔁 Restart Fresh Game"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if st.button("🗑️ Clear All Leaderboard Scores"):
            clear_leaderboard()
            st.success("✅ Leaderboard cleared!")
    elif admin_pass:
        st.error("❌ Incorrect Password")

with st.sidebar.expander("⚙️ Admin Tools"):
    if st.button("🔁 Restart Fresh Game"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if st.button("🗑️ Clear All Leaderboard Scores"):
        clear_leaderboard()
        st.success("✅ All scores deleted!")
