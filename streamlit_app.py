import streamlit as st
import json
import httpx
import pandas as pd
import altair as alt
import time
import asyncio

file_path = "top_3_questions.json"
data_path = "Data_old.xlsx"
data_path_full = "Data_new.xlsx"

email_data = pd.read_excel(data_path)
scores_email = email_data['Overall_score']
scores_email = pd.DataFrame({'Overall_score': scores_email})

email_data_full = pd.read_excel(data_path_full)
scores_email_full = email_data_full['Overall_score']
scores_email_full = pd.DataFrame({'Overall_score': scores_email_full})

st.set_page_config(layout="wide",
                   page_title='AutoGrade eng writing ЕГЭ',
                   page_icon=":sunglasses:"
                   )

@st.cache_data
def plot_graph_bin(email_data):

    # Create an interactive histogram for email scores
    hist_email = alt.Chart(email_data).mark_bar().encode(
        alt.X('Overall_score:Q', bin=alt.Bin(extent=[0, 6], step=1), title='Общий балл'),
        alt.Y('count():Q', title='Количество'),
        color=alt.value('lightblue')
    ).interactive()

    # Display the interactive histograms side by side
    st.altair_chart(hist_email, use_container_width=True)


@st.cache_data
def plot_graph_bin_percent(email_data):

    email_data = email_data.groupby('Overall_score').size().reset_index(name='total')
    email_data['Percent'] = ((email_data['total'] / email_data['total'].sum()) * 100).round(2)

    hist_email = alt.Chart(email_data).mark_bar().encode(
        alt.X('Overall_score:O',  title='Общий балл'),
        alt.Y('Percent:Q', title='Процент, %'),
        color=alt.value('lightblue')
    ).configure_axis(
        labelAngle=0
    ).interactive()

    # Display the interactive histograms side by side
    st.altair_chart(hist_email, use_container_width=True)


@st.cache_data
def plot_graph_bin_x_good(email_data):

    # Create an interactive histogram for email scores
    hist_email = alt.Chart(email_data).mark_bar(size=50).encode(
        alt.X('Overall_score:Q', bin=False, title='Общий балл'),
        alt.Y('count():Q', title='Количество'),
        color=alt.value('lightblue')
    ).interactive()

    # Display the interactive histograms side by side
    st.altair_chart(hist_email, use_container_width=True)


@st.cache_data
def draw_pie_chart(email_data, selected_criterion) -> None:

    score_3_data = email_data.loc[:, ['Solving a communicative task', 'Text structure', 'Use of English (for emails)']]
    df_score_3_data = pd.melt(score_3_data, var_name='Criterion', value_name='Score')

    filtered_df = df_score_3_data[df_score_3_data['Criterion'] == selected_criterion]
    total_counts = filtered_df.groupby('Score').size().reset_index(name='total')

    df_merged = pd.merge(filtered_df, total_counts, on='Score')
    df_merged = df_merged.groupby('Score').size().reset_index(name='count')
    df_merged['Percent'] = ((df_merged['count'] / df_merged['count'].sum()) * 100).round(2)

    if selected_criterion == "Solving a communicative task":
        value_text = "K1"
        color = alt.Color("Score:N", scale=alt.Scale(scheme='set2'), title='Баллы', legend=None)
    elif selected_criterion == "Text structure":
        value_text = "K2"
        color = alt.Color("Score:N", scale=alt.Scale(scheme='set2'), title='Баллы', legend=None)
    elif selected_criterion == "Use of English (for emails)":
        value_text = "K3"
        color = alt.Color("Score:N", scale=alt.Scale(scheme='set2'), title='Баллы')

    chart = alt.Chart(df_merged).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("Percent", stack='normalize', title="Процент"),
        color=color
    ).properties(height=250)

    text = alt.Chart(df_merged).mark_text().encode(
        text=alt.value(value_text),
        color=alt.value('lightblue'),
        size=alt.value(24)
    )

    chart_with_text = chart + text
    chart_with_text.configure_legend(title=None)

    st.altair_chart(chart_with_text, use_container_width=True)


def download_button(object_to_download, download_filename, button_text, key):
    # Добавляем временный ключ, чтобы кнопка обновлялась при каждом нажатии
    download_key = f"download_button_{key}"

    # Генерируем уникальный идентификатор для кнопки
    st.download_button(
        data=object_to_download,
        label=button_text,
        key=download_key
    )


def open_json_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as json_file:
        questions_in_dict = json.load(json_file)

    questions = []
    for key, value in questions_in_dict.items():
        questions.append(value)

    return questions

async def send_request(selected_question, user_input):
    # URL FastAPI-сервера
    fast_api_url = "https://stunning-star-octopus.ngrok-free.app/predict"

    data = {
        "data": {
            "Question": selected_question,
            "Text": user_input
        }
    }

    # Засекаем время начала запроса
    start_time = time.time()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(fast_api_url, json=data)

    # Засекаем время окончания запроса
    end_time = time.time()

    # Вывод времени запроса
    duration = end_time - start_time

    if response.status_code == 200:
        return response.json(), duration
    else:
        return {"error": f"HTTP Error {response.status_code}: {response.text}"}, duration

# Главная функция Streamlit
async def main():
    st.title("Автоматическое оценивание письма на английском по критериям ЕГЭ")

    # Боковая панель для вкладок
    tab1, tab2, tab3 = st.tabs([
        "# **Краткий экскурс**",
        "# **Анализ данных**",
        "# **Предсказание**"
    ])

    with tab1:
        col1, col2, col3 = st.columns((4, 0.3, 3))
        with col1:
            st.write('Письмо ЕГЭ по английскому языку — одно из заданий '
                     'с развернутым ответом письменной части экзамена. Данное задание содержит отрывок письма '
                     'от друга по переписке. Предлагается написать ответ '
                     'с соблюдением определенных критериев.')
            st.write('Письмо, чтобы организовать его логически и выразить свои мысли последовательно, '
                     'следует структурировать в соответствии со следующей структурой: \n'
                     '- Введение, включающее обращение к адресату; \n'
                     '- Выражение благодарности или других соответствующих чувств; \n'
                     '- Основная часть, где развиваются основные мысли и идеи; \n'
                     '- Завершение с выражением надежды на будущие контакты; \n'
                     '- Завершающая фраза, заключительные слова или пожелания; \n'
                     '- Подпись, завершающая часть письма. \n')
            st.write('Для оценки письма используются три критерия: \n'
                     '1) К1 - Решение коммуникативной задачи (даны ответы + заданы вопросы + вежливость и стиль); \n'
                     '2) К2 - Организация текста (количество абзацев + логичность); \n'
                     '3) К3 - Языковое оформление текста (грамматика + лексика + пунктуация).')
            st.write('По каждому критерию выставляется от 0 до 2 баллов. '
                     'В общей сумме можно получить максимум 6 баллов.')
            st.write('Более подробно по критерии: https://disk.yandex.ru/i/3pNnqUuh3D887w')
            st.write('Наше приложение Streamlit предлагает оценить ваш письменный ответ по английскому языку '
                     'по критериям ЕГЭ во вкладке "Предсказание". '
                     'Оценка по трем критериям, каждый из которых может принести от 0 до 2 баллов, '
                     'с максимальным общим баллом в 6 + комментарии по работе.')


    with tab2:

        col1_1, col1_2, col1_3, col1_4 = st.columns((1, 1.8, 0.03, 0.7))

        with col1_1:
            on = st.toggle('Синтетические данные')
            st.markdown('')
            st.write(f"- Без сгенерированных данных преобладают работы "
                     f"с наивысшим баллом (6 баллов) с большим отрывом. "
                     f"Малое количество работ с баллами меньше 4;")
            st.write(f"- Добавление сгенерированных данных способствовало "
                     f"более равномерному распределению между оценками 4 и 5 баллов "
                     f"с небольшим отрывом от работ в 6 баллов. "
                     f"По-прежнему малое количество работ с баллами меньше 4.")
            st.write(f"Добавление синтетических данных (с использованием OpenAI API) "
                     f"позволило сделать распределение общих оценок "
                     f"в интервале от 4 до 6 более равномерным, однако для низких оценок общая картина распределения"
                     f" не изменилась. "
                     f"Стоит отметить, что сгенерированные данные в большей степени "
                     f"имеют отношение к критерию РКЗ (К1), целью создания которых было улучшение распределения по "
                     f"данному критерию для дальнейшего обучения модели.")

        if on:
            with col1_2:
                st.subheader('Общее число баллов за письмо')

                genre = st.radio("**Выберите график**",
                                 ["Количественное соотношение",
                                  "Количественное соотношение (интервалы по оси X)",
                                  "Процентное соотношение"])

                if genre == "Количественное соотношение (интервалы по оси X)":
                    plot_graph_bin(scores_email_full)
                elif genre == "Количественное соотношение":
                    plot_graph_bin_x_good(scores_email_full)
                elif genre == "Процентное соотношение":
                    plot_graph_bin_percent(scores_email_full)

            with col1_4:
                st.markdown('')
                st.markdown('')
                st.markdown('')
                st.write(f"**Количество писем: {len(email_data_full['Text'])} (514 - новые)**")
                st.write(f"**Количество уникальных заданий: {109}**")
                st.write(f"**Топ-5 заданий по повторяемости:**")
                st.markdown(f"1) Question_id(70) - 111 - Household chores")
                st.markdown(f"2) Question_id(63) -  87 - Camping")
                st.markdown(f"3) Question_id(73) -  83 - Shopping")
                st.markdown(f"4) Question_id(71) -  80 - Environmental issues")
                st.markdown(f"5) Question_id(72) -  73 - Friends")
                st.markdown(f"*ID задания - Количество - Тема задания")


            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.subheader('Решение коммуникативной задачи')
                draw_pie_chart(email_data_full, 'Solving a communicative task')
                st.markdown("- После добавления новых данных распределение стало ближе к равномерному: "
                            "2 балла - 38%, 1 балл - 35%, 0 баллов - 27%")

            with col2_2:
                st.subheader('Организация текста')
                draw_pie_chart(email_data_full, 'Text structure')
                st.markdown("- Распределение по баллам неравномерное - преобладание оценки в 2 балла (87 %): "
                            "2 балла - 94%, 1 балл - 5%, 0 баллов - 1%")

            with col2_3:
                st.subheader('Языковое оформление текста')
                draw_pie_chart(email_data_full, 'Use of English (for emails)')
                st.markdown("- Распределение по баллам неравномерное - преобладание оценки в 2 балла (65 %): "
                            "2 балла - 84%, 1 балл - 12%, 0 баллов - 5%")

        else:
            with col1_4:
                st.markdown('')
                st.markdown('')
                st.markdown('')
                st.write(f"**Количество писем: {len(email_data['Text'])}**")
                st.write(f"**Количество уникальных заданий: {109}**")
                st.write(f"**Топ-5 заданий по повторяемости:**")
                st.markdown(f"1) Question_id(31) - 57 - Household chores")
                st.markdown(f"2) Question_id(37) - 56 - Grandparents")
                st.markdown(f"3) Question_id(28) - 56 - Dreams")
                st.markdown(f"4) Question_id(25) - 56 - Friends")
                st.markdown(f"5) Question_id(38) - 45 - Family")
                st.markdown(f"*ID задания - Количество - Тема задания")

            with col1_2:
                st.subheader('Общее число баллов за письмо')

                genre = st.radio("**Выберите график**",
                                 ["Количественное соотношение",
                                   "Количественное соотношение (интервалы по оси X)",
                                   "Процентное соотношение"] )

                if genre == "Количественное соотношение (интервалы по оси X)":
                    plot_graph_bin(scores_email)
                elif genre == "Количественное соотношение":
                    plot_graph_bin_x_good(scores_email)
                elif genre == "Процентное соотношение":
                    plot_graph_bin_percent(scores_email)

            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.subheader('Решение коммуникативной задачи')
                draw_pie_chart(email_data, 'Solving a communicative task')
                st.markdown("- Распределение по баллам неравномерное - преобладание оценки в 2 балла (81%) "
                            "и околонулевой процент для 0: "
                            "1 балл - 18%, 0 баллов - 1%")

            with col2_2:
                st.subheader('Организация текста')
                draw_pie_chart(email_data, 'Text structure')
                st.markdown("- Распределение по баллам неравномерное - преобладание оценки в 2 балла (87%): "
                            "и околонулевой процент для 0: "
                            "1 балл - 11%, 0 баллов - 2%")

            with col2_3:
                st.subheader('Языковое оформление текста')
                draw_pie_chart(email_data, 'Use of English (for emails)')
                st.markdown("- Распределение по баллам неравномерное (но лучшее среди всех) "
                            "- преобладание оценки в 2 балла (65%): "
                            "1 балл - 25%, 0 баллов - 10%")

        # Переходим на вторую вкладку
        with tab3:
            col1, col2, col3 = st.columns(3)
            with col3:
                st.write("##### **Результат:**")
            with col1:
                selected_question = st.selectbox("##### **Выберите задание:**",
                                                 open_json_questions(file_path), placeholder='')

                # Поле ввода текста
                user_input = st.text_area("##### **Введите текст:**", height=200)

                # Соединение входных данных
                input_data = f"\n\n**Selected Question:** {selected_question}\n\n**User Input:**\n{user_input}"
                # Обработка текста по кнопке
                if st.button("Предсказать"):
                    with st.spinner('Пожалуйста, подождите...'):
                        with col3:
                            if user_input:
                                # Вызов функции обработки текста
                                result, time_req = await send_request(selected_question, user_input)
                                # Вывод результата
                                formatted_result = (
                                    f"**Общий балл:** {result['total']} из 6 баллов \n "
                                    f"**K1 (Решение коммуникативной задачи):** {result['k1']} из 2 баллов \n "
                                    f"**K2 (Организация текста):** {result['k2']} из 2 баллов \n "
                                    f"**K3 (Языковое оформление текста):** {result['k3']} из 2 баллов \n "
                                    f"**Комментарии:** \n {result['comments']}"
                                )
                                # Если есть ошибка, выводим ее
                                if "error" in result:
                                    st.error(result["error"])
                                else:
                                    with col1:
                                        st.success(f"Успешно! Время обработки: {round(time_req, 1)} с")

                                    formatted_result = formatted_result.replace('\n', '<br>')
                                    st.markdown(f"""{formatted_result}""", unsafe_allow_html=True)
                                    download_data = f"{input_data}\n\n{formatted_result}"
                                    # Кнопка для скачивания ответа в текстовом формате
                                    download_button(
                                        object_to_download=download_data,
                                        download_filename="result.txt",
                                        button_text="Скачать ответ (txt)",
                                        key=1
                                    )
                            else:
                                st.warning("Введите текст для обработки.")

            # Отображаем то, что ввел пользователь
            with col2:
                st.markdown("##### **Задание:**")
                st.write(selected_question)
                st.markdown("")
                st.markdown("##### **Ваш ответ:**")
                st.write(user_input)

if __name__ == '__main__':
    asyncio.run(main())
