const tableHead = document.querySelector("#data-head");
const tableBody = document.querySelector("#data-body");
const rowCount = document.querySelector("#row-count");
const chatHistory = document.querySelector("#chat-history");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");

// Convert database column names into readable table headers.
function formatHeader(value) {
  return value.replaceAll("_", " ").toLowerCase();
}

// Build the table headers and rows from API data.
function renderTable(rows) {
  tableHead.replaceChildren();
  tableBody.replaceChildren();

  if (rows.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.className = "loading-cell";
    emptyCell.textContent = "No data found.";
    emptyRow.append(emptyCell);
    tableBody.append(emptyRow);
    rowCount.textContent = "No records found";
    return;
  }

  const columns = Object.keys(rows[0]);

  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = formatHeader(column);
    headerRow.append(th);
  }
  tableHead.append(headerRow);

  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const column of columns) {
      const td = document.createElement("td");
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = row[column] ?? "";
      td.append(cell);
      tr.append(td);
    }
    tableBody.append(tr);
  }

  rowCount.textContent = `Showing 1 to ${rows.length} of ${rows.length}`;
}

// Send the browser to the login page when a request returns 401 Unauthorized.
function redirectIfUnauthorized(response) {
  if (response.status === 401) {
    window.location.href = "/login";
    return true;
  }
  return false;
}

// Disable the chat form when the data is unavailable
function disableChat() {
  chatInput.disabled = true;
  chatInput.placeholder = "Data unavailable — refresh to retry.";
  const submitButton = chatForm.querySelector("button[type='submit']");
  if (submitButton) submitButton.disabled = true;
}

// Fetch data from the API and render it into the table.
async function loadData() {
  try {
    const response = await fetch("/api/data");

    if (redirectIfUnauthorized(response)) {
      return;
    }
    if (!response.ok) {
      throw new Error("Could not load data");
    }

    const payload = await response.json();
    renderTable(payload.data);
  } catch (error) {
    tableBody.innerHTML = '<tr><td class="loading-cell">Unable to load data.</td></tr>';
    rowCount.textContent = "Error";
    disableChat();
  }
}

// Append a question + answer pair to the history and return the
// answer element so the caller can fill it in once the response arrives.
function appendHistoryItem(question) {
  const item = document.createElement("div");
  item.className = "chat-item";

  const questionEl = document.createElement("p");
  questionEl.className = "chat-question";
  questionEl.textContent = question;

  const answerEl = document.createElement("p");
  answerEl.className = "chat-answer-text is-thinking";
  answerEl.textContent = "Thinking...";

  item.append(questionEl, answerEl);
  chatHistory.append(item);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  return answerEl;
}

// Send the user's question to the chat API and fill in the corresponding answer.
async function submitChat(message) {
  const answerEl = appendHistoryItem(message);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (redirectIfUnauthorized(response)) {
      return;
    }
    if (!response.ok) {
      throw new Error("Could not load chat answer");
    }

    const payload = await response.json();
    answerEl.textContent = payload.answer;
  } catch (error) {
    answerEl.textContent = "Unable to answer right now.";
  } finally {
    answerEl.classList.remove("is-thinking");
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  submitChat(message);
  chatInput.value = "";
});

loadData();
