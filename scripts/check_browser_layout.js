// Evaluate through agent-browser `eval --stdin` after setting each QA viewport.
(() => {
  const controls = [...document.querySelectorAll("button,a,input,textarea")];
  const undersized = controls.flatMap((element) => {
    const rect = element.getBoundingClientRect();
    if (!rect.width || !rect.height) return [];
    return rect.width < 44 || rect.height < 44
      ? [{ text: element.textContent.trim().slice(0, 60), width: rect.width, height: rect.height }]
      : [];
  });
  const result = {
    viewport: [innerWidth, innerHeight],
    scrollWidth: document.documentElement.scrollWidth,
    noHorizontalScroll: document.documentElement.scrollWidth <= innerWidth,
    undersized,
  };
  if (!result.noHorizontalScroll || undersized.length) {
    throw new Error(JSON.stringify(result));
  }
  return result;
})()
