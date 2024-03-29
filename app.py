from flask import Flask, render_template, request, json, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import sqlite3

from input import art_input
import input_book
from db_books import Books
from db_arthub import Arthub
from db_team import Team
from arthub_d2v import western_data
from arthub_d2v import lda_sim

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ExhbnRec.db'
app.config['SECRET_KEY'] = "dubu"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = False

db = SQLAlchemy(app)
conn = sqlite3.connect("ExhbnRec.db")
cur = conn.cursor()

book_list = pd.read_sql_query('SELECT name FROM books_info', conn)
book_name_list = book_list.name.tolist()
data_final = pd.read_sql_query('SELECT * FROM arthub_info', conn)

ko_bestseller = db.session.query(Books).filter_by(genre="한국소설").limit(5).all()
jp_bestseller = db.session.query(Books).filter_by(genre="일본소설").limit(5).all()
en_bestseller = db.session.query(Books).filter_by(genre="영미소설").limit(5).all()
etc_bestseller = db.session.query(Books).filter_by(genre="기타 외국 소설").limit(5).all()
bestseller = [ko_bestseller, jp_bestseller, en_bestseller, etc_bestseller]


# @app.route('/')
# def root():
#     return render_template('base.html',bestseller = bestseller)


@app.route('/')
def index():
    return render_template('index_book.html', active='index_book', book_list = book_name_list, bestseller=bestseller)


@app.route('/index_art')
def index_art():
    return render_template('index.html', famous_paint=art_input(), active='index_art')


@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        book_name = request.args.get('book_name') # 쿼리한 책 제목을 get으로 받아옴
        if book_name:
            book_info = db.session.query(Books).filter(Books.name==book_name).first()
        else:
            book_info = ''

    return render_template('index_book.html', active='index_book', book_name=book_name, book_info=book_info, book_list=book_name_list, bestseller=bestseller)


@app.route('/load_ajax', methods=['POST'])
def load_ajax():
    if request.method == 'POST':
        book_name = request.form['book_name']
        result = db.session.query(Books).filter_by(name=book_name)

        book_nouns = None
        for row in result:
            book_nouns = row.noun.split(',')
        plot_url = input_book.word_cloud(book_nouns)
        return json.dumps({'status':'OK', 'plot_url':plot_url})


@app.route('/exhbnRec', methods = ['POST','GET']) # Exhibition Recommendation
def exhbnRec():
    test_txt_list = []
    title = ''
    try:
        title = request.form['title']
    except:
        pass

    if title != '': # title을 넘겨받았을 경우
        book_corpus = db.session.query(Books.noun).filter_by(name=title).first() # 저장된 해당 도서의 명사 token을 리턴
        sims = lda_sim(book_corpus, data_final) # 명사 token을 쿼리로 사용하여 data_final에 저장된 전시 중 쿼리와 유사도 높은 전시를 받아옴

    elif title=='': # title을 넘겨받지 못한 경우
        result = request.form
        result_selected = []

        for key in result.keys():
            if result[key] == '1':
                result_selected.extend(key)
        if not result_selected:
            return redirect(url_for('index_art'))

        for index in result_selected:
            test_txt_list.append(western_data['noun'][int(index)])

        test_txt_list = test_txt_list[0].split(',')

        sims = lda_sim(test_txt_list, data_final)
    else:
        return render_template('index_book.html', bestseller=bestseller, book_name_list=book_name_list, active='index_book')

    simsKeys = list(sims.keys()) # sims = {(exhb_key:similarity),}

    q = db.session.query(Arthub).filter(Arthub.id.in_(simsKeys))
    query_as_string = str(q.statement.compile(compile_kwargs={"literal_binds": True}))
    model=db.session.execute(query_as_string).fetchall()

    simsVal = []
    sorted_sims = sorted(sims.items(), key=lambda kv: kv[1], reverse=True)
    for tpl in sorted_sims:
        simsVal.append(tpl[1])

    return render_template('exhbnRec.html', active='exhbnRec', sims=simsVal, model=model)


@app.route('/aboutUs')  # about Us
def aboutUs():
    model = db.session.query(Team).all()
    return render_template('aboutUs.html', active='aboutUs', model=model)


@app.route('/intro')  # introduce
def intro():
    return render_template('intro.html', active='intro')


@app.route('/skills')  # Common Elements
def skills():
    return render_template('skills.html', active='skills')


@app.route('/elements')  # Common Elements
def elements():
    return render_template('elements.html', active='elements')

if __name__ == '__main__':
    app.run()
