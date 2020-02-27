from flask import Flask, render_template, g, request
from functools import reduce
from datetime import datetime
from database import get_db


app = Flask(__name__)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3_db'):
        g.sqlite3_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db()

    if request.method == 'POST':
        date = request.form['date']
        conn.execute('insert into log_date (entry_date) values (?)', [date])
        conn.commit()

    results = conn.execute('select * from log_date order by entry_date desc').fetchall()

    totals_per_day = {}
    for day in results:
        totals_per_day[day['entry_date']] = {}
        food_in_that_day = conn.execute('select * from food where id in \
                                        (select food_id from food_log_date where food_log_date.log_date_id = ?)',
                                        [day['id']]).fetchall()

        totals_per_day[day['entry_date']]['protein'] = reduce((lambda x, y: x + y),
                                                              map(lambda x: x['protein'], food_in_that_day), 0)
        totals_per_day[day['entry_date']]['carbs'] = reduce((lambda x, y: x + y),
                                                            map(lambda x: x['carbohydrates'], food_in_that_day),  0)
        totals_per_day[day['entry_date']]['fat'] = reduce((lambda x, y: x + y),
                                                          map(lambda x: x['fat'], food_in_that_day), 0)
        totals_per_day[day['entry_date']]['calories'] = reduce((lambda x, y: x + y),
                                                               map(lambda x: x['calories'], food_in_that_day), 0)

    return render_template('home.html', dates=get_dates(results), totals_per_day=totals_per_day)


@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    conn = get_db()

    date_result = conn.execute('select id, entry_date from log_date where entry_date = ?', [date]).fetchone()

    if request.method == 'POST':
        if 'cancel' in request.form.keys():
            conn.execute('delete from food_log_date where food_id=?', [request.form['cancel']])
            conn.commit()
        else:
            conn.execute('insert into food_log_date (food_id, log_date_id) values (?, ?)',
                         [request.form['food-select'], date_result['id']])
            conn.commit()

    food_results = conn.execute('select id, name from food').fetchall()
    date_food_results = conn.execute(
        'select * from food where id in \
        (select food_id from food_log_date inner join log_date on food_log_date.log_date_id=?)',
        [date_result['id']]).fetchall()

    total_proteins = reduce((lambda x, y: x + y), map(lambda x: x['protein'], date_food_results), 0)
    total_carbs = reduce((lambda x, y: x + y), map(lambda x: x['carbohydrates'], date_food_results), 0)
    total_fat = reduce((lambda x, y: x + y), map(lambda x: x['fat'], date_food_results), 0)
    total_calories = reduce((lambda x, y: x + y), map(lambda x: x['calories'], date_food_results), 0)

    return render_template('day.html',
                           dates=get_dates(date_result),
                           food_list=food_results,
                           date_food_list=date_food_results,
                           total_proteins=total_proteins,
                           total_calories=total_calories,
                           total_carbs=total_carbs,
                           total_fat=total_fat)


@app.route('/food', methods=['GET', 'POST'])
def food():
    conn = get_db()

    if request.method == 'POST':
        if request.form['submit'] == "Add":
            name = request.form['food-name']
            proteins = int(request.form['protein-value'])
            carbs = int(request.form['carbs-value'])
            fat = int(request.form['fat-value'])
            calories = proteins * 4 + carbs * 4 + fat * 9

            conn.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?, ?, ?, ?, ?)',
                         [name, proteins, carbs, fat, calories])
            conn.commit()
        else:
            conn.execute('delete from food where id = ?', [request.form['submit']])
            conn.commit()

    results = conn.execute('select * from food').fetchall()
    return render_template('add_food.html', food_list=results)


def get_dates(db_results):

    dates = []
    if isinstance(db_results, list):
        for day in list(db_results):
            dates.append({"formatted": datetime.strftime(datetime.fromisoformat(day['entry_date']), '%B %d, %Y'),
                          "unformatted": day['entry_date']})
    else:
        dates.append({"formatted": datetime.strftime(datetime.fromisoformat(db_results['entry_date']), '%B %d, %Y'),
                      "unformatted": db_results['entry_date']})
    return dates


if __name__ == '__main__':
    app.run(debug=True)
