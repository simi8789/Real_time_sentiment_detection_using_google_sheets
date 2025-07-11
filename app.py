import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from textblob import TextBlob
import time
from streamlit_autorefresh import st_autorefresh
from wordcloud import WordCloud
from wordcloud import STOPWORDS
import matplotlib.pyplot as plt
from datetime import datetime
import emoji
import altair as alt



st.set_page_config(page_title="Real-Time Sentiment Dashboard", layout="wide")
st_autorefresh(interval=10*1000,key="refresh")

# Google Sheets API setup
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
    client = gspread.authorize(creds)


# Sheet connection
    SHEET_NAME = "https://docs.google.com/spreadsheets/d/1hUJeI0ZGc2g4MSAfhlG6BVwft5_2K3Ohi3w0fXR8fNQ/edit?resourcekey=&gid=1353412904#gid=1353412904"  # Your actual sheet name
    sheet = client.open_by_url(SHEET_NAME).sheet1
    data=sheet.get_all_records()
    df=pd.DataFrame(data)
    return df



# ---- SENTIMENT ANALYSIS ----
def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positive", polarity
    elif polarity < -0.1:
        return "Negative", polarity
    else:
        return "Neutral", polarity

# ---- MAIN DASHBOARD ----
st.title("📊 Real-Time Sentiment Detection from Google Feedback")

df = load_data()
df.columns=[str(col).strip() for col in df.columns]
st.write("columns from sheet:",df.columns.tolist())


if "Reviews" not in df.columns:
    st.error("🛑 No 'Reviews' column found in the sheet!")
else:
    df["Reviews"] = df["Reviews"].astype(str)
    df[["Sentiment  Detection", "Polarity"]] = df["Reviews"].apply(lambda x: pd.Series(analyze_sentiment(x)))

# --- Display Latest Data ---
st.subheader("📝 Latest Feedback")
st.dataframe(df[["Timestamp", "Reviews", "Polarity", "Sentiment  Detection"]].sort_values(by="Timestamp", ascending=False), height=300)

# --- Emoji Summary ---
st.subheader("😊 Emoji-Based Sentiment Summary")
emoji_map = {"Positive": "😃", "Negative": "😠", "Neutral": "😐"}
counts = df["Sentiment  Detection"].value_counts()
st.write(" | ".join(f"{emoji_map.get(k, '')} {k}: {v}" for k, v in counts.items()))

 # --- Word Cloud ---
st.subheader("☁️ Word Cloud of Reviews")
text = " ".join(df["Reviews"])
custom_stopwords=set(STOPWORDS)
custom_stopwords.update(["app","okay","nothing"])
wordcloud = WordCloud(width=800, height=400, background_color='white',stopwords=custom_stopwords,colormap='Set2').generate(text)
fig, ax = plt.subplots()
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis("off")
st.pyplot(fig)

# --- Sentiment Distribution Pie ---
st.subheader("📊 Sentiment Distribution")
fig2, ax2 = plt.subplots()
ax2.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90)
ax2.axis("equal")
st.pyplot(fig2)

 # --- Sentiment Trend Over Time ---
if "Timestamp" in df.columns:
     st.subheader("📈 Sentiment Trend Over Time")
     df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')
     trend_data = df.groupby([df["Timestamp"].dt.date, "Sentiment  Detection"]).size().unstack(fill_value=0)
     chart=alt.Chart(trend_data).mark_line(point=True).encode(x="Timestamp:T",y="Count:Q",color=alt.Color("Sentiment  Detection:N",scale=alt.Scale(domain=["Positive","Neutral","Negative"],range=["red","gray","blue"])),tooltip=["Timestamp:T","Sentiment  Detection:N","Count:Q"]).properties(width=700,height=400)
     st.altair_chart(chart,use_container_width=True)








