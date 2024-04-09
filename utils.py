import json

import altair as alt
import pandas as pd
import streamlit as st

# Создаем интерактивный график по общим баллам - интервалы по оси X
@st.cache_data
def plot_graph_bin(email_data):

    hist_email = (
        alt.Chart(email_data)
        .mark_bar()
        .encode(
            alt.X(
                "Overall_score:Q",
                bin=alt.Bin(extent=[0, 6], step=1),
                title="Общий балл",
            ),
            alt.Y("count():Q", title="Количество"),
            color=alt.value("lightblue"),
        )
        .interactive()
    )

    st.altair_chart(hist_email, use_container_width=True)


# Создаем интерактивный график по общим баллам в процентном соотношении
@st.cache_data
def plot_graph_bin_percent(email_data):

    email_data = email_data.groupby("Overall_score").size().reset_index(name="total")
    email_data["Percent"] = (
        (email_data["total"] / email_data["total"].sum()) * 100
    ).round(2)

    hist_email = (
        alt.Chart(email_data)
        .mark_bar()
        .encode(
            alt.X("Overall_score:O", title="Общий балл"),
            alt.Y("Percent:Q", title="Процент, %"),
            color=alt.value("lightblue"),
        )
        .configure_axis(labelAngle=0)
        .interactive()
    )

    st.altair_chart(hist_email, use_container_width=True)


# Создаем интерактивный график по общим баллам
@st.cache_data
def plot_graph_bin_x_good(email_data):

    hist_email = (
        alt.Chart(email_data)
        .mark_bar(size=50)
        .encode(
            alt.X("Overall_score:Q", bin=False, title="Общий балл"),
            alt.Y("count():Q", title="Количество"),
            color=alt.value("lightblue"),
        )
        .interactive()
    )

    st.altair_chart(hist_email, use_container_width=True)


# Создаем интерактивный круговой график по баллам для критериев
@st.cache_data
def draw_pie_chart(email_data, selected_criterion) -> None:

    score_3_data = email_data.loc[
        :,
        [
            "Solving a communicative task",
            "Text structure",
            "Use of English (for emails)",
        ],
    ]
    df_score_3_data = pd.melt(score_3_data, var_name="Criterion", value_name="Score")

    filtered_df = df_score_3_data[df_score_3_data["Criterion"] == selected_criterion]
    total_counts = filtered_df.groupby("Score").size().reset_index(name="total")

    df_merged = pd.merge(filtered_df, total_counts, on="Score")
    df_merged = df_merged.groupby("Score").size().reset_index(name="count")
    df_merged["Percent"] = (
        (df_merged["count"] / df_merged["count"].sum()) * 100
    ).round(2)

    if selected_criterion == "Solving a communicative task":
        value_text = "K1"
        color = alt.Color(
            "Score:N", scale=alt.Scale(scheme="set2"), title="Баллы", legend=None
        )
    elif selected_criterion == "Text structure":
        value_text = "K2"
        color = alt.Color(
            "Score:N", scale=alt.Scale(scheme="set2"), title="Баллы", legend=None
        )
    elif selected_criterion == "Use of English (for emails)":
        value_text = "K3"
        color = alt.Color("Score:N", scale=alt.Scale(scheme="set2"), title="Баллы")

    chart = (
        alt.Chart(df_merged)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("Percent", stack="normalize", title="Процент"), color=color
        )
        .properties(height=250)
    )

    text = (
        alt.Chart(df_merged)
        .mark_text()
        .encode(
            text=alt.value(value_text), color=alt.value("lightblue"), size=alt.value(24)
        )
    )

    chart_with_text = chart + text
    chart_with_text.configure_legend(title=None)

    st.altair_chart(chart_with_text, use_container_width=True)


# Кнопка для скачивания результата
def download_button(object_to_download, button_text, key):
    download_key = f"download_button_{key}"

    st.download_button(data=object_to_download, label=button_text, key=download_key)


# Считываем вопросы из json
def open_json_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as json_file:
        questions_in_dict = json.load(json_file)

    # Возвращаем только значения (вопросы), игнорируя ключи
    questions = list(questions_in_dict.values())

    return questions