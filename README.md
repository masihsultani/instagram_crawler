# Instagram Crawler

A module to crawl user posts and comments of posts. Gives back a csv file of posts with the caption, no photos returned. To retrieve all posts of a user simply do
```
username = "example_user_name"
get_all_posts(username)
```
To retrieve comments for a post, you need the "short_code" of the post. This will be found when you call get_all_posts().
```
short_code ="example_short_code"
get_all_comments(short_code)
```
