import pandas as pd

# 저장된 명화 pandas DF로 읽어와 25개 sample 리턴하는 함수
def art_input():
    western_data = pd.read_csv('static/data/western_preprocessed.csv')
    famous_paint = western_data[['title', 'artist', 'image']].sample(25)
    return famous_paint