import os
import requests
import csv
import pandas as pd


POSTS_ENDPOINT = "https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b"
COMMENTS_ENDPOINT = "https://www.instagram.com/graphql/query/?query_hash=33ba35852cb50da46f5b5e889df7d159"
SNEAKERNEWS_USER_ID = "16389033"
COMMENTS_HEADER = ["commentID", "comment", "createdTime", "userID", "userName"]
POSTS_HEADER = ["shortCode", "postCaption", "postLikes", "commentCount", "postTime"]


def make_post_requests(user_id, count, end_cursor=None):
    """
    Makes GET requests to instagram for posts

    :param user_id: str
    unique user_id for Instagram user
    :param count: int
    number of posts to retrieve
    :param end_cursor: str/None
    Used for pagenation
    :return: tuple
    """
    if end_cursor is None:
        params = {"id": user_id, "first": count}
    else:
        params = {"id": user_id, "first": count, "after": end_cursor}

    r = requests.get(POSTS_ENDPOINT, params=params)
    if r.status_code == 200:
        page_info = r.json()["data"]["user"]['edge_owner_to_timeline_media']["page_info"]
        posts = r.json()["data"]["user"]['edge_owner_to_timeline_media']["edges"]
        return page_info, posts
    else:
        return None


def get_post_meta_data(post):
    """
    Retrieve a list of meta_data of a post
    :param post: dict
    The post in json format
    :return: list

    """
    shortCode = post["node"]["shortcode"]
    postLikes = post["node"]['edge_media_preview_like']["count"]
    commentCount = post["node"]['edge_media_to_comment']["count"]
    postTime = post["node"]['taken_at_timestamp']
    postCaption = post["node"]['edge_media_to_caption']['edges'][0]['node']['text']

    return [shortCode, postCaption, postLikes, commentCount, postTime]


def get_comment_meta_data(comment_data):
    """
    Return list of comment meta data
    :param comment_data: dict
    :return: list
    """
    comment = comment_data["node"]["text"]
    created_time = comment_data["node"]["created_at"]
    user_id = comment_data["node"]['owner']['id']
    username = comment_data['node']['owner']['username']
    comment_id = comment_data['node']['id']

    return [comment_id, comment, created_time, user_id, username]


def make_comments_requests(shortcode, count, end_cursor=None):
    """
    Make GET request for comments given "shortcode" of a post

    :param shortcode:str
    :param count:int
    :param end_cursor:str
    :return: tuple
    """
    if end_cursor is None:
        params = {"shortcode": shortcode, "first": count}
    else:
        params = {"shortcode": shortcode, "first": count, "after": end_cursor}

    r = requests.get(COMMENTS_ENDPOINT, params=params)
    if r.status_code == 200:
        comments = r.json()["data"]["shortcode_media"]["edge_media_to_comment"]["edges"]
        page_info = r.json()["data"]["shortcode_media"]["edge_media_to_comment"]["page_info"]
        return page_info, comments
    else:
        return None


def get_user_id(username):
    """
    Find unique user_id from instagram user name
    :param username: str
    :return: str
    """
    r = requests.get(f"https://www.instagram.com/{username}/?__a=1")
    user_id = r.json()['graphql']['user']['id']
    return user_id


def is_private(username):
    """
    Check if user is private
    :param username:
    :return: bool
    """
    r = requests.get(f"https://www.instagram.com/{username}/?__a=1")
    private_status = r.json()['graphql']['user']['is_private']
    return private_status


def get_all_posts(username):
    """
    Get all posts from a user and save data into csv file
    :param username: str
    Unique user id for instagram account
    location for csv file to write posts to
    """
    if not os.path.exists('posts'):
        os.mkdir('posts')
    out_file = f"posts/{username}_posts.csv"
    user_id = get_user_id(username)
    if is_private(username):
        print("User is Private, cannot get posts")
        return None
    else:
        get_all(user_id, POSTS_HEADER, make_post_requests, get_post_meta_data, out_file)


def get_all_comments(short_code):
    """
    Get all comments given post short code
    :param short_code: str
    :return:
    """
    if not os.path.exists('comments'):
        os.mkdir('comments')
    out_file = f"comments/{short_code}.csv"
    get_all(short_code, COMMENTS_HEADER, make_comments_requests, get_comment_meta_data, out_file)


def get_posts_by_count(user_id, count, end_cursor=None):
    """
    Get only a certain number of posts and return pandas dataframe
    :param user_id: str
    Unique user id for instagram user
    :param count: int
    number of posts to retrieve
    :param end_cursor: str
    Used for pagenation
    :return: dataframe
    """

    posts_list = []
    while True:
        requestAmount = min(50, count)
        results = make_post_requests(user_id, requestAmount, end_cursor)
        if results is not None:
            page_info, posts = results
            next_page = page_info["has_next_page"]
            end_cursor = page_info["end_cursor"]
            for post in posts:
                try:
                    data = get_post_meta_data(post)
                    posts_list.append(data)
                except IndexError:
                    continue
            count -= requestAmount
            if (not next_page) or (count == 0):
                break
    df = pd.DataFrame(posts, columns=POSTS_HEADER)
    return df


def get_all(unique_id, header, make_requests, get_meta_data, out_file, ):
    """
    Save all comments or posts into csv file
    :param unique_id: str
    :param header: list
    :param make_requests: func
    :param get_meta_data: func
    :param out_file: str
    :return:
    """
    with open(out_file, 'w', encoding="utf-8") as file_out:
        csv_writer = csv.writer(file_out)
        csv_writer.writerow(header)
        end_cursor = None
        while True:
            results = make_requests(unique_id, 50, end_cursor)
            if results is not None:
                page_info, data_list = results
                next_page = page_info["has_next_page"]
                end_cursor = page_info["end_cursor"]

                for data in data_list:
                    try:
                        data = get_meta_data(data)
                        csv_writer.writerow(data)
                    except IndexError:
                        continue
                if not next_page:
                    break
        file_out.close()
