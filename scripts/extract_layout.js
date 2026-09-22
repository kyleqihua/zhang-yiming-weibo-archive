const fs = require("fs");
const path = require("path");
const pdf = require("pdf-parse");

const root = path.resolve(__dirname, "..");
const source = path.join(root, "data/source/zhang-yiming-weibo-2886.pdf");
const output = path.join(root, "data/source/extracted_layout.txt");
const metaOutput = path.join(root, "data/source/extraction_meta.json");

const X_GAP_SPACE_THRESHOLD = 1.3;
const Y_LINE_TOLERANCE = 0.8;
let footerBlocksRemoved = 0;

function groupIntoLines(items) {
  const groups = [];

  for (const item0 of items) {
    const item = {
      str: item0.str,
      x: item0.transform[4],
      y: item0.transform[5],
      width: item0.width
    };

    let line = groups.find((g) => Math.abs(g.y - item.y) < Y_LINE_TOLERANCE);
    if (!line) {
      line = { y: item.y, items: [] };
      groups.push(line);
    }
    line.items.push(item);
  }

  groups.sort((a, b) => b.y - a.y);

  return groups.map((line) => {
    line.items.sort((a, b) => a.x - b.x);

    let text = "";
    let previous = null;

    for (const item of line.items) {
      if (previous) {
        const gap = item.x - (previous.x + previous.width);
        if (gap > X_GAP_SPACE_THRESHOLD) text += " ";
      }
      text += item.str;
      previous = item;
    }

    return text.trimEnd();
  });
}

function stripThirdPartyFooter(lines) {
  const out = lines.slice();

  while (out.length && !out[out.length - 1].trim()) out.pop();

  for (let span = 1; span <= 4 && out.length >= span; span += 1) {
    const joined = out.slice(-span).join("").replace(/\s+/g, "");
    if (/添加微信1?领取200个互联网创业项目/.test(joined)) {
      out.splice(out.length - span, span);
      footerBlocksRemoved += 1;
      if (out.length && /^\d{1,3}$/.test(out[out.length - 1].trim())) out.pop();
      break;
    }
  }

  return out;
}

async function main() {
  if (!fs.existsSync(source)) {
    throw new Error("Missing source PDF: " + source);
  }

  const buffer = fs.readFileSync(source);
  const pages = [];
  let pageNumber = 0;

  await pdf(buffer, {
    pagerender: async (pageData) => {
      pageNumber += 1;
      const textContent = await pageData.getTextContent({
        normalizeWhitespace: false,
        disableCombineTextItems: false
      });

      const lines = stripThirdPartyFooter(groupIntoLines(textContent.items));
      pages.push(lines.join("\n"));
      return "";
    }
  });

  fs.writeFileSync(output, pages.join("\n"), "utf8");
  fs.writeFileSync(metaOutput, JSON.stringify({
    pages: pageNumber,
    footerBlocksRemoved: footerBlocksRemoved,
    xGapSpaceThreshold: X_GAP_SPACE_THRESHOLD,
    yLineTolerance: Y_LINE_TOLERANCE
  }, null, 2), "utf8");
  console.log(JSON.stringify({
    pages: pageNumber,
    output: output,
    bytes: fs.statSync(output).size,
    footerBlocksRemoved: footerBlocksRemoved
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
