let step = 1;

let user = {
  age: 0,
  income: 0,
  expenses: 0,
  savings: 0,
  goal: "",
  risk: ""
};


// Easy shortcut for finding an element
function $(id) {
  return document.getElementById(id);
}


// START QUESTIONNAIRE

function startQuestionnaire() {
  $("home").classList.add("hidden");
  document.getElementById("how").classList.add("hidden");
  document.getElementById("features").classList.add("hidden");
  $("questionnaire").classList.remove("hidden");

  window.scrollTo(0, 0);
}


// GO TO NEXT QUESTION

function nextStep() {

  // Save current answer
  if (step == 1) {
    user.age = Number($("age").value);
  }

  if (step == 2) {
    user.income = Number($("income").value);
  }

  if (step == 3) {
    user.expenses = Number($("expenses").value);
  }

  if (step == 4) {
    user.savings = Number($("savings").value);
  }

  // Check number questions
  if (step <= 4 && !getCurrentAnswer()) {
    alert("Please enter your answer.");
    return;
  }

  // Check goal
  if (step == 5 && !user.goal) {
    alert("Please choose a goal.");
    return;
  }

  document.getElementById("step" + step).classList.remove("active");

  step++;

  document.getElementById("step" + step).classList.add("active");

  $("stepText").innerText = "Step " + step + " of 6";

  $("progressBar").style.width = (step / 6) * 100 + "%";
}


// CHECK CURRENT ANSWER

function getCurrentAnswer() {

  if (step == 1) return user.age;
  if (step == 2) return user.income;
  if (step == 3) return user.expenses;
  if (step == 4) return user.savings;

  return true;
}


// SELECT GOAL

function selectGoal(button, goal) {

  document.querySelectorAll("#step5 .options button")
    .forEach(function(btn) {
      btn.classList.remove("selected");
    });

  button.classList.add("selected");

  user.goal = goal;
}


// SELECT RISK

function selectRisk(button, risk) {

  document.querySelectorAll("#step6 .options button")
    .forEach(function(btn) {
      btn.classList.remove("selected");
    });

  button.classList.add("selected");

  user.risk = risk;
}


// CREATE DASHBOARD

function generateDashboard() {

  if (!user.risk) {
    alert("Please choose your risk comfort.");
    return;
  }

  document.getElementById("step6").classList.remove("active");
  $("questionnaire").classList.add("hidden");
  $("dashboard").classList.remove("hidden");

  let balance = user.income - user.expenses;

  // Suggested saving
  let saving = user.income * 0.20;

  if (user.expenses > user.income * 0.70) {
    saving = user.income * 0.10;
  }

  if (balance <= 0) {
    saving = 0;
  }


  // Show money
  $("showIncome").innerText = money(user.income);
  $("showExpenses").innerText = money(user.expenses);
  $("showBalance").innerText = money(balance);
  $("showSaving").innerText = money(saving);


  // Health score
  let score = calculateHealthScore();

  $("healthScore").innerText = score;

  if (score >= 80) {
    $("healthText").innerText =
      "Your finances look healthy.";
  } else if (score >= 50) {
    $("healthText").innerText =
      "You are doing okay, but there is room to improve.";
  } else {
    $("healthText").innerText =
      "Your spending needs some attention.";
  }


  // Recommendations
  showRecommendations(saving);

  window.scrollTo(0, 0);
}


// HEALTH SCORE

function calculateHealthScore() {

  if (user.income <= 0) {
    return 0;
  }

  let expenseRatio = user.expenses / user.income;
  let savingRatio = user.savings / user.income;

  let score = 100;

  if (expenseRatio > 0.70) {
    score -= 25;
  } else if (expenseRatio > 0.50) {
    score -= 10;
  }

  if (savingRatio < 0.10) {
    score -= 15;
  }

  if (user.savings >= user.income * 3) {
    score += 5;
  }

  return Math.max(0, Math.min(100, score));
}


// PERSONALIZED RECOMMENDATIONS

function showRecommendations(saving) {

  let list = $("recommendationsList");

  list.innerHTML = "";

  let recommendations = [];


  if (user.expenses > user.income * 0.70) {
    recommendations.push(
      ["Watch your spending",
       "Your expenses are taking a large part of your income. Try identifying areas where you can reduce unnecessary spending."]
    );
  }


  if (saving > 0) {
    recommendations.push(
      ["Build your savings",
       "A possible starting point is to save around " +
       money(saving) + " each month."]
    );
  }


  if (user.goal == "Start investing") {
    recommendations.push(
      ["Learn before investing",
       "Understand different investment options and choose based on your goals and comfort with risk."]
    );
  }


  if (user.goal == "Build emergency fund") {
    recommendations.push(
      ["Focus on an emergency fund",
       "Build a savings buffer that can help with unexpected expenses."]
    );
  }


  if (user.goal == "Reduce expenses") {
    recommendations.push(
      ["Track your expenses",
       "Look at your regular spending and identify expenses that are not necessary."]
    );
  }


  if (user.goal == "Save more") {
    recommendations.push(
      ["Make saving automatic",
       "Set aside a fixed amount whenever you receive your income."]
    );
  }


  recommendations.forEach(function(item) {

    let div = document.createElement("div");

    div.className = "recommendation";

    div.innerHTML =
      "<strong>" + item[0] + "</strong>" +
      "<p>" + item[1] + "</p>";

    list.appendChild(div);
  });
}


// MONEY FORMAT

function money(number) {
  return "₹" + Number(number).toLocaleString("en-IN");
}


// START AGAIN

function restart() {

  step = 1;

  user = {
    age: 0,
    income: 0,
    expenses: 0,
    savings: 0,
    goal: "",
    risk: ""
  };

  document.querySelectorAll(".question")
    .forEach(function(q) {
      q.classList.remove("active");
    });

  $("step1").classList.add("active");

  $("progressBar").style.width = "16.66%";

  $("stepText").innerText = "Step 1 of 6";

  $("dashboard").classList.add("hidden");
  $("questionnaire").classList.add("hidden");

  $("home").classList.remove("hidden");
  document.getElementById("how").classList.remove("hidden");
  document.getElementById("features").classList.remove("hidden");

  window.scrollTo(0, 0);
}