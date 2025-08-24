import pyodbc
import random

# ------------------ Helper Functions ------------------

def print_dict(dictionary):
    """
    Print the values and keys of a dictionary in a formatted way.
    """
    for key, value in dictionary.items():
        print(f"{value} - {key}")

def establish_connection(odbc_conn_str):
    """
    Establish a pyodbc connection using the given ODBC connection string.
    """
    return pyodbc.connect(odbc_conn_str)

def close_connection(conn):
    """
    Close the given database connection.
    """
    conn.close()

def query_show_name_by_id(conn, show_id):
    """
    Query the name of a show by its UID from tblCard.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT Name FROM tblCard WHERE UID = ?', (show_id,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else f"Unknown Show ({show_id})"

def query_worker_name_by_id(conn, worker_id):
    """
    Query the name of a worker by their UID from tblWorker.
    Returns 'Unknown' if not found or None.
    """
    if worker_id is None:
        return "Unknown"
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT Name FROM tblWorker WHERE UID = ?', (int(worker_id),))
        row = cursor.fetchone()
        return row[0] if row else "Unknown"
    finally:
        cursor.close()

def query_tournaments(conn):
    """
    Query all incomplete round robin tournaments from tblTournament.
    Returns a dict of tournaments and the federation ID.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tblTournament WHERE RoundRobin = True AND Complete = False')
    rows = cursor.fetchall()
    result_list = {}
    fed_id = 0
    for row in rows:
        result_list[row[0]] = (row[2], row[3])
        fed_id = row[1]
    cursor.close()
    return result_list, fed_id

def query_tournament_participants(conn, tournament_id, tournament_type):
    """
    Query participants for a tournament from tblTournamentRobin.
    Returns a list of participant IDs or teams depending on type.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tblTournamentRobin WHERE TournamentUID = ?', (tournament_id,))
    rows = cursor.fetchall()
    result_list = []
    for row in rows:
        if tournament_type == 1:
            result_list.append(row[3])
        elif tournament_type == 2:
            result_list.append([row[3], row[4]])
        elif tournament_type == 3:
            result_list.append([row[3], row[4], row[5]])
    cursor.close()
    return result_list

def query_shows_of_fed(conn, fed_id):
    """
    Query all shows for a federation from tblCard.
    Returns a dict {ShowID: ShowName}.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tblCard WHERE Fed = ?', (fed_id,))
    rows = cursor.fetchall()
    result_list = {row[0]: row[1] for row in rows}
    cursor.close()
    return result_list

def generate_round_robin_tournament(participant_ids):
    """
    Generate a round-robin schedule for the given participant IDs.
    Returns a list of rounds, each with match tuples.
    """
    if len(participant_ids) % 2 != 0:
        participant_ids.append("bye")
    schedule = []
    rounds = participant_ids + participant_ids
    for i in range(1, len(participant_ids)):
        round_matches = []
        for j in range(len(participant_ids)//2):
            match = (rounds[j], rounds[len(participant_ids)-1-j])
            match_list = list(match)
            random.shuffle(match_list)
            round_matches.append(tuple(match_list))
        random.shuffle(round_matches)
        schedule.append(round_matches)
        rounds = [rounds[0]] + [rounds[-1]] + rounds[1:-1]
    return schedule

def clear_pre_booking(conn):
    """
    Clear all pre-booking data from the relevant tables.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM tblPreBooking')
        cursor.execute('DELETE FROM tblPreBookingInvolvedMatch')
        cursor.execute('DELETE FROM tblPreBookingNote')
        conn.commit()
        print("CLEARED Pre Booking")
    except pyodbc.Error as e:
        print(f"Error clearing pre-booking: {e}")
    finally:
        cursor.close()

def get_last_prebooking_id(conn):
    """
    Get the highest UID from tblPreBooking.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT MAX(UID) AS MaxUID FROM tblPreBooking')
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0
    finally:
        cursor.close()

def add_data_to_tblPreBooking(conn, cursor, uid, booking_name, fed_id, card_uid, match_or_angle_id, match_length, match_uid):
    """
    Insert a new pre-booking entry into tblPreBooking.
    """
    query = "INSERT INTO tblPreBooking (UID, Booking_Name, FedUID, CardUID, TVUID, Match, MatchUID, Length, Major, Belt1, Belt2, Belt3, Booked, AngleOutput, Scripted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (uid, booking_name, fed_id, card_uid, 0, True, match_uid, match_length, True, 0, 0, 0, 0, 0, None)
    cursor.execute(query, values)
    conn.commit()

def add_data_to_tblPreBookingInvolved(conn, cursor, prebooking_uid, fed_uid, position, involved):
    """
    Insert a new involved entry into tblPreBookingInvolvedMatch.
    """
    query = "INSERT INTO tblPreBookingInvolvedMatch (PreBookingUID, FedUID, Position, Involved, Complain) VALUES (?, ?, ?, ?, ?)"
    values = (prebooking_uid, fed_uid, position, involved, 0)
    cursor.execute(query, values)
    conn.commit()

def add_data_to_tblPreBookingNote(conn, cursor, userbooking_uid, fed_uid):
    """
    Insert a new note entry into tblPreBookingNote.
    """
    query = "INSERT INTO tblPreBookingNote (UserBookingUID, Position, RoadAgent_Type, RoadAgent_Worker, RoadAgent_Attack, Used, BeltUID, Champion1, Champion2, Champion3, Match, FedUID, StoryUID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (userbooking_uid, 1, 200, 0, 0, False, 0, 0, 0, 0, True, fed_uid, 0)
    cursor.execute(query, values)
    conn.commit()

def book_tournament_day(conn, prefix, day, show, match_list, tournament_type, fed_id, match_length_list, match_uid):
    """
    Book all matches for a single day of a tournament.
    match_uid: UID from tblMatch selected in GUI
    match_list: list of matches (singles/teams)
    match_length_list: list of match lengths per match
    """
    last_prebooking_id = get_last_prebooking_id(conn) + 1
    cursor = conn.cursor()
    for idx, match in enumerate(match_list):
        match_length = match_length_list[idx]
        if tournament_type == 1:
            booking_name = f"{prefix}: {query_worker_name_by_id(conn, match[0])} vs {query_worker_name_by_id(conn, match[1])}"
        else:
            team_names = ["|".join(query_worker_name_by_id(conn, pid) for pid in team) for team in match]
            booking_name = f"{prefix}: {team_names[0]} vs {team_names[1]}"

        card_uid = {1: 1, 2: 391, 3: 498}[tournament_type]
        add_data_to_tblPreBooking(conn, cursor, last_prebooking_id, booking_name, fed_id, show, match_uid, match_length, match_uid)

        if tournament_type == 1:
            for pos, pid in enumerate(match):
                add_data_to_tblPreBookingInvolved(conn, cursor, last_prebooking_id, fed_id, pos+1, pid)
        else:
            pos = 1
            for team in match:
                for pid in team:
                    add_data_to_tblPreBookingInvolved(conn, cursor, last_prebooking_id, fed_id, pos, pid)
                    pos += 1

        add_data_to_tblPreBookingNote(conn, cursor, last_prebooking_id, fed_id)
        last_prebooking_id += 1
    cursor.close()

def book_tournament(conn, prefix, tournament_dict, show_list, match_lengths_dict, tournament_type, fed_id, match_uid):
    """
    GUI-driven booking for singles, tag, and trios tournaments.
    Each day uses one show from show_list.
    """
    num_days = len(tournament_dict)
    if len(show_list) < num_days:
        raise ValueError("Not enough shows for all tournament days!")

    for day_idx, day in enumerate(sorted(tournament_dict.keys())):
        matches = tournament_dict[day]
        lengths = match_lengths_dict.get(day, [0]*len(matches))
        show_id = show_list[day_idx]  # One show per day

        if len(matches) != len(lengths):
            raise ValueError(f"Day {day} has {len(matches)} matches but {len(lengths)} lengths provided!")

        # Book all matches for this day at once
        book_tournament_day(conn, prefix, day, show_id, matches, tournament_type, fed_id, lengths, match_uid)

