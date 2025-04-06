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

def clear_leaderboard():
    conn = sqlite3.connect("snake_leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leaderboard")
    conn.commit()
    conn.close()

# Page setup
st.set_page_config(page_title="AI Snake Game", layout="centered")
st.title("🤖 AI Snake Game")
init_db()

# --- Sidebar Controls ---
# 🎯 LEVEL
difficulty = st.sidebar.selectbox("🎯 LEVEL ", ["Easy", "Medium", "Hard"])
speed_map = {"Easy": 0.3, "Medium": 0.2, "Hard": 0.1}
game_speed = speed_map[LEVEL]

# 🌈 Theme
theme = st.sidebar.radio("🌗 Theme", ["Dark", "Light"])
BG = "⬛" if theme == "Dark" else "⬜"

# 🛑 End Game Button
if st.sidebar.button("🛑 End Game"):
    st.session_state.game_over = True
    st.sidebar.warning("Game ended manually.")

# 🐍 Snake & Food Emoji
snake_skin = st.sidebar.selectbox("🐍 Snake Emoji", ["🟩", "🟢", "🧪", "🟦"])
food_emoji = st.sidebar.selectbox("🍏 Food Emoji", ["🍎", "🍇", "🍒", "🍉"])

# 📘 Instructions
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

# ℹ️ About
with st.sidebar.expander("ℹ️ About This Game"):
    st.markdown("""
    - 🐍 A fun AI-powered Snake game built with **Streamlit**.
    - 💡 Snake uses logic to chase food.
    - 🧠 Great for showcasing AI behavior visually.
    - 🏆 Scoreboard stores top players (locally using SQLite).
    """)

# 📊 Score Chart
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

# AI logic
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

# Run frame
if not st.session_state.game_over:
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

# 💀 Game Over Controls (in sidebar)
if st.session_state.game_over:
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

# 🛡️ Admin Controls in Sidebar
with st.sidebar.expander("🔐 Admin Login"):
    admin_pass = st.text_input("Enter Admin Password", type="password", key="admin_pass")
    if admin_pass == "admin123":  # You can change this password
        st.sidebar.success("✅ Access Granted")
        st.sidebar.subheader("⚙️ Admin Tools")
        if st.sidebar.button("🔁 Restart Fresh Game", key="admin_restart"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        if st.sidebar.button("🗑️ Clear All Leaderboard Scores", key="admin_clear"):
            clear_leaderboard()
            st.sidebar.success("✅ Leaderboard cleared!")
    elif admin_pass:
        st.sidebar.error("❌ Incorrect Password")


