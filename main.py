from pathlib import Path
from datetime import datetime
import streamlit as st
import altair as alt
import pandas as pd
from data_manipulation import data_cleansing


def get_avg_salary_by_category(df):
    df = df.groupby('種類')['mid_salary'].mean().reset_index()
    df.columns = ['種類', '平均月薪']
    df['平均月薪'] = df['平均月薪'].round(2)
    df.sort_values(by='平均月薪', ascending=False, inplace=True)
    return df.head(10)


def get_avg_salary_by_industry(df):
    df = df.groupby('公司類型')['mid_salary'].mean().reset_index()
    df.columns = ['行業', '平均月薪']
    df['平均月薪'] = df['平均月薪'].round(2)
    df.sort_values(by='平均月薪', ascending=False, inplace=True)
    return df


def get_avg_salary_by_education(df):
    df = df.groupby('學歷')['mid_salary'].mean().reset_index()
    df.columns = ['學歷', '平均月薪']
    df['平均月薪'] = df['平均月薪'].round(2)
    df.sort_values(by='平均月薪', ascending=False, inplace=True)
    return df


def get_avg_salary_by_experience(df):
    df = df.groupby('experience')['mid_salary'].mean().reset_index()
    df.columns = ['年資', '平均月薪']
    df['平均月薪'] = df['平均月薪'].round(2)
    df.sort_values(by='平均月薪', ascending=False, inplace=True)
    return df


def load_data(x):
    latest_file = ''
    latest_time = datetime.min
    for file_path in Path('output').glob('gov_jobs*.csv'):
        file_name = file_path.name
        file_time = datetime.strptime(file_name.split('_')[2].split('.')[0], '%Y%m%d')
        if file_time > latest_time:
            latest_file = file_name
            latest_time = file_time
    if latest_file == '':
        raise Exception("No files found with name containing 'gov_jobs' in /output")
    formatted_date = latest_time.strftime('%Y-%m-%d')
    df = pd.read_csv(f'output/{latest_file}')
    df = data_cleansing(df, x)
    return df, formatted_date


st.set_page_config(page_title='澳門就業市場分析', layout='wide')


st.title('澳門就業市場分析')
st.write('此網站數據來自[本地職位空缺 - 勞工事務局](https://www.dsal.gov.mo/jobseeking/app/#/service)')
x = st.sidebar.slider('你想以多少天計算日薪類職業', max_value=31, value=22)
with st.spinner('Fetching data...'):
    df, latest_time = load_data(x)
    m1, m2, m3, m4 = st.columns((1, 1, 1, 1))
    m2.metric(label='數據更新至', value=latest_time)
    m3.metric(label='所有工作數量', value=f'{len(df)}個')

    select = st.radio(
        "你想以什麼標準查看數據",
        ('工作種類', '行業'), horizontal=True)
    if select == '工作種類':
        categories = df['種類'].unique().tolist()
        # Create a selectbox for the user to choose a category
        selected_category = st.selectbox('選擇一個工作種類', categories)

        # Filter the DataFrame based on the selected category
        filtered_df = df.loc[df['種類'] == selected_category].iloc[:, :-2]
        # Display the filtered DataFrame
        st.dataframe(filtered_df)
    else:
        industries = df['公司類型'].unique().tolist()
        # Create a selectbox for the user to choose a category
        selected_industry = st.selectbox('選擇一個行業', industries)

        # Filter the DataFrame based on the selected category
        filtered_df = df.loc[df['公司類型'] == selected_industry].iloc[:, :-2]
        # Display the filtered DataFrame
        st.dataframe(filtered_df)


col1, col2 = st.columns(2)

with col1:
    st.subheader("澳門前十工種平均薪金")
    # st.caption('_此數據由中間值計算_')
    bar = alt.Chart(get_avg_salary_by_category(df)).mark_bar().encode(x='平均月薪', y="種類")
    st.altair_chart(bar, use_container_width=True, theme='streamlit')

with col2:
    st.subheader("平均薪金分佈圖")
    avg_salary_df = df[df['mid_salary'] < 100000]
    hist = alt.Chart(pd.DataFrame({'salary': avg_salary_df['mid_salary']})).mark_bar().encode(alt.X("salary", bin=alt.Bin(step=2500), title='薪水(不含10萬以上)'), y=alt.Y('count()', title='數量'))
    st.altair_chart(hist, use_container_width=True)


# Create Streamlit columns
col3, col4 = st.columns(2)

# Show average salary by industry
with col3:
    st.subheader("澳門不同行業平均薪金")
    chart = alt.Chart(get_avg_salary_by_industry(df)).mark_bar().encode(x='平均月薪', y="行業")
    st.altair_chart(chart, use_container_width=True)

# Show average salary by education level
with col4:
    st.subheader("澳門不同學歷平均薪金")
    chart = alt.Chart(get_avg_salary_by_education(df)).mark_bar().encode(x='平均月薪', y="學歷")
    st.altair_chart(chart, use_container_width=True)


st.subheader("澳門薪金與工作年資關係")
chart = alt.Chart(df).mark_circle().encode(
    x=alt.X('experience', axis=alt.Axis(format='~g'), title='年資要求'),
    y=alt.Y('mid_salary', axis=alt.Axis(tickCount=8), title='薪金')
).interactive()
st.altair_chart(chart, use_container_width=True)


# hide the footer
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
