import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

import json

BASE_URL = "https://ust.space"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": USER_AGENT
}

login_details = dotenv_values(".env")

if login_details["username"] is None or login_details["password"] is None:
    print("Please provide username and password in .env file!")
    exit(1)

session = requests.Session()


# Returns true if successfully logged in
def login(username: str, password: str) -> bool:
    login_post_data = {
        "_token": None,
        "username": username,
        "password": password,
        "remember": "on"  # just incase so that we don't lose session during scraping
    }

    # Need to pass a check because of course
    login_page_req = session.get(f"{BASE_URL}/login", headers=headers)
    login_soup = BeautifulSoup(login_page_req.content, "lxml")
    token = login_soup.find("input", attrs={"name": "_token"})["value"]
    login_post_data["_token"] = token

    login_req = session.post(f"{BASE_URL}/login", data=login_post_data, headers=headers)
    if login_req.status_code == 200:
        return True


def get_overview() -> list:
    overview_req = session.get(url=f"{BASE_URL}/selector/query",
                               params={"page": "review", "type": "default", "value": ""}, headers=headers)
    overview = overview_req.json()
    return overview["list"]


def get_all_subjects() -> list[str]:
    subjects = []
    overview = get_overview()
    for item in overview:
        if item["type"] == "subject":
            subjects.append(item["value"])
    return subjects
    pass


def get_subjects_courses(subject: str) -> list[str]:
    courses = []
    subject_req = session.get(url=f"{BASE_URL}/selector/query",
                              params={"page": "review", "type": "subject", "value": subject}, headers=headers)
    course_res = subject_req.json()
    for item in course_res["list"]:
        if item["type"] == "course-review":
            courses.append(item["value"])
    return courses


login(login_details["username"], login_details["password"])
print(get_all_subjects())
print(get_subjects_courses("COMP"))
session.close()
