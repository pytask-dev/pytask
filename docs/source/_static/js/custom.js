/*

The following code is copied from https://github.com/tiangolo/typer.

The MIT License (MIT)

Copyright (c) 2019 Sebastián Ramírez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/

document.querySelectorAll(".use-termynal").forEach(node => {
    node.style.display = "block";
    new Termynal(node, {
        lineDelay: 500
    });
});
const progressLiteralStart = "---> 100%";
const promptLiteralStart = "$ ";
const customPromptLiteralStart = "# ";
const termynalActivateClass = "termy";
let termynals = [];

function createTermynals() {
    document
        .querySelectorAll(`.${termynalActivateClass} .highlight`)
        .forEach(node => {
            const text = node.textContent;
            const lines = text.split("\n");
            const useLines = [];
            let buffer = [];
            function saveBuffer() {
                if (buffer.length) {
                    let isBlankSpace = true;
                    buffer.forEach(line => {
                        if (line) {
                            isBlankSpace = false;
                        }
                    });
                    dataValue = {};
                    if (isBlankSpace) {
                        dataValue["delay"] = 0;
                    }
                    if (buffer[buffer.length - 1] === "") {
                        // A last single <br> won't have effect
                        // so put an additional one
                        buffer.push("");
                    }
                    const bufferValue = buffer.join("<br>");
                    dataValue["value"] = bufferValue;
                    useLines.push(dataValue);
                    buffer = [];
                }
            }
            for (let line of lines) {
                if (line === progressLiteralStart) {
                    saveBuffer();
                    useLines.push({
                        type: "progress"
                    });
                } else if (line.startsWith(promptLiteralStart)) {
                    saveBuffer();
                    const value = line.replace(promptLiteralStart, "").trimEnd();
                    useLines.push({
                        type: "input",
                        value: value
                    });
                } else if (line.startsWith("// ")) {
                    saveBuffer();
                    const value = "💬 " + line.replace("// ", "").trimEnd();
                    useLines.push({
                        value: value,
                        class: "termynal-comment",
                        delay: 0
                    });
                } else if (line.startsWith(customPromptLiteralStart)) {
                    saveBuffer();
                    const promptStart = line.indexOf(promptLiteralStart);
                    if (promptStart === -1) {
                        console.error("Custom prompt found but no end delimiter", line)
                    }
                    const prompt = line.slice(0, promptStart).replace(customPromptLiteralStart, "")
                    let value = line.slice(promptStart + promptLiteralStart.length);
                    useLines.push({
                        type: "input",
                        value: value,
                        prompt: prompt
                    });
                } else {
                    buffer.push(line);
                }
            }
            saveBuffer();
            const div = document.createElement("div");
            node.replaceWith(div);
            const termynal = new Termynal(div, {
                lineData: useLines,
                noInit: true,
                lineDelay: 500
            });
            termynals.push(termynal);
        });
}

function loadVisibleTermynals() {
    termynals = termynals.filter(termynal => {
        if (termynal.container.getBoundingClientRect().top - innerHeight <= 0) {
            termynal.init();
            return false;
        }
        return true;
    });
}
window.addEventListener("scroll", loadVisibleTermynals);
createTermynals();
loadVisibleTermynals();

function isTextInputElement(element) {
    if (!element) {
        return false;
    }
    const tagName = element.tagName.toLowerCase();
    return (
        tagName === "input" ||
        tagName === "textarea" ||
        tagName === "select" ||
        element.isContentEditable
    );
}

document.addEventListener("keydown", event => {
    if (
        event.defaultPrevented ||
        event.altKey ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        isTextInputElement(document.activeElement)
    ) {
        return;
    }

    let rel;
    if (event.key === "ArrowLeft") {
        rel = "prev";
    } else if (event.key === "ArrowRight") {
        rel = "next";
    } else {
        return;
    }

    const link = document.querySelector(`link[rel="${rel}"]`);
    if (link && link.href) {
        event.preventDefault();
        window.location.href = link.href;
    }
});

function getTitleForUrl(url) {
    const targetPath = new URL(url, window.location.href).pathname;
    const navLinks = document.querySelectorAll(".md-nav a[href], .md-tabs a[href]");

    for (const link of navLinks) {
        const linkPath = new URL(link.href, window.location.href).pathname;
        if (linkPath === targetPath) {
            return link.textContent.trim().replace(/\s+/g, " ");
        }
    }

    const fileName = targetPath.split("/").pop() || "";
    return fileName.replace(".html", "").replace(/[-_]/g, " ");
}

function createPageHintNav() {
    const prev = document.querySelector('link[rel="prev"]');
    const next = document.querySelector('link[rel="next"]');

    if (!prev && !next) {
        return;
    }

    const article = document.querySelector("article.md-content__inner");
    if (!article) {
        return;
    }

    const nav = document.createElement("nav");
    nav.className = "page-hint-nav";
    nav.setAttribute("aria-label", "Page navigation");

    function buildLink(rel, href) {
        const direction = rel === "next" ? "next" : "prev";
        const anchor = document.createElement("a");
        anchor.className = `page-hint page-hint--${direction}`;
        anchor.href = href;

        const label = document.createElement("span");
        label.className = "page-hint__label";
        label.textContent = direction === "next" ? "Next" : "Previous";

        const title = document.createElement("span");
        title.className = "page-hint__title";
        title.textContent = getTitleForUrl(href);

        const caret = document.createElement("span");
        caret.className = "page-hint__caret";
        caret.textContent = direction === "next" ? "›" : "‹";

        anchor.append(label, title, caret);
        return anchor;
    }

    if (prev?.href) {
        nav.appendChild(buildLink("prev", prev.href));
    }
    if (next?.href) {
        nav.appendChild(buildLink("next", next.href));
    }

    article.appendChild(nav);
}

createPageHintNav();
