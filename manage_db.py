import sqlite3


def insert_user(user):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")

        c.execute("INSERT INTO users VALUES (:id, :fullname, :cathedra)",
                  {'id': user['id'], 'fullname': user['fullname'], 'cathedra': user['cathedra']})


def get_users_by_cathedra(cathedra):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE cathedra = :cathedra", {'cathedra': cathedra})
        return c.fetchall()


def get_all_users_id():
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT id FROM users")
        return [i[0] for i in c.fetchall()]


def remove_user_by_id(chat_id):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")

        c.execute("DELETE from users WHERE id = :id", {'id': chat_id})


def get_all_cathedras():
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM cathedras")
        return [i[0] for i in c.fetchall()]


def check_cathedra(cathedra):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM cathedras WHERE name = :name", {'name': cathedra})

        if c.fetchone():
            return True
        return False


def get_lecturers_by_cathedra(cathedra):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT fullname FROM lecturers WHERE cathedra = :cathedra", {'cathedra': cathedra})
        return [i[0] for i in c.fetchall()]


def get_lecturer_by_id(chat_id):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT fullname FROM users WHERE id = :id", {'id': chat_id})
        return c.fetchone()[0]


def get_lectures_by_month(lecturer, month):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute(f"SELECT lectures FROM {month_to_table(month)} WHERE lecturer = :lecturer", {'lecturer': lecturer})
        lectures_db = c.fetchone()[0]
        return read_lectures(lectures_db)


def check_lecturer(lecturer):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM lecturers WHERE fullname = :fullname", {'fullname': lecturer})

        if c.fetchone():
            return True
        return False


def read_lectures(lectures_db):
    lectures = {}

    if lectures_db:
        for line in lectures_db.split('\n'):
            lectures[line[:line.find('[')]] = line[line.find('[') + 1:].split('|')
        return lectures
    return {}


def check_id(chat_id):
    with sqlite3.connect('lectures.db') as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = :id", {'id': chat_id})

        if c.fetchone():
            return True
        return False


def month_to_table(month):
    table = ['schedule_january', 'schedule_february', 'schedule_march', 'schedule_april',
             'schedule_may', 'schedule_june', 'schedule_july', 'schedule_august',
             'schedule_september', 'schedule_october', 'schedule_november', 'schedule_december']
    return table[int(month) - 1]
