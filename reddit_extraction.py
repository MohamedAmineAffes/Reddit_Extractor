import streamlit as st
import praw
import pandas as pd
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import base64

def Parse_Reddit(subReddit,cl_id,cl_sec):
    # Initialize Reddit instance
    reddit = praw.Reddit(client_id=cl_id,
                        client_secret=cl_sec,
                        user_agent=True)  # User agent can be any string describing your app
    # Specify the subreddit you want to parse
    subreddit = reddit.subreddit(subReddit)
    # Fetch top posts from the subreddit
    top_posts = subreddit.top(limit=5)  # Fetching top 5 posts
    # Iterate over the top posts and print titles
    titles=[]     
    titles=[]
    all_comments=[]
    # Loop through the top posts
    for post in top_posts:
        titles.append(post.title)
        # Replace more comments
        post.comments.replace_more(limit=0)
        # Fetch and print top 5 comments
        comments=[]
        for comment in post.comments.list()[:5]:
            comments.append(comment.body)
        all_comments.append(comments)
        
    data={
        'title': titles,
        'comments': all_comments
    }
    df = pd.DataFrame(data)
    return df

# Authenticate the client
def authenticate_client(key,endpoint):
    ta_credential = AzureKeyCredential(key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
    return text_analytics_client

# Concatenate title and comment columns, handling lists in the comments
def concatenate_text(row):
    title = row['title']
    comments = ast.literal_eval(row['comment']) if isinstance(row['comments'], str) else row['comments']
    combined_text = title + ' ' + ' '.join(comments)
    return combined_text

def detect_language(df,key,endpoint):
    df['combined_text'] = df.apply(concatenate_text, axis=1)
    # Concatenate all values in the 'combined_text' column into a single string
    documents = ' '.join(df['combined_text'].dropna().astype(str))
    # Put the string into a list
    documents = [documents]
    # Detect languages
    client = authenticate_client(key,endpoint) 
    languages = client.detect_language(documents=documents)[0]
    return languages.primary_language.name, languages.primary_language.confidence_score 


# Streamlit app
st.title("Enter Reddit Credentials:")
#Input for Reddit account
client_identifier = st.text_input("Enter your client ID")
client_secret = st.text_input("Enter your Client Secure")

st.title("Enter the Azure Service credentials:")
#Input for Azure service
endpoint = st.text_input("Enter your azure endpoint")
key = st.text_input("Enter your azure key")

st.title("Enter the Subreddit to parse:")
# Input for subreddit
subreddit_input = st.text_input("Enter a subreddit:")

if subreddit_input:
    # Fetch data from Reddit
    df = Parse_Reddit(subreddit_input,client_identifier,client_secret)

    lang,score= detect_language(df,key,endpoint)
    # Display the language and confidence score
    st.write("Language:")
    st.write(lang)
    
    st.write("Confidence Score:")
    st.write(score)
    # Display the dataset
    st.write("Dataset:")
    st.write(df)

    # Provide a button to download the dataset
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="reddit_comments.csv">Download CSV file</a>'
    st.markdown(href, unsafe_allow_html=True)
    