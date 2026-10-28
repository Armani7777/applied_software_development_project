const SAMPLE_PAGE = [
  "В работе сравнивают сжатие JPEG и точность детекции.",
  "Авторы пишут, что метрики PSNR и SSIM плохо совпадают с mAP.",
  "Проверка шла на выборке COCO val2017.",
].join("\n");

const CASES = {
  cited: "метрики   PSNR и SSIM плохо совпадают с mAP",
  unchecked: "модель обучали с нуля на ImageNet",
  empty: "   ",
};

const COPY = {
  cited: {
    title: "Цитата на странице есть",
    text: "Фраза нашлась. Поле карточки можно показывать. Лишние пробелы, переносы и регистр я не считаю другой цитатой.",
  },
  unchecked: {
    title: "На этой странице фразы нет",
    text: "Строка в карточке есть, но в тексте этой страницы её нет. Это не пустое поле: в карточке стоит «не проверено», а не «готово».",
  },
  empty: {
    title: "Цитату не вписали",
    text: "В поле пусто или одни пробелы. Так карточку закрывать нельзя. Это другой случай, не «не нашёл».",
  },
};

const form = document.querySelector("#form");
const pageInput = document.querySelector("#page");
const pageText = document.querySelector("#pageText");
const quoteInput = document.querySelector("#quote");
const result = document.querySelector("#result");
const submit = document.querySelector("#submit");
const historyList = document.querySelector("#history");
const historyEmpty = document.querySelector("#historyEmpty");

pageText.value = SAMPLE_PAGE;
quoteInput.value = CASES.cited;

function show(data) {
  const copy = COPY[data.status] || {
    title: "Проверка не запустилась",
    text: data.error || "Не понял ответ.",
  };
  result.hidden = false;
  result.className = "verdict " + data.status;
  document.querySelector("#statusCode").textContent = "стр. " + data.page + " · " + data.status;
  document.querySelector("#statusTitle").textContent = copy.title;
  document.querySelector("#statusText").textContent = copy.text;
  const shown = data.status === "empty" ? "Пустая строка" : quoteInput.value.trim();
  document.querySelector("#shownQuote").textContent = shown;
  const preview = document.querySelector("#preview");
  preview.replaceChildren();
  const text = pageText.value;
  if (data.start != null && data.end != null) {
    const mark = document.createElement("mark");
    mark.textContent = text.slice(data.start, data.end);
    preview.append(
      document.createTextNode(text.slice(0, data.start)),
      mark,
      document.createTextNode(text.slice(data.end)),
    );
  } else if (!text.trim()) {
    preview.textContent = "Текст страницы пустой.";
  } else {
    preview.textContent = text;
  }
  addHistory(data);
  result.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function addHistory(data) {
  historyEmpty.hidden = true;
  const item = document.createElement("li");
  item.className = data.status;
  const snippet = (quoteInput.value.trim() || "пусто").slice(0, 42);
  item.textContent = data.status + " · стр. " + data.page + " · " + snippet;
  historyList.prepend(item);
  while (historyList.children.length > 8) {
    historyList.lastElementChild.remove();
  }
}

async function check() {
  submit.disabled = true;
  try {
    const response = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        page_text: pageText.value,
        quote: quoteInput.value,
        page: pageInput.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      show({ status: "empty", page: pageInput.value, error: data.error });
      return;
    }
    show(data);
  } catch (error) {
    show({
      status: "empty",
      page: pageInput.value,
      error: "Сервер не ответил. Если страница открыта из контейнера, проверьте docker logs.",
    });
  } finally {
    submit.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  check();
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    check();
  }
});

document.querySelector("#fillPage").addEventListener("click", () => {
  pageText.value = SAMPLE_PAGE;
  pageInput.value = "4";
  pageText.focus();
});

document.querySelector("#file").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }
  pageText.value = await file.text();
});

document.querySelectorAll("[data-case]").forEach((button) => {
  button.addEventListener("click", () => {
    pageText.value = SAMPLE_PAGE;
    pageInput.value = "4";
    quoteInput.value = CASES[button.dataset.case];
    check();
  });
});

const demo = new URLSearchParams(location.search).get("demo");
if (CASES[demo]) {
  quoteInput.value = CASES[demo];
  check();
}
