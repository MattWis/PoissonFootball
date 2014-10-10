import os
import datetime

exceptions = { "Bears 23Eagles 28": ((23, 28), (15 + 6 + 4 / 60.0, "TD", "Bears")),
               "Bears 31Eagles 28": ((31, 28), (15 + 1 + 29 / 60.0, "TD", "Bears")) }


points_for = { "FG": 3, "TD": 7 }
quarter_times = {"1st Quarter": 45, "2nd Quarter": 30,
                 "3rd Quarter": 15, "4th Quarter": 0 }

def main():
    url_base = "http://www.covers.com"
    url = url_base + "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team7.html"
    output = os.popen("curl " + url + " | " +
                    "pup table.data td.datacell a attr{href}")
    urls = []
    for line in output:
        if "boxscore" in line:
            urls.append(url_base + line.strip())

    games = []
    for url in urls:
        print(url)
        games.append(scrape_box_score(url))
    print(games)

def scrape_box_score(url):
    html = os.popen("curl " + url + " | pup table.num-left text{}")
    filtered = []
    for line in html:
        line = line.strip(" \t\n")
        if line != "" and line != "-":
            filtered.append(line)

    scores = [] # [(rem_time, "FG" or "TD", team_name)]

    #teams = ("49ers", "Eagles")
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
    print("Add exception for: '"+ lines[0] + lines[1] + "'")
    print(lines)
    print(cur_score)
    print(teams)
    print(goal_type)
    raise ValueError()


if __name__ == "__main__":
    main()
