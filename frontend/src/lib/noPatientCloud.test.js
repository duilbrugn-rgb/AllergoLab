const fs = require("fs");
const path = require("path");

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (/\.(js|jsx)$/.test(entry.name) && !entry.name.endsWith(".test.js")) files.push(full);
  }
  return files;
}

describe("frontend privacy contract", () => {
  const files = walk(path.join(__dirname, ".."));

  test("nessuna chiamata a /reports e nessun doctorName nel flusso", () => {
    const hits = files.filter((file) => {
      const text = fs.readFileSync(file, "utf8");
      return text.includes("/reports") || text.includes("doctor_name") || text.includes("doctorName");
    });
    expect(hits).toEqual([]);
  });

  test("nessun salvataggio di dati paziente in storage locale", () => {
    const hits = files.filter((file) => {
      const text = fs.readFileSync(file, "utf8");
      return (
        text.includes("localStorage") ||
        text.includes("sessionStorage") ||
        text.includes("indexedDB")
      );
    });
    expect(hits).toEqual([]);
  });
});
