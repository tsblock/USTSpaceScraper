import time
import random
import json
import os

import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from ratelimit import limits


# Network stuff
BASE_URL = "https://ust.space"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": USER_AGENT
}

# Rate limits
CALLS = 20
PER_PERIOD = 60

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
    login_page_req = session.get(f"{BASE_URL}/login", headers=HEADERS)
    login_soup = BeautifulSoup(login_page_req.content, "lxml")
    token = login_soup.find("input", attrs={"name": "_token"})["value"]
    login_post_data["_token"] = token

    login_req = session.post(f"{BASE_URL}/login", data=login_post_data, headers=HEADERS)
    if login_req.status_code == 200:
        return True
    else:
        raise Exception("Unable to login!")


def get_overview() -> list:
    overview_req = session.get(url=f"{BASE_URL}/selector/query",
                               params={"page": "review", "type": "default", "value": ""}, headers=HEADERS)
    overview = overview_req.json()
    if overview["error"]:
        raise Exception("Can't get overview data!")
    return overview["list"]


def get_all_subjects() -> list[str]:
    subjects = []
    overview = get_overview()
    for item in overview:
        if item["type"] == "subject":
            subjects.append(item["value"])
    return subjects
    pass


def get_courses_in_subject(subject: str) -> list[str]:
    courses = []
    subject_req = session.get(url=f"{BASE_URL}/selector/query",
                              params={"page": "review", "type": "subject", "value": subject}, headers=HEADERS)
    course_res = subject_req.json()
    if course_res["error"]:
        raise Exception(f"Can't get courses in subject {subject}!")
    for item in course_res["list"]:
        if item["type"] == "course-review":
            courses.append(item["value"])
    return courses


# Eventually this will be the output files
@limits(calls=CALLS, period=PER_PERIOD)
def get_course_reviews(course: str) -> list[dict]:
    params = {
        "single": "false",
        "composer": "false",
        "preferences[sort]": 0,
        "preferences[filterSemester]": 0,
        "preferences[filterRating]": 0,
    }
    reviews_req = session.get(url=f"{BASE_URL}/review/{course}/get", params=params, headers=HEADERS)
    reviews = reviews_req.json()
    if reviews["error"]:
        raise Exception(f"Unable to get reviews from course {course}")
    return reviews


def dump():
    subjects = get_all_subjects()
    for subject in subjects:
        courses = get_courses_in_subject(subject)
        print(f"Walking through {subject}...")
        for course in courses:
            reviews = get_course_reviews(course)
            # need to create directories first...
            filename = f"output/{subject}/{course}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # finally we can write to json file
            with open(filename, "w+") as file:
                # why do we convert from json to python object back to json?
                # lol idk
                json.dump(reviews, file)
                print(f"Archived {course}")


login(login_details["username"], login_details["password"])
dump()

session.close()
