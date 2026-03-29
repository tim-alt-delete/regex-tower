const regexInput = document.getElementById("regex-input");
const submitButton = document.getElementById("submit-button");
const targetList = document.getElementById("target-list");
const avoidList = document.getElementById("avoid-list");

function getRegexFromInput() {
  if (!regexInput.value) return null;
  // console.log("Raw input:", regexInput.value);
  try { return new RegExp(regexInput.value); }
  catch (e) { return null; }
}

function setEmoji(iconEl, emoji) {
  iconEl.textContent = emoji || ""; // empty when no regex
}

function getItemText(li) {
  const icon = li.querySelector('.result-icon');
  const full = li.textContent || "";
  const iconText = icon ? icon.textContent : "";
  return full.replace(iconText, "").trim();
}

function testLists(regex) {
  const targets = Array.from(targetList.children);
  const avoids = Array.from(avoidList.children);
  targets.forEach(li => {
    const icon = li.querySelector('.result-icon');
    if (!icon) return;
    if (!regex) { setEmoji(icon, ""); return; }
    const itemText = getItemText(li);
    setEmoji(icon, regex.test(itemText) ? "✅" : "❌");
  });
  avoids.forEach(li => {
    const icon = li.querySelector('.result-icon');
    if (!icon) return;
    if (!regex) { setEmoji(icon, ""); return; }
    const itemText = getItemText(li);
    setEmoji(icon, regex.test(itemText) ? "❌" : "✅");
  });
}

regexInput.addEventListener("input", () => testLists(getRegexFromInput()));
const form = document.querySelector('form');

document.addEventListener('DOMContentLoaded', function () {
  const hintBtn = document.getElementById('get-hint');
  const hint = document.getElementById('hint');

  hintBtn.addEventListener('click', function () {
    hint.classList.toggle('is-hidden');

    // optional: change button text to allow hiding again
    hintBtn.textContent = hint.classList.contains('is-hidden') ? 'Get hint' : 'Hide hint';
  });
});
