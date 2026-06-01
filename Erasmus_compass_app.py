import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials


CATEGORIES = [
    "Personal achievement development",
    "Financial",
    "Risk",
    "Psychological"
]


def main():
    st.set_page_config(page_title="Erasmus Compass",
                       page_icon="🧭", layout="centered")

    st.title("🧭 Erasmus Compass")
    st.write(
        "A decision-support tool that helps students evaluate whether Erasmus is the right decision."
    )

    st.divider()

    st.subheader("Step 1 — Self-assessment")
    st.write("Rate each statement from 1 to 5.")

    scores = get_survey_scores()
    group_scores = calculate_group_scores(scores)

    st.divider()

    st.subheader("Step 2 — Set your priorities")
    st.write(
        "Distribute importance between the four areas. The total must equal **100**.")

    weights = get_weights()
    total_weight = sum(weights.values())

    st.write(f"Current total weight: **{total_weight} / 100**")

    if total_weight != 100:
        st.warning("Please adjust the weights so the total equals exactly 100.")
        return

    if st.button("Calculate my Erasmus Compass result"):
        expected_utility = calculate_expected_utility(group_scores, weights)
        utility_percentage = (expected_utility / 5) * 100
        recommendation = get_recommendation(utility_percentage)

        show_result(expected_utility, utility_percentage,
                    recommendation, group_scores, weights)

        st.session_state["result_ready"] = True
        st.session_state["expected_utility"] = expected_utility
        st.session_state["utility_percentage"] = utility_percentage
        st.session_state["recommendation"] = recommendation
        st.session_state["group_scores"] = group_scores
        st.session_state["weights"] = weights

    if st.session_state.get("result_ready"):
        show_feedback_form()


def get_survey_scores():
    scores = {}

    scores["growth"] = st.slider(
        "Erasmus will help me grow as a person.",
        1, 5, 3
    )

    scores["career"] = st.slider(
        "Erasmus will improve my future career opportunities.",
        1, 5, 3
    )

    scores["finance"] = st.slider(
        "Erasmus is financially manageable for me.",
        1, 5, 3
    )

    scores["reversibility"] = st.slider(
        "If Erasmus does not go as planned, I can recover from the decision.",
        1, 5, 3
    )

    scores["independence"] = st.slider(
        "I am ready to handle daily life in another country.",
        1, 5, 3
    )

    scores["regret"] = st.slider(
        "I think I would regret not taking this opportunity.",
        1, 5, 3
    )

    scores["emotional"] = st.slider(
        "I feel emotionally ready to live and study abroad.",
        1, 5, 3
    )

    scores["excitement"] = st.slider(
        "When I think about Erasmus, I feel more excited than afraid.",
        1, 5, 3
    )

    return scores


def calculate_group_scores(scores):
    return {
        "Personal achievement development": (scores["growth"] + scores["career"]) / 2,
        "Financial": scores["finance"],
        "Risk": (scores["reversibility"] + scores["independence"]) / 2,
        "Psychological": (
            scores["regret"] + scores["emotional"] + scores["excitement"]
        ) / 3
    }


def get_weights():
    weights = {}

    weights["Personal achievement development"] = st.number_input(
        "Personal achievement development weight",
        min_value=0,
        max_value=100,
        value=25,
        step=1
    )

    weights["Financial"] = st.number_input(
        "Financial weight",
        min_value=0,
        max_value=100,
        value=25,
        step=1
    )

    weights["Risk"] = st.number_input(
        "Risk weight",
        min_value=0,
        max_value=100,
        value=25,
        step=1
    )

    weights["Psychological"] = st.number_input(
        "Psychological weight",
        min_value=0,
        max_value=100,
        value=25,
        step=1
    )

    return weights


def calculate_expected_utility(group_scores, weights):
    total = 0

    for category in group_scores:
        total += group_scores[category] * weights[category]

    return total / 100


def get_recommendation(utility_percentage):
    if utility_percentage >= 85:
        return "Strong recommendation: Go to Erasmus"
    if utility_percentage >= 70:
        return "Positive recommendation: Erasmus is probably worth it"
    if utility_percentage >= 55:
        return "Balanced decision: Think carefully"
    if utility_percentage >= 40:
        return "High uncertainty: Prepare more before deciding"

    return "Not recommended right now"


def show_result(expected_utility, utility_percentage, recommendation, group_scores, weights):
    st.divider()
    st.subheader("Result")

    st.metric("Expected Utility", f"{expected_utility:.2f} / 5")
    st.metric("Decision Score", f"{utility_percentage:.1f}%")

    st.success(recommendation)

    st.subheader("Decision Dimension Scores")

    data = []

    for category in CATEGORIES:
        data.append({
            "Dimension": category,
            "Score / 5": round(group_scores[category], 2),
            "Weight %": weights[category]
        })

    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)

    st.bar_chart(df.set_index("Dimension")["Score / 5"])

    st.subheader("Advanced Analysis")
    analysis_lines = generate_advanced_analysis(
        group_scores, weights, utility_percentage)

    for line in analysis_lines:
        st.write(f"- {line}")


def generate_advanced_analysis(group_scores, weights, utility_percentage):
    analysis = []

    strongest = get_categories_with_max_value(group_scores)
    weakest = get_categories_with_min_value(group_scores)
    highest_priority = get_categories_with_max_value(weights)

    analysis.append("Strongest evaluated area(s): " +
                    ", ".join(strongest) + ".")
    analysis.append("Weakest evaluated area(s): " + ", ".join(weakest) + ".")
    analysis.append("Highest priority area(s): " +
                    ", ".join(highest_priority) + ".")

    if utility_percentage >= 70:
        analysis.append(
            "Overall, your answers suggest that Erasmus has strong expected value for you.")
    elif utility_percentage >= 55:
        analysis.append(
            "Your result suggests a balanced decision. Erasmus may be valuable, but some areas need reflection.")
    else:
        analysis.append(
            "Your result suggests that you may need more preparation or clarity before choosing Erasmus.")

    personal = group_scores["Personal achievement development"]
    financial = group_scores["Financial"]
    risk = group_scores["Risk"]
    psychological = group_scores["Psychological"]

    if personal >= 4 and psychological >= 4:
        analysis.append(
            "You show strong growth motivation and psychological readiness.")
    elif personal >= 4 and psychological < 3:
        analysis.append(
            "You see strong growth potential, but psychological readiness may need attention.")
    elif personal < 3 and psychological >= 4:
        analysis.append(
            "You feel emotionally drawn to Erasmus, but the personal-development value is less clear.")

    if financial < 3:
        analysis.append(
            "Financial readiness is a warning area. Review budget, grants, housing, and living costs.")
    elif financial >= 4:
        analysis.append(
            "Financial readiness appears strong, which reduces practical pressure.")

    if risk < 3:
        analysis.append(
            "Risk resilience is low. A clearer backup plan may improve your confidence.")
    elif risk >= 4:
        analysis.append(
            "Risk resilience appears strong. You seem prepared to handle uncertainty.")

    for category in CATEGORIES:
        if weights[category] >= 30:
            score = group_scores[category]

            if score >= 4:
                analysis.append(
                    f"{category} is highly important to you and also scores strongly. This supports the decision.")
            elif score >= 3:
                analysis.append(
                    f"{category} is highly important to you, but the score is moderate. This area needs reflection.")
            else:
                analysis.append(
                    f"{category} is highly important to you, but currently scores low. This may create internal conflict.")

    return analysis


def get_categories_with_max_value(dictionary):
    max_value = max(dictionary.values())
    categories = []

    for category in dictionary:
        if dictionary[category] == max_value:
            categories.append(category)

    return categories


def get_categories_with_min_value(dictionary):
    min_value = min(dictionary.values())
    categories = []

    for category in dictionary:
        if dictionary[category] == min_value:
            categories.append(category)

    return categories


def show_feedback_form():
    st.divider()
    st.subheader("Help improve Erasmus Compass")

    st.write(
        "This feedback is anonymous and will be used only to improve the project.")

    usefulness_rating = st.slider(
        "How useful was this tool?",
        1, 5, 3
    )

    would_recommend = st.radio(
        "Would you recommend this tool to another student?",
        ["Yes", "No", "Not sure"]
    )

    next_tool = st.text_input(
        "What decision-making tool should be created next?"
    )

    comment = st.text_area(
        "Optional comment"
    )

    if st.button("Submit anonymous feedback"):
        save_feedback(
            usefulness_rating,
            would_recommend,
            next_tool,
            comment
        )


def save_feedback(usefulness_rating, would_recommend, next_tool, comment):
    try:
        worksheet = connect_to_google_sheet()

        group_scores = st.session_state["group_scores"]
        weights = st.session_state["weights"]

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(st.session_state["expected_utility"], 2),
            round(st.session_state["utility_percentage"], 1),
            st.session_state["recommendation"],
            round(group_scores["Personal achievement development"], 2),
            round(group_scores["Financial"], 2),
            round(group_scores["Risk"], 2),
            round(group_scores["Psychological"], 2),
            weights["Personal achievement development"],
            weights["Financial"],
            weights["Risk"],
            weights["Psychological"],
            usefulness_rating,
            would_recommend,
            next_tool,
            comment
        ]

        worksheet.append_row(row)
        st.success("Thank you! Your anonymous feedback was saved.")

    except Exception as e:
        st.error("Feedback could not be saved.")
        st.write("Technical error:")
        st.write(e)


def connect_to_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    sheet = client.open_by_key(st.secrets["google_sheet"]["spreadsheet_id"])

    worksheet = sheet.worksheet("Feedback")

    return worksheet


if __name__ == "__main__":
    main()
