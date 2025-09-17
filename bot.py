import os, random, json, time, requests, telebot, threading
from telebot import types
from dotenv import load_dotenv
try:
    import openai
except:
    openai = None

# ---------------------- ENV ---------------------- #
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")
bot = telebot.TeleBot(TOKEN)
if openai and OPENAI_KEY: openai.api_key = OPENAI_KEY

# ---------------------- USER DATA ---------------------- #
DATA_FOLDER = "data"
USER_FILE = os.path.join(DATA_FOLDER, "users.json")
if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
if not os.path.exists(USER_FILE): open(USER_FILE, "w").write("{}")

def load_users(): 
    with open(USER_FILE, "r") as f: return json.load(f)
def save_users(data): 
    with open(USER_FILE, "w") as f: json.dump(data, f, indent=4)
def init_user(uid,name):
    users=load_users()
    if str(uid) not in users:
        users[str(uid)]={"memory":"","trivia_score":0,"mini_game_score":0,"daily_reminders":True,"name":name}
        save_users(users)

# ---------------------- UTILITIES ---------------------- #
def get_joke():
    try: return requests.get("https://v2.jokeapi.dev/joke/Any?type=single").json().get("joke","No joke 😢")
    except: return "Couldn't fetch joke 😢"
def get_quote():
    try: r = requests.get("https://api.quotable.io/random").json(); return f'"{r["content"]}" — {r["author"]}'
    except: return "Couldn't fetch quote 😢"
def random_fact():
    try: return requests.get("https://uselessfacts.jsph.pl/random.json?language=en").json().get("text")
    except: return "No fact 😢"
def get_meme(cat="memes"):
    try: return requests.get(f"https://meme-api.com/gimme/{cat}").json().get("url")
    except: return None
def get_gif(keyword="funny"):
    try: res = requests.get(f"https://api.tenor.com/v1/search?q={keyword}&key=LIVDSRZULELA&limit=10").json(); return random.choice(res['results'])['media'][0]['gif']['url']
    except: return None
def get_anime(name="Naruto"):
    try: res = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1").json(); a=res['data'][0]; return f"🎬 {a['title']}\nEpisodes:{a['episodes']}\nScore:{a['score']}\nURL:{a['url']}"
    except: return "Anime not found 😢"
def get_weather(city):
    if not WEATHER_KEY: return "Weather API key not set 😢"
    try: r=requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric").json(); return f"🌡 {r['main']['temp']}°C\n🌥 {r['weather'][0]['description']}" if r.get("main") else "City not found!"
    except: return "Weather API error 😢"

# ---------------------- AI CHAT ---------------------- #
def ai_response(uid,text):
    users=load_users(); memory=users.get(str(uid),{}).get("memory","")
    responses={"hello":["Hi! 😎","হাই! কেমন আছো?"],"hi":["Hello! 😁","হ্যালো!"],"how are you":["I'm good, how about you?","আমি ভালো আছি! তুমি কেমন?"],"i miss you":["I miss you too 💖","আমিও তোমাকে মিস করছি ❤️"],"flirt":["You're adorable 😘","তুমি অনেক সুন্দর! 😍"]}
    for k,v in responses.items():
        if k in text.lower(): reply=random.choice(v); break
    else:
        if openai and OPENAI_KEY:
            try: reply=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":f"{memory}\nUser: {text}"}]).choices[0].message.content
            except: reply="I'm here for you 💕"
        else: reply="I'm here for you 💕"
    if str(uid) not in users: users[str(uid)]={"memory":""}
    users[str(uid)]["memory"]+=f"\nUser:{text}\nBot:{reply}"; save_users(users)
    return reply

# ---------------------- MENU ---------------------- #
def main_menu():
    m=types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("😂 Joke", callback_data="joke"),
        types.InlineKeyboardButton("📺 Anime", callback_data="anime"),
        types.InlineKeyboardButton("🖼 Meme", callback_data="meme"),
        types.InlineKeyboardButton("💡 Quote", callback_data="quote"),
        types.InlineKeyboardButton("❓ Trivia", callback_data="trivia"),
        types.InlineKeyboardButton("🎲 Dice Roll", callback_data="dice"),
        types.InlineKeyboardButton("💬 Chat AI", callback_data="chat_ai"),
        types.InlineKeyboardButton("🔢 Number Guess", callback_data="guess"),
        types.InlineKeyboardButton("✊✌️✋ RPS", callback_data="rps"),
        types.InlineKeyboardButton("📖 Fact", callback_data="fact"),
        types.InlineKeyboardButton("🌡 Weather", callback_data="weather"),
        types.InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
    )
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    init_user(msg.from_user.id,msg.from_user.first_name)
    bot.send_message(msg.chat.id,f"Hi {msg.from_user.first_name}! 🤖💖\nSelect an option:",reply_markup=main_menu())

# ---------------------- CALLBACK ---------------------- #
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    chat_id=c.message.chat.id; uid=c.from_user.id
    if c.data=="joke": bot.send_message(chat_id,get_joke(),reply_markup=main_menu())
    elif c.data=="quote": bot.send_message(chat_id,get_quote(),reply_markup=main_menu())
    elif c.data=="fact": bot.send_message(chat_id,random_fact(),reply_markup=main_menu())
    elif c.data=="meme": url=get_meme(); bot.send_photo(chat_id,url,reply_markup=main_menu()) if url else bot.send_message(chat_id,"No meme 😢",reply_markup=main_menu())
    elif c.data=="anime": bot.send_message(chat_id,"Send anime name:"); bot.register_next_step_handler(c.message, anime_step)
    elif c.data=="chat_ai": bot.send_message(chat_id,"Talk to AI 💕:"); bot.register_next_step_handler(c.message, ai_step)
    elif c.data=="dice": dice_game(c)
    elif c.data=="trivia": start_trivia(c.message)
    elif c.data=="weather": bot.send_message(chat_id,"Send city name:"); bot.register_next_step_handler(c.message, weather_step)
    elif c.data=="leaderboard": show_leaderboard(chat_id)
    elif c.data=="guess": start_guess(c.message)
    elif c.data=="rps": start_rps(c.message)

# ---------------------- STEP HANDLERS ---------------------- #
def ai_step(msg): bot.send_message(msg.chat.id,ai_response(msg.from_user.id,msg.text),reply_markup=main_menu())
def anime_step(msg): bot.send_message(msg.chat.id,get_anime(msg.text),reply_markup=main_menu())
def weather_step(msg): bot.send_message(msg.chat.id,get_weather(msg.text),reply_markup=main_menu())

# ---------------------- TRIVIA ---------------------- #
TRIVIA=[{"q":"Capital of France?","a":"paris"},{"q":"2+2*2=?","a":"6"},{"q":"Who wrote Hamlet?","a":"shakespeare"}]

def start_trivia(msg):
    q=random.choice(TRIVIA)
    bot.send_message(msg.chat.id,"Trivia:\n"+q["q"])
    bot.register_next_step_handler(msg, check_trivia, q)

def check_trivia(msg,q):
    ans=msg.text.lower(); users=load_users(); uid=str(msg.from_user.id)
    if uid not in users: users[uid]={"trivia_score":0}
    if ans==q["a"]: users[uid]["trivia_score"]=users[uid].get("trivia_score",0)+1; bot.send_message(msg.chat.id,"✅ Correct!")
    else: bot.send_message(msg.chat.id,f"❌ Wrong! Answer: {q['a']}")
    save_users(users); bot.send_message(msg.chat.id,f"Trivia Score: {users[uid]['trivia_score']}",reply_markup=main_menu())

# ---------------------- DICE GAME ---------------------- #
def dice_game(call):
    chat_id=call.message.chat.id; uid=call.from_user.id
    roll=random.randint(1,6)
    users=load_users(); uid_s=str(uid)
    if uid_s not in users: users[uid_s]={"mini_game_score":0}
    if roll>=4: users[uid_s]["mini_game_score"]+=1; result=f"🎲 You rolled {roll} - Win! +1 score"
    else: result=f"🎲 You rolled {roll} - Try again!"
    save_users(users); bot.send_message(chat_id,result,reply_markup=main_menu())

# ---------------------- NUMBER GUESS ---------------------- #
def start_guess(msg):
    number=random.randint(1,10)
    bot.send_message(msg.chat.id,"I'm thinking of a number between 1-10. Try to guess it!")
    bot.register_next_step_handler(msg, check_guess, number)

def check_guess(msg,number):
    try: guess=int(msg.text)
    except: bot.send_message(msg.chat.id,"Please enter a number!",reply_markup=main_menu()); return
    uid=str(msg.from_user.id); users=load_users()
    if uid not in users: users[uid]={"mini_game_score":0}
    if guess==number: users[uid]["mini_game_score"]+=1; bot.send_message(msg.chat.id,"✅ Correct! +1 score")
    else: bot.send_message(msg.chat.id,f"❌ Wrong! I was thinking {number}")
    save_users(users); bot.send_message(msg.chat.id,f"Mini-game score: {users[uid]['mini_game_score']}",reply_markup=main_menu())

# ---------------------- ROCK PAPER SCISSORS ---------------------- #
def start_rps(msg):
    markup=types.InlineKeyboardMarkup(row_width=3)
    for move in ["Rock","Paper","Scissors"]:
        markup.add(types.InlineKeyboardButton(move,callback_data=f"rps_{move.lower()}"))
    bot.send_message(msg.chat.id,"Choose your move:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rps_"))
def rps_play(c):
    chat_id=c.message.chat.id; uid=str(c.from_user.id); users=load_users()
    if uid not in users: users[uid]={"mini_game_score":0}
    user_move=c.data.split("_")[1]; bot_move=random.choice(["rock","paper","scissors"])
    if user_move==bot_move: result="Draw!"
    elif (user_move=="rock" and bot_move=="scissors") or (user_move=="scissors" and bot_move=="paper") or (user_move=="paper" and bot_move=="rock"): result="You Win! +1 score"; users[uid]["mini_game_score"]+=1
    else: result=f"You Lose! Bot chose {bot_move}"
    save_users(users); bot.send_message(chat_id,result,reply_markup=main_menu())

# ---------------------- LEADERBOARD ---------------------- #
def show_leaderboard(chat_id):
    users=load_users()
    leaderboard=sorted([(u,d.get("trivia_score",0)+d.get("mini_game_score",0)) for u,d in users.items()], key=lambda x:-x[1])[:5]
    text="🏆 Leaderboard:\n"+ "\n".join([f"{i+1}. {users[u].get('name',u)}: {score}" for i,(u,score) in enumerate(leaderboard)])
    bot.send_message(chat_id,text,reply_markup=main_menu())

# ---------------------- DAILY REMINDERS ---------------------- #
def daily_reminders():
    while True:
        users=load_users()
        for uid,d in users.items():
            if d.get("daily_reminders",True):
                try:
                    bot.send_message(int(uid),"🕒 Joke:\n"+get_joke())
                    bot.send_message(int(uid),"📜 Quote:\n"+get_quote())
                    bot.send_message(int(uid),"📖 Fact:\n"+random_fact())
                except: pass
        time.sleep(86400)

# ---------------------- RUN ---------------------- #
if __name__=="__main__":
    threading.Thread(target=daily_reminders,daemon=True).start()
    bot.infinity_polling()
