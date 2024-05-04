import streamlit as st
import pandas as pd
import numpy as np
import requests
from random import randint

API_KEYS = ["AIzaSyACbEZiTObiLNepvMNWRslKKpK9vmlEiKM"]

data = {
    "V_id": [],
    "commentCount": [],
    "dislikeCount": [],
    "likeCount": [],
    "viewCount": [],
    "publishedAt": [],
    "channelId": [],
    "categoryId": [],
    "ChannelPublishedAt": [],
    "channel_videoCount": [],
    "channel_subscriberCount": [],
    "channel_ViewCount": []
}
channel_dict = {}


# The function returns the final URL for request
def get_url(Video_urls):
    v_id = ",".join(Video_urls)
    API_KEY = API_KEYS[0]
    url = "https://www.googleapis.com/youtube/v3/videos?part=status,snippet,topicDetails,contentDetails," \
          "statistics&id=" + v_id + "&key=" + API_KEY
    return url


# This function populates the data dictionary
def add_data(i, key1, key2, key3="NA"):
    try:
        if key3 != "NA":
            data[key1].append(i[key2][key3])
        else:
            data[key1].append(i[key2])
    except Exception as e:
        print("Error: ", e)
        if key1 in [
            'viewCount', 'commentCount', 'dislikeCount', 'publishedAt',
            'channel_videoCount', 'channel_subscriberCount'
        ]:
            print(i.get("id", "N/A"))
            print(key1 + " missing")
        data[key1].append(0)


# The function is used to get the Video relevant data
def video_data(get_json):
    for i in get_json["items"]:
        add_data(i, key1="commentCount", key2="statistics", key3="commentCount")
        add_data(i, key1="dislikeCount", key2="statistics", key3="dislikeCount")
        add_data(i, key1="V_id", key2='id')
        add_data(i, key1="categoryId", key2="snippet", key3="categoryId")
        add_data(i, key1="publishedAt", key2="snippet", key3="publishedAt")
        add_data(i, key1="likeCount", key2="statistics", key3="likeCount")
        add_data(i, key1="viewCount", key2="statistics", key3="viewCount")
        add_data(i, key1="channelId", key2="snippet", key3="channelId")


# It gets the channel relevant data
def channel_data():
    channel_id = ",".join(data["channelId"])
    API_KEY = API_KEYS[0]
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=" + channel_id + "&key=" + API_KEY
    r = requests.get(url)
    get_json = r.json()

    if len(set(data["channelId"])) == len(data["channelId"]):
        for i in get_json["items"]:
            add_data(i,
                     key1="ChannelPublishedAt",
                     key2="snippet",
                     key3="publishedAt")
            add_data(i,
                     key1="channel_ViewCount",
                     key2="statistics",
                     key3="viewCount")
            add_data(i,
                     key1="channel_subscriberCount",
                     key2="statistics",
                     key3="subscriberCount")
            add_data(i,
                     key1="channel_videoCount",
                     key2="statistics",
                     key3="videoCount")
    else:
        for i in get_json["items"]:
            channel_dict[i["id"]] = {}
            channel_dict[i["id"]]["ChannelPublishedAt"] = i["snippet"]["publishedAt"]
            channel_dict[i["id"]]["channel_ViewCount"] = i["statistics"]["viewCount"]
            channel_dict[i["id"]]["channel_subscriberCount"] = i["statistics"][
                "subscriberCount"]
            channel_dict[
                i["id"]]["channel_videoCount"] = i["statistics"]["videoCount"]

        for j in data["channelId"]:
            add_data(channel_dict,
                     key1="ChannelPublishedAt",
                     key2=j,
                     key3="ChannelPublishedAt")
            add_data(channel_dict,
                     key1="channel_ViewCount",
                     key2=j,
                     key3="channel_ViewCount")
            add_data(channel_dict,
                     key1="channel_subscriberCount",
                     key2=j,
                     key3="channel_subscriberCount")
            add_data(channel_dict,
                     key1="channel_videoCount",
                     key2=j,
                     key3="channel_videoCount")


def get_months(x):
    return 12 - x.month + 1 + (2016 - (x.year + 1) + 1) * 12


# The function gets the data after converting to derived features
def get_final_data(df):
    df["months_old"] = pd.to_datetime(
        df.publishedAt).apply(lambda x: get_months(x))
    df["channel_months_old"] = pd.to_datetime(
        df.ChannelPublishedAt).apply(lambda x: get_months(x))

    df["viewCount/channel_month_old"] = df.apply(
        lambda x: float(x["viewCount"]) / (x["channel_months_old"] + 1), axis=1)
    df["viewCount/video_month_old"] = df.apply(
        lambda x: float(x["viewCount"]) / float(x["months_old"] + 1), axis=1)

    df["subscriberCount/videoCount"] = df.apply(
        lambda x: (float(x["channel_subscriberCount"]) + 1) /
                  (float(x["channel_videoCount"]) + 1),
        axis=1)

    return df


def fetch_model():
    # This part needs to be replaced with your actual model fetching code
    Y_test = data["likeCount"]
    p = np.array(Y_test).astype("float32")
    p1 = p + randint(5, 20)

    org = np.array(Y_test).astype("float32")
    err = ((p1 - org) / org) * 100.0
    V_id = data["V_id"]
    diff = p1 - org

    try:
        out = pd.DataFrame({
            "V_ids": V_id,
            "Original": org,
            "Predicted": p1,
            "Difference(+/-)": diff,
            "Error Rate": err
        })
        return out
    except:
        return None


def main():
    st.title("YouTube Like Predictor")

    video_id = st.text_input("Enter YouTube Video ID :")

    if st.button("Predict"):
        V_id = video_id.split(',')
        url = get_url(V_id)
        r = requests.get(url)
        get_json = r.json()
        video_data(get_json)
        channel_data()
        df = pd.DataFrame(data)
        df = get_final_data(df)
        result = fetch_model()

        if result is not None:
            st.subheader("YouTube Video:")
            for video_id in V_id:
                video_url = f"https://www.youtube.com/embed/{video_id}"
                st.markdown(
                    f'<iframe width="700" height="315" src="{video_url}" frameborder="0" allowfullscreen></iframe>',
                    unsafe_allow_html=True)
            st.subheader(" ")
            st.subheader("YouTube Video Details :")

            # Format DataFrame to have only two columns: Youtube Parameter and Values
            df_formatted = pd.DataFrame({
                "YouTube Parameter": df.columns.tolist(),
                "Values": df.values.flatten()
            })

            # Print the formatted DataFrame
            st.dataframe(df_formatted)

            st.subheader("Like Prediction Result :")
            st.dataframe(result)


if __name__ == "__main__":
    main()






