import re

def handler(user_text):
    user_text = re.sub(r' ', '+', user_text)
    user_text = 'https://www.wildberries.by/catalog/0/search.aspx?page=1&sort=popular&search=' + user_text
    return user_text