import os
import datetime

exceptions = { "Bears 23Eagles 28": ((23, 28), (15 + 6 + 4 / 60.0, "TD", "Bears")),
               "Bears 31Eagles 28": ((31, 28), (15 + 1 + 29 / 60.0, "TD", "Bears")),
               "Giants 14Cardinals 19": ((14,19), (0 + 10 + 10 / 60.0, "TD", "Cardinals")),
               "Lions 35Giants 14": ((27,14), (0 + 4 + 39 / 60.0, "TD", "Lions")) }


points_for = { "FG": 3, "TD": 7 }
quarter_times = {"1st Quarter": 45, "2nd Quarter": 30,
                 "3rd Quarter": 15, "4th Quarter": 0 }
games_in_season = 5
games_to_ignore = 1

def main():
    """Scrape a given team url, and print the results
    """
    giants_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team8.html"
    eagles_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team7.html"
    team_url = eagles_url
    games = scrape_team(team_url)
    print(games)


def scrape_team(team_url):
    """Scrape a team url from www.covers.com.
    Uses pup to process html.
    Returns a list of games from scrape_box_score
    """
    url_base = "http://www.covers.com"
    url = url_base + team_url
    output = os.popen("curl " + url + " | " +
                    "pup table.data td.datacell a attr{href}")
    urls = []
    for line in output:
        if "boxscore" in line:
            urls.append(url_base + line.strip())

    games = []
    for url in urls[games_to_ignore:]:
        if len(games) >= games_in_season:
            break
        games.append(scrape_box_score(url))
    return games

def scrape_box_score(url):
    """Scrape a team url from www.covers.com.
    Uses pup to process html.
    Returns a list of scoring events, which have the form:
        (time left in game, scoring type, team that scored)
    """
    html = os.popen("curl " + url + " | pup table.num-left text{}")
    filtered = []
    for line in html:
        line = line.strip(" \t\n")
        if line != "" and line != "-":
            filtered.append(line)

    scores = [] # [(rem_time, "FG" or "TD", team_name)]

    teams = get_team_names(filtered)
    cur_score = (0,0)
    i = 0
    line = filtered[i]
    while line != None:
        if line in quarter_times:
            cur_score, score = parseScoreTime(filtered[i: i+5], cur_score, teams, )
            scores.append(score)
        i += 1
        try:
            line = filtered[i]
        except IndexError:
            line = None

    return scores

def get_team_names(lines):
    """Gets the names of teams playing a certain game.
    Returns a tuple of two team names as strings
    """
    i = 0
    line = lines[i]
    while line != None:
        if line in quarter_times:
            team0 = lines[i+3].split()[0]
            team1 = lines[i+4].split()[0]
            break;
        i += 1
    return (team0, team1)

def parseScoreTime(lines, cur_score, teams):
    """Parses and individual scoring event, and the time it happened.
    Uses exceptions defined at the top of this file to handle scores that
    aren't 3 or 7 points.

    Returns an odd format:
        ( new score for the team,
          (time left in game at scoring event, type of score, team name)
        )
    """
    if lines[3] + lines[4] in exceptions:
        return exceptions[lines[3] + lines[4]]

    quarter_rem_time = quarter_times[lines[0]]
    time = datetime.datetime.strptime(lines[1], "%M:%S").time()
    rem_time = time.minute + time.second / 60.0 + quarter_rem_time

    goal_line = lines[2]
    goal_type = ""
    if "TD" in goal_line:
        goal_type = "TD"
    elif "FG" in goal_line:
        goal_type = "FG"
    else:
        raise ValueError("I don't know other goal types")

    new_score, team = parseScore(lines[3:5], cur_score, teams, goal_type)

    return new_score, (rem_time, goal_type, team)

def parseScore(lines, cur_score, teams, goal_type):
    """Intentionally brittle function to parse a score out from a string.
    Will ask to add exception on error.
    Returns the new score and team name
    """

    if not teams[0] in lines[0]:
        raise ValueError("Team error")
    if not teams[1] in lines[1]:
        raise ValueError("Team error")

    if str(cur_score[0]) in lines[0]:
        if str(cur_score[1]) in lines[1]:
            error(lines, cur_score, teams, goal_type)
        elif str(cur_score[1] + points_for[goal_type]) in lines[1]:
            team = teams[1]
            new_score = (cur_score[0], cur_score[1] + points_for[goal_type])
        else:
            error(lines, cur_score, teams, goal_type)
    elif str(cur_score[0] + points_for[goal_type]) in lines[0]:
        if str(cur_score[1]) in lines[1]:
            team = teams[0]
            new_score = (cur_score[0] + points_for[goal_type], cur_score[1])
        else:
            error(lines, cur_score, teams, goal_type)
    else:
        error(lines, cur_score, teams, goal_type)

    return new_score, team

def error(lines, cur_score, teams, goal_type):
    """Errors on odd data, and asks for an exception to be added
    """
    print("Add exception for: '"+ lines[0] + lines[1] + "'")
    print(lines)
    print(cur_score)
    print(teams)
    print(goal_type)
    raise ValueError()


if __name__ == "__main__":
    main()
