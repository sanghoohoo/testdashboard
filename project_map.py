import pandas as pd
import numpy as np
import json
import folium
import re
from fuzzywuzzy import process

# 데이터 로드
df_iowa = pd.read_excel('Iowa ACT 5 Year Trends by District for Graduating Classes 2019 to 2023 (2).xlsx')
geo_iowa = json.load(open('Iowa_School_Districts_2023-2024.geojson', encoding='UTF-8'))

# 데이터 전처리
df_iowa.columns = df_iowa.iloc[1]
df_iowa = df_iowa.iloc[2:, :]
df_iowa.reset_index(drop=True, inplace=True)
df_iowa.replace('Small N', np.nan, inplace=True)
df_iowa.dropna(inplace=True)
df_iowa['CRB % All Four'] = pd.to_numeric(df_iowa['CRB % All Four'])

# 평균 점수 계산
grade_mean = df_iowa.groupby('District Name').agg(score_mean=('CRB % All Four', 'mean')).reset_index()

# 정규화 함수 정의
def normalize_name(name):
    name = name.upper()
    name = re.sub(r'\s+', ' ', name)  # 다중 공백을 단일 공백으로
    name = re.sub(r'[^A-Z\s]', '', name)  # 알파벳과 공백 제외 모든 문자 제거
    return name.strip()

# GeoJSON 구역 이름 정규화
geojson_areas = {normalize_name(feature['properties']['DistrictName']): feature['properties']['DistrictName'] for feature in geo_iowa['features']}

# DataFrame 구역 이름 정규화
df_iowa['Normalized'] = df_iowa['District Name'].apply(normalize_name)

# 유사도 비교 함수 정의
def find_best_match(name, choices):
    return process.extractOne(name, choices)[0]

# GeoJSON 구역 이름과 DataFrame 구역 이름 매칭
name_mapping = {}
for name in df_iowa['Normalized']:
    best_match = find_best_match(name, geojson_areas.keys())
    name_mapping[name] = geojson_areas[best_match]

# DataFrame의 통일된 구역 이름 적용
df_iowa['Unified District'] = df_iowa['Normalized'].map(name_mapping)

# 통합된 데이터프레임과 GeoJSON 데이터 매칭
grade_mean = df_iowa.groupby('Unified District').agg(score_mean=('CRB % All Four', 'mean')).reset_index()

# Folium 맵 생성
map_iowa = folium.Map(
    location=[42.03, -93.64289689856655],
    zoom_start=12, 
    tiles='cartodbpositron'
)

# Folium Choropleth 추가
folium.Choropleth(
    geo_data=geo_iowa,
    data=grade_mean,
    columns=['Unified District', 'score_mean'],
    key_on='feature.properties.DistrictName',  # GeoJSON의 실제 속성 이름
    fill_color='YlGnBu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Average Score'
).add_to(map_iowa)

# 맵 표시
map_iowa