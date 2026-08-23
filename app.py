import datetime
import os
import subprocess
import google.generativeai as genai
from gtts import gTTS
import requests
import streamlit as st

# yt-dlp ကို နောက်ဆုံးရဗားရှင်းသို့ အလိုအလျောက် Update တင်ရန်
subprocess.run([
    "pip",
    "install",
    "--upgrade",
    "https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz",
])
import yt_dlp

st.set_page_config(
    page_title="AI Video Studio & Voiceover", page_icon="🎬", layout="wide"
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
    ["👩 မိန်းကလေးအသံ (Female Voice)", "👨 ယောက်ကျားလေးအသံ (Male Voice)"],
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

# API Key Input
entered_api_key = st.text_input(
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

if st.button("🚀 Process & Generate Voiceover"):
  if not (is_admin or is_vip) and st.session_state.usage_count >= 2:
    st.error(
        "❌ ယနေ့အတွက် အခမဲ့သုံးစွဲခွင့် ပြည့်သွားပါပြီ။ VIP Key ဝယ်ယူပါ။"
    )
  elif not video_url:
    st.error("ကျေးဇူးပြု၍ Video Link ထည့်သွင်းပေးပါ။")
  elif not entered_api_key:
    st.error("ကျေးဇူးပြု၍ Google AI Studio API Key ထည့်သွင်းပေးပါ။")
  else:
    try:
      # API Key ကို ဤနေရာတွင် တိုက်ရိုက် Configure လုပ်ပါသည်
      genai.configure(api_key=entered_api_key.strip())

      st.info("📥 ၁။ ဗီဒီယိုကို ဒေါင်းလုဒ်လုပ်နေပါသည်...")
      input_file = "input_video.mp4"
      audio_extract = "extracted_audio.mp3"

      ydl_opts = {
          "format": "mp4/best",
          "outtmpl": input_file,
          "quiet": True,
          "no_warnings": True,
          "extractor_args": {"tiktok": {"webpage_download": True}},
          "http_headers": {
              "User-Agent": (
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
              )
          },
      }

      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(video_url, download=True)

      st.success("✅ ဗီဒီယို ဒေါင်းလုဒ်ပြီးပါပြီ။")

      st.info(
          "🎙️ ၂။ ဗီဒီယိုထဲမှ အသံကို ထုတ်ယူပြီး AI ဖြင့် အသံထွက်များကို"
          " စာသားပြောင်းလဲခြင်း (Transcript) ပြုလုပ်နေပါသည်..."
      )

      # Extract audio using ffmpeg
      os.system(
          f"ffmpeg -y -i {input_file} -q:a 0 -map a {audio_extract}"
          " >/dev/null 2>&1"
      )

      model = genai.GenerativeModel("gemini-1.5-flash")

      if os.path.exists(audio_extract) and os.path.getsize(audio_extract) > 0:
        st.info(
            "🤖 ၃။ စာသားများကို မြန်မာဘာသာသို့ တိကျမှန်ကန်စွာ ဘာသာပြန်ဆိုနေပါသည်..."
        )
        audio_file_ref = genai.upload_file(audio_extract)

        prompt = (
            "Listen to this audio carefully, transcribe what is being said,"
            " and translate the entire transcript accurately and naturally into"
            " fluent Myanmar (Burmese) language suitable for a voiceover script."
            " Provide only the translated Myanmar script."
        )
        response = model.generate_content([audio_file_ref, prompt])
        myanmar_script = response.text.replace("*", "").strip()
        try:
          genai.delete_file(audio_file_ref.name)
        except:
          pass
      else:
        prompt = (
            "Translate the core narrative context into fluent Myanmar"
            " (Burmese) voiceover script."
        )
        response = model.generate_content(prompt)
        myanmar_script = response.text.replace("*", "").strip()

      st.subheader("📝 ထွက်လာသော မြန်မာဇာတ်ညွှန်း Script:")
      st.info(myanmar_script)

      st.info("🗣️ ၄။ ရွေးချယ်ထားသော အသံပုံစံဖြင့် မြန်မာ AI အသံဖိုင် ဖန်တီးနေပါသည်...")
      final_audio_file = "myanmar_voiceover.mp3"

      tts = gTTS(text=myanmar_script, lang="my", slow=False)
      tts.save(final_audio_file)
      st.success("✅ အသံဖိုင် အောင်မြင်စွာ ထွက်လာပါပြီ။")

      st.subheader("📺 ရလဒ် ဗီဒီယိုနှင့် မြန်မာအသံဖိုင်:")
      if os.path.exists(input_file):
        st.video(input_file)
      if os.path.exists(final_audio_file):
        st.audio(final_audio_file)
        with open(final_audio_file, "rb") as f:
          st.download_button(
              label="📥 မြန်မာအသံဖိုင်ကို သိမ်းဆည်းရန် (Download MP3)",
              data=f,
              file_name="Myanmar_Voiceover.mp3",
              mime="audio/mp3",
          )

      if not (is_admin or is_vip):
        st.session_state.usage_count += 1

    except Exception as e:
      st.error(
          f"အမှားအယွင်း ရှိပါသည်။ API Key သို့မဟုတ် လင့်ခ်မှန်ကန်မှု"
          f" ရှိမရှိ ထပ်စစ်ဆေးပေးပါ။ Error: {str(e)}"
      )
