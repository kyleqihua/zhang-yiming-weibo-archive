(function () {
  "use strict";

  var state = {
    posts: [],
    meta: null,
    filtered: [],
    query: "",
    year: "all",
    type: "all",
    order: "desc",
    visible: 36
  };

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $$(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  var feed = $("#feedList");
  var template = $("#postTemplate");
  var loadMoreBtn = $("#loadMoreBtn");
  var emptyState = $("#emptyState");
  var pinnedResult = $("#pinnedResult");

  function normalizeSearch(value) {
    return String(value || "").trim().toLocaleLowerCase("zh-CN").replace(/\s+/g, "");
  }

  function formatDate(post) {
    return post.year + "年" + post.month + "月" + post.day + "日 " + post.time;
  }

  function linkify(container, text) {
    container.textContent = "";
    var token = /(#([^#\n]{1,40})#|@[\w\u3400-\u9fff-]{1,40}|O网页链接)/g;
    var last = 0;
    var match;
    while ((match = token.exec(text)) !== null) {
      if (match.index > last) {
        container.appendChild(document.createTextNode(text.slice(last, match.index)));
      }
      var a = document.createElement("a");
      a.href = "#";
      a.textContent = match[0];
      a.addEventListener("click", function (event) {
        event.preventDefault();
      });
      container.appendChild(a);
      last = match.index + match[0].length;
    }
    if (last < text.length) {
      container.appendChild(document.createTextNode(text.slice(last)));
    }
  }

  function buildPost(post, pinned) {
    var node = template.content.firstElementChild.cloneNode(true);
    node.id = "post-" + post.id;
    node.dataset.postId = post.id;
    if (pinned) node.classList.add("flash");

    linkify($(".post-text", node), post.text);

    var timeLink = $(".post-time", node);
    timeLink.textContent = formatDate(post);
    timeLink.href = "#post-" + post.id;
    timeLink.title = "复制或分享当前地址，可以直接定位到这一条";

    var source = $(".post-source", node);
    source.textContent = post.source || "来源未识别";

    $(".copy-link", node).addEventListener("click", function () {
      var url = new URL(location.href);
      url.hash = "post-" + post.id;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url.toString()).then(function () {
          var btn = $(".copy-link", node);
          var old = btn.textContent;
          btn.textContent = "已复制";
          setTimeout(function () { btn.textContent = old; }, 1200);
        }).catch(function () {
          location.hash = "post-" + post.id;
        });
      } else {
        location.hash = "post-" + post.id;
      }
    });

    return node;
  }

  function applyFilters(resetVisible) {
    if (resetVisible !== false) state.visible = 36;
    var query = normalizeSearch(state.query);
    var result = state.posts.filter(function (post) {
      if (state.year !== "all" && String(post.year) !== state.year) return false;

      if (state.type === "repost" && post.flags.indexOf("repost") === -1) return false;
      if (state.type === "unavailable" &&
          post.flags.indexOf("deleted") === -1 &&
          post.flags.indexOf("unavailable") === -1) return false;
      if (state.type === "original" && post.flags.indexOf("repost") !== -1) return false;

      if (query) {
        var haystack = normalizeSearch(post.text + " " + post.source + " " + post.date);
        if (haystack.indexOf(query) === -1) return false;
      }
      return true;
    });

    if (state.order === "asc") result = result.slice().reverse();
    state.filtered = result;
    render();
  }

  function render() {
    var fragment = document.createDocumentFragment();
    state.filtered.slice(0, state.visible).forEach(function (post) {
      fragment.appendChild(buildPost(post, false));
    });
    feed.replaceChildren(fragment);

    var activeFilter = state.query || state.year !== "all" || state.type !== "all";
    $("#resultSummary").textContent = activeFilter
      ? "找到 " + state.filtered.length + " 条"
      : "共恢复 " + state.meta.parsedPosts + " 条";

    loadMoreBtn.hidden = state.visible >= state.filtered.length;
    emptyState.hidden = state.filtered.length !== 0;
    updateYearRows();

    if (location.hash.indexOf("#post-") === 0) {
      var id = location.hash.slice(6);
      requestAnimationFrame(function () { revealPost(id); });
    }
  }

  function revealPost(id) {
    var post = state.posts.find(function (item) { return item.id === id; });
    if (!post) return;

    var existing = document.getElementById("post-" + id);
    if (existing) {
      existing.classList.add("flash");
      existing.scrollIntoView({ block: "center" });
      setTimeout(function () { existing.classList.remove("flash"); }, 1600);
      return;
    }

    pinnedResult.hidden = false;
    pinnedResult.replaceChildren();

    var label = document.createElement("div");
    label.className = "pinned-label";
    label.textContent = "来自分享链接的微博";
    pinnedResult.appendChild(label);
    pinnedResult.appendChild(buildPost(post, true));
    pinnedResult.scrollIntoView({ block: "center" });
  }

  function makeBar(width) {
    var bar = document.createElement("span");
    bar.className = "year-bar";
    var inner = document.createElement("i");
    inner.style.width = width + "%";
    bar.appendChild(inner);
    return bar;
  }

  function renderYears() {
    var entries = Object.keys(state.meta.years).map(function (year) {
      return [year, state.meta.years[year]];
    }).sort(function (a, b) {
      return Number(b[0]) - Number(a[0]);
    });

    var max = Math.max.apply(null, entries.map(function (item) { return item[1]; }));
    var fragment = document.createDocumentFragment();

    function addYear(year, count, width, label) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "year-row" + (year === "all" ? " active" : "");
      btn.dataset.year = year;

      var name = document.createElement("span");
      name.className = "year-name";
      name.textContent = label;

      var n = document.createElement("span");
      n.className = "year-count";
      n.textContent = count;

      btn.appendChild(name);
      btn.appendChild(makeBar(width));
      btn.appendChild(n);
      btn.addEventListener("click", function () {
        state.year = year;
        applyFilters(true);
        $("#feed").scrollIntoView({ behavior: "smooth", block: "start" });
      });
      fragment.appendChild(btn);
    }

    addYear("all", state.meta.parsedPosts, 100, "全部");
    entries.forEach(function (item) {
      addYear(item[0], item[1], Math.max(4, item[1] / max * 100), item[0]);
    });
    $("#yearList").replaceChildren(fragment);
  }

  function updateYearRows() {
    $$(".year-row").forEach(function (row) {
      row.classList.toggle("active", row.dataset.year === state.year);
    });
  }

  function renderSources() {
    var entries = Object.keys(state.meta.sources).map(function (name) {
      return [name, state.meta.sources[name]];
    }).slice(0, 8);
    var max = entries.length ? entries[0][1] : 1;
    var fragment = document.createDocumentFragment();

    entries.forEach(function (item) {
      var wrap = document.createElement("div");
      wrap.className = "source-item";

      var row = document.createElement("div");
      row.className = "source-name";
      var name = document.createElement("span");
      var count = document.createElement("span");
      name.textContent = item[0];
      count.textContent = item[1];
      row.appendChild(name);
      row.appendChild(count);

      var bar = document.createElement("div");
      bar.className = "source-bar";
      var inner = document.createElement("i");
      inner.style.width = Math.max(4, item[1] / max * 100) + "%";
      bar.appendChild(inner);

      wrap.appendChild(row);
      wrap.appendChild(bar);
      fragment.appendChild(wrap);
    });

    $("#sourceList").replaceChildren(fragment);
  }

  function setSearch(value, sourceInput) {
    state.query = value;
    var top = $("#topSearch");
    var mobile = $("#mobileSearch");
    if (sourceInput !== top && top.value !== value) top.value = value;
    if (sourceInput !== mobile && mobile.value !== value) mobile.value = value;
    applyFilters(true);
  }

  function clearFilters() {
    state.query = "";
    state.year = "all";
    state.type = "all";
    state.visible = 36;
    $("#topSearch").value = "";
    $("#mobileSearch").value = "";
    $$(".feed-tab").forEach(function (tab) {
      tab.classList.toggle("active", tab.dataset.filter === "all");
    });
    pinnedResult.hidden = true;
    pinnedResult.replaceChildren();
    history.replaceState(null, "", location.pathname + location.search + "#feed");
    applyFilters(true);
  }

  function bindEvents() {
    var searchTimer;
    [$("#topSearch"), $("#mobileSearch")].forEach(function (input) {
      input.addEventListener("input", function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(function () {
          setSearch(input.value, input);
        }, 100);
      });
      input.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          input.value = "";
          setSearch("", input);
        }
      });
    });

    $$(".feed-tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        state.type = tab.dataset.filter;
        $$(".feed-tab").forEach(function (other) {
          other.classList.toggle("active", other === tab);
        });
        applyFilters(true);
      });
    });

    loadMoreBtn.addEventListener("click", function () {
      state.visible += 36;
      render();
    });

    $("#oldestFirstBtn").addEventListener("click", function () {
      state.order = state.order === "desc" ? "asc" : "desc";
      $("#orderLabel").textContent = state.order === "asc" ? "从最新开始" : "从最早开始";
      applyFilters(true);
    });

    $("#randomBtn").addEventListener("click", function () {
      var pool = state.filtered.length ? state.filtered : state.posts;
      var post = pool[Math.floor(Math.random() * pool.length)];
      if (!post) return;
      var url = new URL(location.href);
      url.hash = "post-" + post.id;
      history.replaceState(null, "", url.toString());
      revealPost(post.id);
    });

    $("#clearBtn").addEventListener("click", clearFilters);

    window.addEventListener("hashchange", function () {
      if (location.hash.indexOf("#post-") === 0) {
        revealPost(location.hash.slice(6));
      }
    });
  }

  function init() {
    Promise.all([
      fetch("./data/posts.json"),
      fetch("./data/meta.json")
    ]).then(function (responses) {
      if (!responses[0].ok || !responses[1].ok) throw new Error("数据文件读取失败");
      return Promise.all([responses[0].json(), responses[1].json()]);
    }).then(function (data) {
      state.posts = data[0];
      state.meta = data[1];

      $("#statPosts").textContent = state.meta.parsedPosts;
      $("#statYears").textContent = Object.keys(state.meta.years).length;
      $("#statSources").textContent = Object.keys(state.meta.sources).length;
      $("#statusParsed").textContent = state.meta.parsedPosts + " 条";
      $("#statusRange").textContent = "2010–2016";
      $("#statusFooters").textContent = "已清理 " + state.meta.removedThirdPartyFooters + " 处";
      $("#mobileSearch").placeholder = "搜索 " + state.meta.parsedPosts + " 条历史微博";

      renderYears();
      renderSources();
      bindEvents();
      applyFilters(true);

      if (location.hash.indexOf("#post-") === 0) {
        revealPost(location.hash.slice(6));
      }
    }).catch(function (error) {
      $("#resultSummary").textContent = "存档载入失败";
      feed.innerHTML = "";
      var box = document.createElement("div");
      box.className = "empty-state";
      var title = document.createElement("strong");
      title.textContent = "无法读取微博数据";
      var message = document.createElement("span");
      message.textContent = String(error.message || error);
      box.appendChild(title);
      box.appendChild(message);
      feed.appendChild(box);
    });
  }

  init();
})();
