import calendar
import csv
import datetime
import os
import subprocess
from collections import defaultdict, Counter
from typing import Callable, Dict, Generator

import json

# TODO: load this from toml
NAMES_MAP: Dict[str, str]= {
    "Oskar O": "Oskar O.",
    "Oskar": "Oskar O.",
    "code": "Oskar O.",
    "Oskar Orzełowski": "Oskar O.",
    "Forkility": "Oskar O.",
    "Sebastian Opałczyński": "Sebastian O.",
    "Sebastian Opalczynski": "Sebastian O.",
    "Olaf Górski": "Olaf G.",
    "Krzysztof Kolacz": "Krzychu K.",
    "Krzychu Kolacz": "Krzychu K.",
    "Adrian Podsiadły": "Adrian P.",
    "ap": "Adrian P.",
    "Marcin Gordziejewski": "Marcin G.",
    "Dima Miro": "Dima M.",
    "Dima Miroshnichenko": "Dima M.",
    "Sylvestre Lucia": "Sylvestre L.",
    "Tomasz Mularczyk": "Tomasz M."
}
PEOPLE_TO_FILTER = {"Adrian P.", "Tomasz M.", "Sylvestre L.", "Marcin G.", "bitbucket-pipelines"}
POSSIBLE_STATS: tuple = ("files", "insertion", "deletion")
DAY_NAMES = {value: index for index, value in enumerate(calendar.day_name)}
MONTH_NAMES = {value: index for index, value in enumerate(calendar.month_name)}


def get_stats(stats: str):
    stats: Generator = (line for line in stats.splitlines() if len(line) > 10)
    return {line.strip(): next(stats) for line in stats}


def populate_given_commits_gathering(raw_commits: dict, commit_gathering: defaultdict):
    author: dict = commit_gathering[NAMES_MAP.get(name, name)]
    author["commits_count"] += 1
    try:
        for stat in raw_commits[repo_commit["commit"]].split(","):
            for possible_stat in POSSIBLE_STATS:
                if possible_stat in stat:
                    author["stats"][possible_stat] += int(''.join(c for c in stat if c.isdigit()))
    except KeyError:
        pass

def group_for_plotly(commits, sort_by=None) -> dict:
    if sort_by:
        commits = dict(sorted(commits.items(), key=lambda x: sort_by[x[0]]))
    grouped_commits: defaultdict = defaultdict(lambda: defaultdict(list))
    for day in commits:
        for user_name in commits[day]:
            grouped_commits[user_name]["y"] += [commits[day][user_name]["commits_count"]]
            grouped_commits[user_name]["x"] += [day]
    return grouped_commits


def filter_for_plotly(grouped_plotly_data: dict):
    plotly_data: list = []
    for name in (filtered_name for filtered_name in grouped_plotly_data if filtered_name not in PEOPLE_TO_FILTER):
        grouped_plotly_data[name]["name"] = name
        plotly_data.append(grouped_plotly_data[name])
    return plotly_data


def aggregate_author_values(author_specific, get_key = lambda x: x["name"]):
    values, labels = zip(*[(sum(author["y"]), get_key(author)) for author in author_specific])
    return labels, values


def individual_to_team(per_author):
    unit_sums = list(Counter(dict(zip(author["x"], author["y"]))) for author in per_author)
    return dict(sum(unit_sums, Counter()))


def format_to_result(pre_result):
    result = defaultdict(list)
    for key, value in pre_result.items():
        result["y"] += [value]
        result["x"] += [key]
    return result


author_name: Callable = lambda: {"stats": defaultdict(int), "commits_count": 0}
commits_data_bank_factory: Callable = lambda: defaultdict(lambda: defaultdict(author_name))
# todo: per week day, per week and so on

projects = ("deeptrue-backend", "survey-engine",)
for project in projects:
    if not os.path.exists(f"json/{project}"):
        os.makedirs(f"json/{project}")
    commits_per_date: defaultdict = commits_data_bank_factory()
    commits_per_hour: defaultdict = commits_data_bank_factory()
    commits_per_weekday: defaultdict = commits_data_bank_factory()
    commits_per_month: defaultdict = commits_data_bank_factory()
    lookup_dir = f"../../deeptrue/{project}"
    logs_json: str = subprocess.run(["sh", "logs.sh", lookup_dir], stdout=subprocess.PIPE).stdout.decode()
    stats_string: str = subprocess.run(["sh", "stats.sh", lookup_dir], stdout=subprocess.PIPE).stdout.decode()
    longest_files: str = subprocess.run(["sh", "longest.sh", lookup_dir], stdout=subprocess.PIPE).stdout.decode()
    repo_commits: Dict = json.loads(logs_json)
    commits_stats: Dict[str, str] = get_stats(stats_string)
    file_length: csv.DictReader = csv.DictReader(longest_files.splitlines(), fieldnames=("file","length"), delimiter=";")

    for repo_commit in repo_commits:
        commit_datetime: datetime.datetime = datetime.datetime.fromisoformat(repo_commit["author"]["date"])
        commit_date: datetime.date = commit_datetime.date()
        name: str = repo_commit["author"]["name"]
        populate_given_commits_gathering(raw_commits=commits_stats, commit_gathering=commits_per_date[commit_date.isoformat()])
        populate_given_commits_gathering(raw_commits=commits_stats, commit_gathering=commits_per_hour[commit_datetime.hour])
        populate_given_commits_gathering(raw_commits=commits_stats, commit_gathering=commits_per_weekday[commit_datetime.strftime("%A")])
        populate_given_commits_gathering(raw_commits=commits_stats, commit_gathering=commits_per_month[commit_datetime.strftime("%B")])



    # WEEKDAY
    commits_per_weekday_per_author = filter_for_plotly(group_for_plotly(commits_per_weekday, sort_by=DAY_NAMES))
    commits_per_weekday_team = [format_to_result(individual_to_team(commits_per_weekday_per_author))]
    json.dump(commits_per_weekday_per_author, open(f"json/{project}/commits_per_weekday_per_author.json", "w"))
    json.dump(commits_per_weekday_team, open(f"json/{project}/commits_per_weekday_team.json", "w"))

    # DAILY
    commits_per_date_per_author = filter_for_plotly(group_for_plotly(commits_per_date))
    commits_per_date_team = [format_to_result(individual_to_team(commits_per_date_per_author))]
    json.dump(commits_per_date_per_author, open(f"json/{project}/commits_per_day_per_author.json", "w"))
    json.dump(commits_per_date_team, open(f"json/{project}/commits_per_day_team.json", "w"))

    # TOTAL
    total_commits = aggregate_author_values(commits_per_date_per_author)
    total_commits_formatted = [dict(zip(("labels", "values"), total_commits))]
    json.dump(total_commits_formatted, open(f"json/{project}/total_pie_chart.json", "w"))
    json.dump([{"labels": commits_per_weekday_team[0]["x"], "values": commits_per_weekday_team[0]["y"]}], open(
        f"json/{project}/weekdays_commits_pie.json", "w"))
    json.dump([{"name": key, "commits": value} for key, value in sorted(zip(*total_commits), key=lambda x: x[1])], open(
        f"json/{project}/commiters.json", "w"))

    # MONTHLY
    commits_per_month_per_author = filter_for_plotly(group_for_plotly(commits_per_month, sort_by=MONTH_NAMES))
    commits_per_month_team = [format_to_result(individual_to_team(commits_per_month_per_author))]
    json.dump(commits_per_month_per_author, open(f"json/{project}/commits_per_month_per_author.json", "w"))
    json.dump(commits_per_month_team, open(f"json/{project}/commits_per_month_team.json", "w"))

    # HOURLY
    commits_per_hour_per_author = filter_for_plotly(group_for_plotly(commits_per_hour))
    commits_per_hour_team = [format_to_result(individual_to_team(commits_per_hour_per_author))]
    json.dump(commits_per_hour_per_author, open(f"json/{project}/commits_per_hour_per_author.json", "w"))
    json.dump(commits_per_hour_team, open(f"json/{project}/commits_per_hour_team.json", "w"))

    json.dump(list(file_length), open(f"json/{project}/file_lengths.json", "w"))
    json.dump({"repo_commits": repo_commits, "commits_stats": commits_stats}, open(f"json/{project}/base_stats.json", "w"))
