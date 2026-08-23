import datetime
import os
import subprocess
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import AudioFileClip, VideoFileClip
import requests
import streamlit as st

# yt-dlp ကို နောက်ဆုံးရဗားရှင်းသို့ အလိုအလျောက် Update တင်ရန်
subprocess.run(["pip", "install", "--upgrade", "yt-dlp"])
import yt_dlp

st.set_page_config(
    page_title="AI Video Auto Dubbing Studio", page_icon="🎬", layout="wide"
)
st.title("🎬 AI Video Dubbing & Myanmar Voiceover Studio")

# Admin နှင့် VIP စနစ်များ
ADMIN_KEYS = ["ADMIN123", "JEWAN_MASTER"]
VIP_KEYS_DATABASE = {"VIP-202608-0001": "2026-08-31"}

if "purchased_keys" not in st.session_state:
  st.session_state.purchased_keys = {}
if "today" not in st.session_state:
  st.session_state.today = datetime.date.today()
if (
    "usage_count" not in st.session_state
    or st.session_state.today != datetime.date.today()
):
  st.session_state.today = datetime.date.today()
  st.session_state.usage_count = 0

ALL_VIP_KEYS = {**VIP_KEYS_DATABASE, **st.session_state.purchased_keys}

# Sidebar (VIP / Admin Panel & Voice Settings)
st.sidebar.title("👑 VIP / Admin Panel")
st.sidebar.markdown("### 💰 VIP ဈေးနှုန်းများ")
st.sidebar.markdown("""
* **၁ လ (30 Days):** 35,000 MMK / 300 THB
* **၃ လ (90 Days):** 75,000 MMK / 600 THB
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎙️ အသံအမျိုးအစား ရွေးချယ်ရန်")
voice_gender = st.sidebar.selectbox(
    "AI အသံ ပုံစံရွေးပါ:",
    [
        "မြန်မာအသံ - ပုံမှန်အမြန်နှုန်း (Standard)",
        "မြန်မာအသံ - အနှေးပုံစံ (Slow Narration)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💳 VIP Key ဝယ်ယူရန်")
col1, col2 = st.sidebar.columns(2)
with col1:
  if os.path.exists("kpay.png"):
    st.image("kpay.png", caption="KBZPay")
  else:
    st.info("📱 KBZPay QR")
with col2:
  if os.path.exists("promptpay.png"):
    st.image("promptpay.png", caption="PromptPay")
  else:
    st.info("📱 PromptPay QR")

st.sidebar.info("📌 ငွေလွှဲပြီးပါက ပြေစာကို Telegram သို့ ပို့ပေးပါ။")
st.sidebar.link_button(
    "✈️ Telegram သို့ ဆက်သွယ်ရန်", "https://t.me/Han_Oo_Hlaing"
)
st.sidebar.markdown("---")

user_key = st.sidebar.text_input(
    "🔑 VIP Key (သို့) Admin Key ထည့်ပါ:", type="password"
)
is_admin, is_vip = False, False

if user_key:
  if user_key in ADMIN_KEYS:
    is_admin = True
    st.sidebar.success("⚡ Admin Mode အဖြစ် ဝင်ရောက်ထားပါသည်။")
  elif user_key in ALL_VIP_KEYS:
    expire_date_str = ALL_VIP_KEYS[user_key]
    expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d").date()
    if datetime.date.today() <= expire_date:
      is_vip = True
      st.sidebar.success(f"👑 VIP သက်တမ်းရှိသည် (ကုန်ရက်: {expire_date_str})")
    else:
      st.sidebar.error("❌ သင်၏ VIP Key မှာ သက်တမ်းကုန်သွားပါပြီ။")
  else:
    st.sidebar.error("❌ VIP Key မှားယွင်းနေပါသည်။")

if is_admin:
  st.sidebar.markdown("---")
  st.sidebar.markdown("### 🛠 Admin: VIP Key အသစ်ထုတ်ရန်")
  new_key = st.sidebar.text_input("VIP Key အသစ် နာမည်ပေးပါ:")
  exp_days = st.sidebar.number_input(
      "သက်တမ်း (ရက်ပေါင်း):", min_value=1, value=30
  )
  if st.sidebar.button("Key အသစ်ဆောက်မည်"):
    if new_key:
      new_exp_date = (
          datetime.date.today() + datetime.timedelta(days=exp_days)
      ).strftime("%Y-%m-%d")
      st.session_state.purchased_keys[new_key] = new_exp_date
      st.sidebar.success(f"Key: {new_key}\nExpiry: {new_exp_date}")

# Main UI
st.subheader("🔗 Video Link ထည့်ပါ (TikTok, YouTube, Facebook, etc.)")
video_url = st.text_input(
    "URL Input", placeholder="https://www.tiktok.com/@... သို့မဟုတ် YouTube လင့်ခ်"
)

api_key = st.text_input(
    "Google AI Studio API Key ထည့်ပါ:", type="password"
)
st.markdown(
    "🔑 API Key မရှိသေးပါက [ဒီနေရာကိုနှိပ်၍"
    " အခမဲ့ယူပါ](https://aistudio.google.com/app/apikey)"
)

if not (is_admin or is_vip):
  st.warning(
      f"⚠️ အခမဲ့ အသုံးပြုသူများအတွက် ၁ ရက်လျှင် ၂ ကြိမ်သာ"
      f" အသုံးပြုနိုင်ပါသည်။ (ယနေ့ သုံးပြီးစီးမှု: {st.session_state.usage_count}/2)"
      f" \n\n✨ **၁ လလုံး အကန့်အသတ်မရှိ အသုံးပြုရန် VIP ဝယ်ယူပါ။**"
  )

if st.button("🚀 Process & Generate Dubbed Video"):
  if not (is_admin or is_vip) and st.session_state.usage_count >= 2:
    st.error(
        "❌ ယနေ့အတွက် အခမဲ့သုံးစွဲခွင့် ပြည့်သွားပါပြီ။ VIP Key ဝယ်ယူပါ။"
    )
  elif not video_url:
    st.error("ကျေးဇူးပြု၍ Video Link ထည့်သွင်းပေးပါ။")
  elif not (is_admin or is_vip) and not api_key:
    st.error("ကျေးဇူးပြု၍ API Key ထည့်သွင်းပေးပါ။")
  else:
    try:
      if api_key:
        genai.configure(api_key=api_key)

      model = genai.GenerativeModel("gemini-3.6-flash")

      st.info("📥 ၁။ ဗီဒီယိုကို ဒေါင်းလုဒ်လုပ်နေပါသည်...")
      input_file = "input_video.mp4"
      output_file = "final_dubbed_video.mp4"

      ydl_opts = {
          "format": "mp4/best",
          "outtmpl": input_file,
          "quiet": True,
          "no_warnings": True,
          "http_headers": {
              "User-Agent": (
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
              )
          },
      }

      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        title = info.get("title", "Video")
        description = info.get("description", "")

      st.success("✅ ဗီဒီယို ဒေါင်းလုဒ်ပြီးပါပြီ။")

      st.info("🤖 ၂။ AI ဖြင့် ဇာတ်လမ်းကို တိုတိုနှင့်တိကျစွာ မြန်မာလို ဘာသာပြန်ဆိုနေပါသည်...")
      prompt = (
          "Summarize and translate the core storyline into a concise, natural"
          " Myanmar voiceover script (strictly short sentences matching the"
          " video flow, no extra unnecessary fluff):\nTitle:"
          f" {title}\nDescription: {description}"
      )
      response = model.generate_content(prompt)
      myanmar_script = response.text.replace("*", "").strip()

      st.subheader("📝 ထွက်လာသော မြန်မာဇာတ်ညွှန်း Script:")
      st.info(myanmar_script)

      st.info("🗣️ ၃။ မြန်မာ AI အသံထုတ်ယူ၍ မူရင်းအသံဖျောက်ကာ ပေါင်းစပ်နေပါသည်...")
      audio_file = "myanmar_audio.mp3"

      # အသံနှုန်း ရွေးချယ်မှု
      is_slow = True if "အနှေး" in voice_gender else False
      tts = gTTS(text=myanmar_script, lang="my", slow=is_slow)
      tts.save(audio_file)

      # MoviePy ဖြင့် မူရင်းအသံဖြုတ်ပြီး မြန်မာအသံအသစ်ထည့်ခြင်း
      video_clip = VideoFileClip(input_file)
      audio_clip = AudioFileClip(audio_file)

      # အသံနှင့် ဗီဒီယို အရှည်ညီညာစေရန် ပေါင်းစပ်ခြင်း
      final_clip = video_clip.set_audio(audio_clip)
      final_clip.write_videofile(
          output_file,
          codec="libx264",
          audio_codec="aac",
          temp_audiofile="temp-audio.m4a",
          remove_temp=True,
          logger=None,
      )

      st.success("✅ မြန်မာအသံသီးသန့်ပါဝင်သော ဗီဒီယို အောင်မြင်စွာ ပြီးစီးပါပြီ။")

      st.subheader("📺 ရလဒ် ဗီဒီယို (မူရင်းအသံပျောက်ပြီး မြန်မာအသံပါဝင်သည်):")
      if os.path.exists(output_file):
        st.video(output_file)
        with open(output_file, "rb") as f:
          st.download_button(
              label="📥 မြန်မာအသံပါ ဗီဒီယိုကို သိမ်းဆည်းရန် (Download MP4)",
              data=f,
              file_name="Myanmar_Dubbed_Video.mp4",
              mime="video/mp4",
          )

      if not (is_admin or is_vip):
        st.session_state.usage_count += 1

    except Exception as e:
      st.error(
          f"အမှားအယွင်း ရှိပါသည်။ လင့်ခ်မှန်ကန်မှု ရှိမရှိ ထပ်စစ်ဆေးပေးပါ။"
          f" Error: {str(e)}"
      )
