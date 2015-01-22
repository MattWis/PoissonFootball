import os
import datetime


#Teams that can be simulated currently
teams = ["Eagles", "Giants", "Panthers", "Patriots", "Seahawks"]

#Number of preseason games played by each team
preseason = { "Eagles": 4, "Giants": 5, "Panthers": 4,
              "Patriots": 4, "Seahawks": 4 }

urls = {
    "Eagles": "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team7.html",
    "Giants": "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team8.html",
    "Panthers": "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team29.html",
    "Patriots": "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team18.html",
    "Seahawks": "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team19.html"
}

exceptions = {
    "Bears 23Eagles 28": ((23, 28), (15 + 6 + 4 / 60.0, "TD", "Bears")),
    "Bears 31Eagles 28": ((31, 28), (15 + 1 + 29 / 60.0, "TD", "Bears")),
    "Giants 14Cardinals 19": ((14, 19), (0 + 10 + 10 / 60.0, "TD", "Cardinals")),
    "Lions 35Giants 14": ((35, 14), (0 + 4 + 39 / 60.0, "TD", "Lions")),
    "Panthers 19Steelers 37": ((19, 37), (0 + 3 + 53 / 60.0, "TD", "Panthers")),
    "Panthers 21Lions 7": ((21, 7), (0 + 7 + 26 / 60.0, "TD", "Panthers")),
    "Patriots 43Broncos 21": ((43, 21), (0 + 13 + 57 / 60.0, "TD", "Patriots")),
    "Patriots 45Bears 15": ((45, 15), (15 + 0 + 54 / 60.0, "TD", "Bears")),
    "Patriots 48Bears 23": ((48, 23), (0 + 5 + 16 / 60.0, "TD", "Bears")),
    "Patriots 27Jets 25": ((27, 25), (0 + 2 + 31 / 60.0, "TD", "Jets")),
    "Bills 22Patriots 30": ((22, 30), (0 + 5 + 58 / 60.0, "TD", "Bills")),
    "Seahawks 22Packers 19": ((22, 19), (0 + 1 + 25 / 60.0, "TD", "Seahawks")),
    "Rams 21Seahawks 19": ((21, 19), (0 + 9 + 44 / 60.0, "TD", "Seahawks")),
    "Seahawks 17Broncos 12": ((17, 12), (0 + 9 + 20 / 60.0, "TD", "Broncos")),
    "Seahawks 20Broncos 20": ((20, 20), (0 + 0 + 18 / 60.0, "TD", "Broncos")),
    "Seahawks 29Packers 10": ((29, 10), (0 + 14 + 55 / 60.0, "TD", "Seahawks")),
    "Seahawks 29Packers 16": ((29, 16), (0 + 9 + 31 / 60.0, "TD", "Packers")),
}


points_for = { "FG": 3, "TD": 7 }
quarter_times = {"1st Quarter": 45, "2nd Quarter": 30,
                 "3rd Quarter": 15, "4th Quarter": 0 }

def main():
    """Scrape a given team url, and print the results
    """
    print(scrape_team("Eagles"))

def scrape_team(team_name):
    return scrape_team_url(urls[team_name], preseason[team_name])

def scrape_team_url(team_url, preseason_games):
    """Scrape a team url from www.covers.com.
    Uses pup to process html.
    Returns a list of games from scrape_box_score
    """
    url_base = "http://www.covers.com"
    output = os.popen("curl " + url_base + team_url + " | " +
                    "pup table.data td.datacell a attr{href}")

    urls = [url_base + line.strip() for line in output if "boxscore" in line]

    return [scrape_box_score(url) for url in urls[:-preseason_games]]

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

    slices = [filtered[i: i+5] for i in range(len(filtered) - 5)]
    for view in slices:
        if view[0] in quarter_times:
            new_score, score = parseScoreTime(view, cur_score, teams)
            if score != None:
              cur_score = new_score
              scores.append(score)

    return scores

def get_team_names(lines):
    """Gets the names of teams playing a certain game.
    Returns a tuple of two team names as strings
    """
    for i, line in enumerate(lines):
        if lines[i] in quarter_times:
            team0 = lines[i + 3].split()[0]
            team1 = lines[i + 4].split()[0]
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
    if "TD" in goal_line:
        goal_type = "TD"
    elif "FG" in goal_line:
        goal_type = "FG"
    else:
        return (None, None)

    new_score, team = parseScore(lines[3:5], cur_score, teams, goal_type, rem_time)

    return new_score, (rem_time, goal_type, team)

def parseScore(lines, cur_score, teams, goal_type, rem_time = None):
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
            #Neither team has scored
            error(lines, cur_score, teams, goal_type, rem_time)
        elif str(cur_score[1] + points_for[goal_type]) in lines[1]:
            #Team 1 scored correct amount
            team = teams[1]
            new_score = (cur_score[0], cur_score[1] + points_for[goal_type])
        else:
            #Team 1 scored incorrectly
            error(lines, cur_score, teams, goal_type, rem_time)
    elif str(cur_score[0] + points_for[goal_type]) in lines[0]:
        if str(cur_score[1]) in lines[1]:
            #Team 0 scored correct amount
            team = teams[0]
            new_score = (cur_score[0] + points_for[goal_type], cur_score[1])
        else:
            #Team 0 scored incorrectly
            error(lines, cur_score, teams, goal_type, rem_time)
    else:
        #Both teams scored
        error(lines, cur_score, teams, goal_type, rem_time)

    return new_score, team

def error(lines, cur_score, teams, goal_type, rem_time=None):
    """Errors on odd data, and asks for an exception to be added
    """
    print("Add exception for: '"+ lines[0] + lines[1] + "'")
    print(lines)
    print(cur_score)
    print(teams)
    print(goal_type)
    print(rem_time)
    raise ValueError()


if __name__ == "__main__":
    main()
