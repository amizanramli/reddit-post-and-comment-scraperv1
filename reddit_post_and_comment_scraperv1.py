import streamlit as st
import praw
import pandas as pd
import time

# Reddit API Credentials
REDDIT_CLIENT_ID = "fX_9j6sKjm-wKW_CGN3BKQ"
REDDIT_CLIENT_SECRET = "HIF_Mlm1ET3fqaswKN21Iy4kvXq9Wg"
REDDIT_USER_AGENT = "MyCrawlerBot/1.0 (by u/Ok_Inspector98)"

# Max Token Limit
MAX_TOKENS = 10  

# Initialize Reddit API
def initialize_reddit():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

# Session state for authentication & tokens
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "tokens_used" not in st.session_state:
    st.session_state.tokens_used = 0

# Login Page
st.title("🔑 Login to Reddit Scraper")

if not st.session_state.authenticated:
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", type="password", key="password")
    login_button = st.button("Login")

    if login_button:
        if username == "alphatesting002" and password == "redditbot002":
            st.session_state.authenticated = True
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials. Try again.")

# Logout Button
if st.session_state.authenticated:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()

# Reddit Scraper UI
if st.session_state.authenticated:
    st.title("🔎 Reddit Post Search Scraper")

    # Display Remaining Tokens
    remaining_tokens = MAX_TOKENS - st.session_state.tokens_used
    st.info(f"💰 Remaining Tokens: **{remaining_tokens}/{MAX_TOKENS}**")

    reddit = initialize_reddit()  

    # Stop Fetching State
    if "stop_fetching" not in st.session_state:
        st.session_state.stop_fetching = False

    def fetch_posts(subreddit_name, query, limit, comment_limit):
        """Fetch posts and top comments from a subreddit."""
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.search(query, limit=limit)
        post_data = []

        progress_bar = st.progress(0)

        for count, post in enumerate(posts, 1):
            if st.session_state.stop_fetching:
                st.warning("⚠️ Fetching stopped by user.")
                break  

            try:
                post.comments.replace_more(limit=2)
                comments = [c.body for c in post.comments.list()[:comment_limit] if hasattr(c, "body")]

                post_data.append({
                    "title": post.title,
                    "upvotes": post.score,
                    "num_comments": post.num_comments,
                    "comments": comments
                })

                progress_bar.progress(count / limit)
                time.sleep(1)  # Avoid rate limits

            except Exception as e:
                st.warning(f"⚠️ Error processing post: {post.title} | {e}")

        progress_bar.empty()
        if not st.session_state.stop_fetching:
            st.success("✅ Fetching complete!")

        return post_data

    def rank_posts(post_data):
        """Rank posts based on upvotes and comments."""
        for post in post_data:
            post["score"] = post["upvotes"] * 2 + post["num_comments"]

        return sorted(post_data, key=lambda x: x["score"], reverse=True)

    # User Inputs
    subreddit_input = st.text_input("Enter subreddit name", "Bolehland")
    query_input = st.text_input("Enter search query", "muslim")
    post_limit = st.number_input("Number of posts to pull", min_value=1, max_value=100, value=10)
    comment_limit = st.number_input("Number of comments per post", min_value=1, max_value=20, value=5)

    # Buttons
    col1, col2 = st.columns(2)
    with col1:
        fetch_button = st.button("Pull Posts")
    with col2:
        stop_button = st.button("Stop Pulling")

    if stop_button:
        st.session_state.stop_fetching = True
        st.warning("⚠️ Stopping pull...")

    if fetch_button:
        # Check Token Usage
        if st.session_state.tokens_used >= MAX_TOKENS:
            st.error("❌ Maximum token limit reached! Please wait for a new session.")
        else:
            st.session_state.stop_fetching = False
            st.info(f"🔄 Fetching {post_limit} posts from r/{subreddit_input} for '{query_input}'...")

            posts = fetch_posts(subreddit_input, query_input, post_limit, comment_limit)

            if posts:
                ranked_posts = rank_posts(posts)
                df = pd.DataFrame(ranked_posts)

                # Display DataFrame
                st.dataframe(df)

                # Deduct Token
                st.session_state.tokens_used += 1
                st.success(f"✅ Fetch successful! Tokens remaining: **{MAX_TOKENS - st.session_state.tokens_used}**")
            else:
                st.error("❌ No posts found. Try again later.")
