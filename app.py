import datetime
import streamlit as st
import google.generativeai as genai
import yt_dlp
import os

st.set_page_config(page_title="AI Movie Recap Generator", page_icon="🎬", layout="wide")
st.title("🎬 AI Movie Recap Generator")

ADMIN_KEYS = ["ADMIN123", "JEWAN_MASTER"]
VIP_KEYS_DATABASE = {"VIP-202608-0001": "2026-08-31"}

if "purchased_keys" not in st.session_state:
    st.session_state.purchased_keys = {}
if "today" not in st.session_state:
    st.session_state.today = datetime.date.today()
if "usage_count" not in st.session_state or st.session_state.today != datetime.date.today():
    st.session_state.today = datetime.date.today()
    st.session_state.usage_count = 0

ALL_VIP_KEYS = {**VIP_KEYS_DATABASE, **st.session_state.purchased_keys}

st.sidebar.title("👑 VIP / Admin Panel")
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
st.sidebar.link_button("✈️ Telegram သို့ ဆက်သွယ်ရန်", "https://t.me/Han_Oo_Hlaing")
st.sidebar.markdown("---")

user_key = st.sidebar.text_input("🔑 VIP Key (သို့) Admin Key ထည့်ပါ:", type="password")

is_admin = False
is_vip = False

if user_key:
    if user_key in ADMIN_KEYS:
        is_admin = True
        st.sidebar.success("⚡ Admin Mode အဖြစ် ဝင်ရောက်ထားပါသည်။")
    elif user_key in ALL_VIP_KEYS:
        expire_date_str = ALL_VIP_KEYS[user_key]
        expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d").date()
        if datetime.date.today() <= expire_date:
            is_vip = True
            st.sidebar.success(f"👑 VIP အဖြစ် အသုံးပြုနိုင်ပါသည်။ (သက်တမ်းကုန်ရက်: {expire_date_str})")
        else:
            st.sidebar.error("❌ သင်၏ VIP Key မှာ သက်တမ်းကုန်သွားပါပြီ။")
    else:
        st.sidebar.error("❌ VIP Key / Admin Key မှားယွင်းနေပါသည်။")

if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠 Admin: VIP Key အသစ်ထုတ်ရန်")
    new_key = st.sidebar.text_input("VIP Key အသစ် နာမည်ပေးပါ:")
    exp_days = st.sidebar.number_input("သက်တမ်း (ရက်ပေါင်း):", min_value=1, value=30)
    if st.sidebar.button("Key အသစ်ဆောက်မည်"):
        if new_key:
            new_exp_date = (datetime.date.today() + datetime.timedelta(days=exp_days)).strftime("%Y-%m-%d")
            st.session_state.purchased_keys[new_key] = new_exp_date
            st.sidebar.success(f"Key: {new_key}\nExpiry: {new_exp_date}")

st.subheader("Video Link (TikTok / YouTube / Facebook / Rednote / Douyin) ထည့်ပါ:")
video_url = st.text_input("URL Input", placeholder="https://vt.tiktok.com/...")
api_key = st.text_input("Google AI Studio API Key ထည့်ပါ (VIP/Admin မဟုတ်ပါက လိုအပ်ပါသည်):", type="password")

if not (is_admin or is_vip):
    st.warning(f"⚠️ အခမဲ့ အသုံးပြုသူများအတွက် ၁ ရက်လျှင် ၂ ကြိမ်သာ အသုံးပြုနိုင်ပါသည်။ (ယနေ့ သုံးပြီးစီးမှု: {st.session_state.usage_count}/2)")

if st.button("Generate Recap"):
    if not (is_admin or is_vip) and st.session_state.usage_count >= 2:
        st.error("❌ ယနေ့အတွက် အခမဲ့သုံးစွဲခွင့် (၂ ကြိမ်) ပြည့်သွားပါပြီ။ ဆက်လက်သုံးစွဲလိုပါက VIP Key ဝယ်ယူပါခင်ဗျာ။")
    elif not video_url:
        st.error("ကျေးဇူးပြု၍ Video Link ထည့်သွင်းပေးပါ။")
    elif not (is_admin or is_vip) and not api_key:
        st.error("ကျေးဇူးပြု၍ API Key ထည့်သွင်းပေးပါ။")
    else:
        try:
            if api_key:
                genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            
            st.info("Video အချက်အလက်များ ရယူနေပါသည်...")
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.tiktok.com/'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Video')
                description = info.get('description', '')
                
            st.success(f"Video တွေ့ရှိပါသည်: {title}")
            st.info("AI Recap ရေးသားနေပါသည်...")
            prompt = f"Please write a comprehensive and engaging movie/video recap based on the following title and description in Myanmar language:\nTitle: {title}\nDescription: {description}"
            response = model.generate_content(prompt)
            st.subheader("📝 Movie Recap Result:")
            st.write(response.text)
            
            if not (is_admin or is_vip):
                st.session_state.usage_count += 1
        except Exception as e:
            st.error(f"အမှားအယွင်း ရှိပါသည်။ Error: {str(e)}")
