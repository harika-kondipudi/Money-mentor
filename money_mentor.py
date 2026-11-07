# Money Mentor - personal finance learning project
# Run with: streamlit run money_mentor.py

from io import BytesIO

import streamlit as st
import speech_recognition as sr
from gtts import gTTS


st.set_page_config(page_title="Money Mentor", page_icon="💰", layout="wide")

# ---------------- Session state ----------------
DEFAULT_DATA = {
    "age": 20,
    "work": "Student",
    "income": 50000,
    "expenses": 28000,
    "savings": 60000,
    "invest": 30000,
    "debt": 0,
    "emi": 0,
    "risk": "Balanced",
    "health_ins": False,
    "life_ins": False,
}

if "data" not in st.session_state:
    st.session_state.data = DEFAULT_DATA.copy()
if "history" not in st.session_state:
    st.session_state.history = []
if "chat" not in st.session_state:
    st.session_state.chat = [
        ("assistant", "Hi! Ask me about your score, savings, goals or investing.")
    ]
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "speak_text" not in st.session_state:
    st.session_state.speak_text = None

d = st.session_state.data


# ---------------- Calculations ----------------
def rupees(value):
    return "₹" + format(round(value), ",")


def free_money():
    return d["income"] - d["expenses"] - d["emi"]


def months_cover():
    if d["expenses"] <= 0:
        return 0.0
    return d["savings"] / d["expenses"]


def get_score(income, expenses, savings, emi):
    """Financial learning score out of 100: cash-flow/saving (40),
    emergency fund (40), and EMI burden (20).
    This is an illustrative score, not a professional credit score.
    """
    score = 0.0

    if income > 0:
        saving_rate = (income - expenses - emi) / income
        if saving_rate > 0:
            score += min(saving_rate / 0.20, 1.0) * 40

        emi_ratio = emi / income
        if emi_ratio <= 0.10:
            score += 20
        elif emi_ratio < 0.30:
            score += 20 - ((emi_ratio - 0.10) / 0.20) * 20

    if expenses > 0:
        months = max(0, savings) / expenses
        score += min(months / 6, 1.0) * 40

    return max(0, min(100, round(score)))


def my_score():
    return get_score(d["income"], d["expenses"], d["savings"], d["emi"])


def score_name(score):
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Healthy"
    if score >= 45:
        return "Needs attention"
    return "At risk"


def get_stage():
    months = months_cover()

    if months < 1 or free_money() < 0:
        return 1, "Financial Foundation", "Build a small safety net and address overspending."
    if months < 6:
        return 2, "Stability", "Build financial stability before prioritizing investment returns."
    if d["age"] >= 50:
        return 5, "Future Security", "Focus on retirement planning and suitable protection."
    if d["invest"] < d["income"] * 12:
        return 3, "Growth", "Consider investing regularly after essential savings and debts are addressed."
    return 4, "Wealth Building", "Review diversification, costs, and long-term goals."


def make_plan(free, months):
    # This is an illustrative allocation of positive monthly surplus.
    if months < 3:
        parts = [0.50, 0.20, 0.10, 0.20]
        why = "Your emergency fund covers less than 3 months, so safety comes first."
    elif months < 6:
        parts = [0.30, 0.30, 0.25, 0.15]
        why = "Build your safety net while allocating a smaller amount to investing."
    else:
        parts = [0.10, 0.30, 0.45, 0.15]
        why = "Your emergency fund is stronger, so you may be able to direct more toward long-term growth."

    if d["risk"] == "Conservative":
        why += " Since you prefer lower risk, research lower-risk options and their terms."
    elif d["risk"] == "Growth-oriented":
        why += " Growth-oriented investments can fluctuate and may lose value."

    names = ["Emergency Fund", "Goals", "Investment", "Flexible Spending"]
    return {name: max(0, free) * parts[i] for i, name in enumerate(names)}, why


# ---------------- Rule-based chatbot ----------------
def chatbot(question):
    q = question.lower().strip()
    words = q.replace("?", "").replace("!", "").replace(".", "").split()
    free = free_money()
    months = months_cover()

    if any(word in words for word in ("hello", "hi", "hey")):
        return "Hello! Try asking: what is my score, or what should I do with my money?"
    if "score" in q or "financial health" in q:
        score = my_score()
        return f"Your Financial Health Score is {score} out of 100 ({score_name(score)})."
    if "emergency" in q:
        target = d["expenses"] * 6
        return (
            f"Your savings cover {months:.1f} months of expenses. "
            f"A 6-month target based on your entered expenses is {rupees(target)}."
        )
    if "stage" in q or "life stage" in q:
        number, name, advice = get_stage()
        return f"You are in stage {number}, {name}. {advice}"
    if "invest" in q:
        if months < 3:
            return "Consider building an emergency fund first and reviewing high-interest debt before investing."
        return "Consider a regular, diversified, long-term approach that fits your risk tolerance and goals. Returns are not guaranteed."
    if "do with" in q or "plan" in q or "allocate" in q:
        plan, why = make_plan(max(0, free), months)
        items = ", ".join(f"{name}: {rupees(amount)}" for name, amount in plan.items())
        return f"Your estimated monthly surplus is {rupees(max(0, free))}. Suggested illustrative allocation: {items}. {why}"
    if "save" in q or "saving" in q:
        return (
            f"Your estimated amount left each month is {rupees(free)}. "
            f"Saving 20% of your entered income would be {rupees(d['income'] * 0.20)} per month, if affordable."
        )
    if "debt" in q or "emi" in q or "loan" in q:
        if d["income"] <= 0:
            return "Enter a monthly income greater than zero on the Assessment page to calculate your EMI ratio."
        ratio = d["emi"] / d["income"] * 100
        return f"Your monthly EMI is {ratio:.1f}% of your entered income. Review affordability alongside essential expenses and other debts."
    if "insurance" in q or "protect" in q:
        return "Check the Protection page. Consider emergency savings and suitable health/life protection based on your circumstances."
    if "tax" in q:
        return "Tax rules can change. Check the official Income Tax Department website or consult a qualified tax professional."
    return "I can help with: score, emergency fund, saving, investing, debt, stage, insurance, tax, or 'what should I do with my money'."


# ---------------- Voice helpers ----------------
def listen(audio_bytes):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except (sr.UnknownValueError, sr.RequestError, ValueError, OSError):
        st.warning("Sorry, I couldn't understand that recording. Check the audio/internet connection and try again.")
        return None


def speak(text):
    try:
        spoken_text = text.replace("₹", "rupees ")
        mp3 = BytesIO()
        gTTS(spoken_text, lang="en").write_to_fp(mp3)
        mp3.seek(0)
        st.audio(mp3, format="audio/mp3")
    except Exception:
        st.warning("Voice replies need an internet connection and the gTTS package.")


def ask(question):
    answer = chatbot(question)
    st.session_state.chat.append(("user", question))
    st.session_state.chat.append(("assistant", answer))
    st.session_state.speak_text = answer


# ---------------- Navigation ----------------
st.sidebar.title("💰 Money Mentor")
page = st.sidebar.radio(
    "Go to",
    [
        "Home", "Assessment", "Dashboard", "AI Money Plan", "Goal Planner",
        "What-If", "Analytics", "Protection", "Life Stage", "Chatbot & Voice",
    ],
)
st.sidebar.caption("Learning project. Not professional financial advice.")


# ================= HOME =================
if page == "Home":
    st.title("Track less. Decide better. Grow smarter.")
    st.write("Most money apps tell you where your money went.")
    st.write("**But the harder question is: what should I do with my money next?**")
    st.write("1. Fill the **Assessment**.")
    st.write("2. Review your **Dashboard** and **AI Money Plan**.")
    st.write("3. Plan goals, try **What-If**, or talk to the **Chatbot**.")


# ================= ASSESSMENT =================
elif page == "Assessment":
    st.title("Financial Assessment")
    st.subheader("Step 1 — About you")
    d["age"] = st.number_input("Age", min_value=16, max_value=90, value=int(d["age"]))
    work_list = ["Student", "Working", "Business", "Other"]
    d["work"] = st.selectbox("You are a", work_list, index=work_list.index(d["work"]))
    d["income"] = st.number_input("Monthly income (₹)", 0, 10_000_000, int(d["income"]), 1000)

    st.subheader("Step 2 — Your money")
    d["expenses"] = st.number_input("Monthly expenses (₹)", 0, 10_000_000, int(d["expenses"]), 500)
    d["savings"] = st.number_input("Current savings (₹)", 0, 100_000_000, int(d["savings"]), 1000)
    d["invest"] = st.number_input("Current investments (₹)", 0, 100_000_000, int(d["invest"]), 1000)
    d["debt"] = st.number_input("Total debt (₹)", 0, 100_000_000, int(d["debt"]), 1000)
    d["emi"] = st.number_input("Monthly EMIs (₹)", 0, 10_000_000, int(d["emi"]), 500)

    st.subheader("Step 3 — Protection")
    d["health_ins"] = st.checkbox("I have health insurance", value=d["health_ins"])
    d["life_ins"] = st.checkbox("I have life insurance", value=d["life_ins"])

    st.subheader("Step 4 — Risk preference")
    risk_list = ["Conservative", "Balanced", "Growth-oriented"]
    d["risk"] = st.radio("Choose one", risk_list, index=risk_list.index(d["risk"]), horizontal=True)
    st.caption("Goals are set on the Goal Planner page.")

    if st.button("Save and calculate my score"):
        st.session_state.history.append(my_score())
        st.success(f"Saved! Your score is {my_score()}/100. Open the Dashboard.")


# ================= DASHBOARD =================
elif page == "Dashboard":
    st.title("Here's what your money is telling you today.")
    score = my_score()
    st.metric("Financial Health", f"{score} / 100", score_name(score), delta_color="off")
    st.progress(score / 100)

    st.subheader("Money snapshot")
    c1, c2 = st.columns(2)
    c1.metric("Monthly income", rupees(d["income"]))
    c2.metric("Expenses + EMIs", rupees(d["expenses"] + d["emi"]))
    c1.metric("Available each month", rupees(free_money()))
    c2.metric("Current savings", rupees(d["savings"]))

    st.subheader("Your strengths")
    found_strength = False
    if d["income"] > 0 and free_money() >= d["income"] * 0.20:
        st.write("✅ Savings capacity is at least 20% of income.")
        found_strength = True
    if d["income"] > 0 and d["expenses"] <= d["income"] * 0.60:
        st.write("✅ Expenses are at or below 60% of income.")
        found_strength = True
    if months_cover() >= 6:
        st.write("✅ Strong emergency fund based on entered expenses.")
        found_strength = True
    if not found_strength:
        st.write("Add your financial details and review the recommendations below.")

    st.subheader("Needs attention")
    if months_cover() < 6:
        st.write(f"⚠️ Emergency fund: {months_cover():.1f} months of expenses.")
    if d["income"] > 0 and d["emi"] > d["income"] * 0.30:
        st.write("⚠️ EMIs exceed 30% of entered income.")
    if free_money() < 0:
        st.write("⚠️ Spending and EMIs exceed monthly income.")

    st.subheader("Income vs expenses")
    st.bar_chart({
        "Income": d["income"],
        "Expenses + EMIs": d["expenses"] + d["emi"],
        "Available": max(0, free_money()),
    })


# ================= AI MONEY PLAN =================
elif page == "AI Money Plan":
    free = max(0, free_money())
    st.title(f"What could I do with {rupees(free)} this month?")
    if free_money() < 0:
        st.warning("Your expenses and EMIs exceed income. This plan is set to ₹0 until you review your cash flow.")
    plan, why = make_plan(free, months_cover())
    for name, amount in plan.items():
        st.write(f"**{name}:** {rupees(amount)}")
    st.bar_chart(plan)
    st.subheader("Why this recommendation?")
    st.info(f"Your emergency fund covers about {months_cover():.1f} months of expenses. {why}")
    st.write("Current life-stage advice: " + get_stage()[2])


# ================= GOAL PLANNER =================
elif page == "Goal Planner":
    st.title("Goal Planner")
    goal_name = st.text_input("Goal (Laptop, Phone, Car, House, Travel, Education...)", "Laptop")
    cost = st.number_input("Goal amount (₹)", 1, 100_000_000, 100_000, 5000)
    saved = st.number_input("Saved so far (₹)", 0, 100_000_000, 32_000, 1000)
    months_left = st.number_input("Months left", 1, 600, 8)
    now = st.number_input("Saving for it each month now (₹)", 0, 10_000_000, 7500, 500)

    remaining = max(0, cost - saved)
    needed = remaining / months_left
    progress = min(1.0, saved / cost)
    st.metric("Remaining", rupees(remaining))
    st.metric("Required per month", rupees(needed))
    st.progress(progress, text=f"{progress * 100:.0f}% complete")

    if remaining == 0:
        st.success(f"Your {goal_name} goal is fully funded based on the amount entered.")
    elif now >= needed:
        st.success(f"You are on track for your {goal_name} goal.")
    elif needed <= max(0, free_money()):
        st.warning(f"You currently save {rupees(now)}. Consider increasing it by {rupees(needed - now)} or extending the target date.")
    else:
        st.error("This goal needs more than your estimated monthly surplus. Choose a later date or a smaller goal.")


# ================= WHAT-IF =================
elif page == "What-If":
    st.title("What do you want to simulate?")
    choice = st.selectbox(
        "Pick one",
        ["Buy something expensive", "Lose my job", "Increase my investment", "Income increases"],
    )
    income = d["income"]
    expenses = d["expenses"]
    savings = d["savings"]
    emi = d["emi"]

    if choice == "Buy something expensive":
        price = st.number_input("Purchase price (₹)", 0, 10_000_000, 100_000, 5000)
        savings = max(0, savings - price)
    elif choice == "Lose my job":
        months_off = st.slider("Months without income", 1, 12, 3)
        savings = max(0, savings - (expenses + emi) * months_off)
        income = 0
    elif choice == "Increase my investment":
        extra = st.number_input("Extra monthly investment (₹)", 0, 1_000_000, 3000, 500)
        expenses += extra
    else:
        extra = st.number_input("Extra income per month (₹)", 0, 1_000_000, 10_000, 1000)
        income += extra

    old_score = my_score()
    new_score = get_score(income, expenses, savings, emi)
    old_months = months_cover()
    new_months = savings / expenses if expenses > 0 else 0

    c1, c2 = st.columns(2)
    c1.subheader("Now")
    c1.metric("Score", old_score)
    c1.metric("Emergency cover", f"{old_months:.1f} months")
    c2.subheader("After decision")
    c2.metric("Score", new_score, new_score - old_score)
    c2.metric("Emergency cover", f"{new_months:.1f} months", round(new_months - old_months, 1))

    if new_months < 3 and new_months < old_months:
        st.warning("This decision may reduce your emergency-fund safety.")
    elif income - expenses - emi < 0:
        st.warning("You would spend more than you earn each month.")
    elif new_score > old_score:
        st.success("This scenario improves the illustrative financial score.")
    else:
        st.info("This scenario has a small or neutral effect on the illustrative score.")


# ================= ANALYTICS =================
elif page == "Analytics":
    st.title("Financial Analytics")
    st.caption("Past months are estimated from your current numbers; no bank data is connected.")

    st.subheader("1. Cash flow (illustrative 6-month view)")
    income_factors = [0.98, 1.00, 1.00, 1.02, 1.00, 1.00]
    spend_factors = [1.06, 0.97, 1.03, 0.95, 1.02, 1.00]
    income_list = [d["income"] * factor for factor in income_factors]
    expense_list = [(d["expenses"] + d["emi"]) * factor for factor in spend_factors]
    st.line_chart({"Income": income_list, "Expenses + EMIs": expense_list})

    st.subheader("2. Needs vs wants vs growth (estimated)")
    needs = d["expenses"] * 0.70 + d["emi"]
    wants = d["expenses"] * 0.30
    growth = max(0, free_money())
    st.bar_chart({"Needs (estimated)": needs, "Wants (estimated)": wants, "Available for goals": growth})

    st.subheader("3. Financial health trend")
    if len(st.session_state.history) >= 2:
        st.line_chart(st.session_state.history)
    else:
        score = my_score()
        st.line_chart([max(0, score - 14), max(0, score - 9), max(0, score - 4), score])
        st.caption("Example trend only. Save assessments over time to build a history.")
    st.info("This score is an educational estimate, not a bank, credit, or investment rating.")


# ================= PROTECTION =================
elif page == "Protection":
    st.title("Financial Protection")
    st.subheader("Debt")
    ratio = (d["emi"] / d["income"] * 100) if d["income"] > 0 else 0
    st.write("Outstanding debt: " + rupees(d["debt"]))
    st.write(f"EMI burden: {rupees(d['emi'])} ({ratio:.1f}% of income)")
    if ratio > 35:
        st.error("EMI burden is high relative to the entered income.")
    elif ratio > 20:
        st.warning("Keep a close watch on your EMI burden.")
    else:
        st.success("EMI burden is within the app's simple guideline.")
    st.write("Compare interest rates, fees, and terms when reviewing debt repayment options.")

    st.subheader("Emergency fund")
    st.write("Current savings: " + rupees(d["savings"]))
    st.write("Illustrative 6-month target: " + rupees(d["expenses"] * 6))
    st.write(f"Months covered: {months_cover():.1f}")

    st.subheader("Protection check")
    st.write("✅ Emergency fund looks on target." if months_cover() >= 6 else "⚠️ Emergency fund may need attention.")
    st.write("✅ Health coverage recorded." if d["health_ins"] else "⚠️ No health insurance recorded.")
    st.write("✅ Life coverage recorded." if d["life_ins"] else "⚠️ No life insurance recorded (relevance depends on dependants and circumstances).")
    st.caption("This page points out possible gaps; it does not recommend insurers or guarantee results.")


# ================= LIFE STAGE =================
elif page == "Life Stage":
    st.title("Financial Journey")
    number, name, advice = get_stage()
    st.info(f"{name}: {advice}")
    stages = ["Financial Foundation", "Stability", "Growth", "Wealth Building", "Future Security"]
    for i, stage in enumerate(stages, start=1):
        if i == number:
            st.success(f"Stage {i} — {stage} ← you are here")
        else:
            st.write(f"Stage {i} — {stage}")


# ================= CHATBOT & VOICE =================
else:
    st.title("🤖 Money Mentor Chatbot")
    read_aloud = st.checkbox("🔊 Read new answers aloud", value=True)

    audio = st.audio_input("🎤 Record your question")
    if audio is not None:
        audio_bytes = audio.getvalue()
        audio_id = hash(audio_bytes)
        if audio_id != st.session_state.last_audio:
            st.session_state.last_audio = audio_id
            heard = listen(audio_bytes)
            if heard:
                ask(heard)

    typed = st.chat_input("Or type your question here...")
    if typed:
        ask(typed)

    for who, message in st.session_state.chat:
        with st.chat_message(who):
            st.write(message)

    # Speak only when a new answer has been queued.
    pending_speech = st.session_state.speak_text
    st.session_state.speak_text = None
    if pending_speech and read_aloud:
        speak(pending_speech)
