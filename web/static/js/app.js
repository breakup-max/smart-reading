var state = {
    activeFileHash: null,
    activeFileName: null,
    files: {}
};

var dom = {
    uploadZone: document.getElementById("uploadZone"),
    fileInput: document.getElementById("fileInput"),
    fileListContainer: document.getElementById("fileListContainer"),
    fileIndicator: document.getElementById("fileIndicator"),
    chatMessages: document.getElementById("chatMessages"),
    questionInput: document.getElementById("questionInput"),
    sendBtn: document.getElementById("sendBtn")
};

// ========================
//  Upload
// ========================

dom.uploadZone.addEventListener("click", function () {
    dom.fileInput.click();
});

dom.uploadZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dom.uploadZone.classList.add("dragover");
});

dom.uploadZone.addEventListener("dragleave", function () {
    dom.uploadZone.classList.remove("dragover");
});

dom.uploadZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dom.uploadZone.classList.remove("dragover");
    var file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
});

dom.fileInput.addEventListener("change", function () {
    var file = dom.fileInput.files[0];
    if (file) handleUpload(file);
    dom.fileInput.value = "";
});

function handleUpload(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("只支持 PDF 文件");
        return;
    }

    showUploading(file.name);

    var formData = new FormData();
    formData.append("file", file);

    fetch("/api/upload", { method: "POST", body: formData })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.detail) throw new Error(data.detail);

            var record = { name: file.name, hash: data.file_hash };
            state.files[data.file_hash] = record;
            renderFileList();
            switchFile(data.file_hash);
        })
        .catch(function (err) {
            alert("上传失败: " + err.message);
            removeUploading();
        });
}

function showUploading(name) {
    var item = document.createElement("div");
    item.className = "file-item";
    item.id = "uploading-item";
    item.innerHTML =
        '<div class="file-name">⏳ ' + escapeHtml(name) + '</div>' +
        '<div class="file-meta">正在构建索引...</div>';
    var container = dom.fileListContainer;
    var empty = container.querySelector(".empty-files");
    if (empty) empty.remove();
    container.insertBefore(item, container.firstChild);
}

function removeUploading() {
    var item = document.getElementById("uploading-item");
    if (item) item.remove();
    if (Object.keys(state.files).length === 0) {
        dom.fileListContainer.innerHTML = '<div class="empty-files">暂无文件，请先上传 PDF</div>';
    }
}

// ========================
//  File List
// ========================

function renderFileList() {
    var html = "";
    var hashes = Object.keys(state.files);
    if (hashes.length === 0) {
        html = '<div class="empty-files">暂无文件，请先上传 PDF</div>';
    } else {
        hashes.forEach(function (h) {
            var f = state.files[h];
            var isActive = h === state.activeFileHash;
            html +=
                '<div class="file-item' + (isActive ? " active" : "") + '" data-hash="' + h + '">' +
                '<span class="remove-btn" data-hash="' + h + '" title="移除">&times;</span>' +
                '<div class="file-name">📄 ' + escapeHtml(f.name) + '</div>' +
                '<div class="file-meta"><span class="status-dot"></span>已就绪</div>' +
                '</div>';
        });
    }
    dom.fileListContainer.innerHTML = html;

    // bind click on file items
    var items = dom.fileListContainer.querySelectorAll(".file-item");
    items.forEach(function (item) {
        item.addEventListener("click", function (e) {
            if (e.target.classList.contains("remove-btn")) return;
            var h = item.getAttribute("data-hash");
            if (h) switchFile(h);
        });
    });

    // bind remove
    var removes = dom.fileListContainer.querySelectorAll(".remove-btn");
    removes.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            var h = btn.getAttribute("data-hash");
            if (h === state.activeFileHash) {
                state.activeFileHash = null;
                state.activeFileName = null;
                dom.fileIndicator.textContent = "请选择或上传 PDF 文件";
                dom.questionInput.disabled = true;
                dom.sendBtn.disabled = true;
            }
            delete state.files[h];
            renderFileList();
        });
    });
}

function switchFile(hash) {
    state.activeFileHash = hash;
    state.activeFileName = state.files[hash].name;
    dom.fileIndicator.textContent = state.activeFileName;
    dom.questionInput.disabled = false;
    dom.sendBtn.disabled = false;
    renderFileList();
    clearChat();
}

// ========================
//  Chat
// ========================

function clearChat() {
    dom.chatMessages.innerHTML =
        '<div class="welcome"><div class="big-icon">💬</div>' +
        '<p>现在可以针对 <strong>' + escapeHtml(state.activeFileName) + '</strong> 提问了</p></div>';
}

function addMessage(role, text, evidence) {
    var welcome = dom.chatMessages.querySelector(".welcome");
    if (welcome) welcome.remove();

    var msgDiv = document.createElement("div");
    msgDiv.className = "msg " + role;

    var avatar = role === "user" ? "👤" : "🤖";
    msgDiv.innerHTML = '<div class="avatar">' + avatar + '</div>' +
        '<div><div class="bubble">' + formatText(text) + '</div></div>';

    var bubbleWrapper = msgDiv.querySelector(".bubble").parentNode;

    if (role === "bot" && evidence && evidence.length > 0) {
        var toggleBtn = document.createElement("span");
        toggleBtn.className = "evidence-toggle";
        toggleBtn.textContent = "📎 查看引用证据 (" + evidence.length + ")";
        bubbleWrapper.appendChild(toggleBtn);

        var evList = document.createElement("div");
        evList.className = "evidence-list";
        evList.style.display = "none";
        evidence.forEach(function (ev) {
            var pageLabel = ev.page !== null ? "第" + (ev.page + 1) + "页" : "未知页";
            var evItem = document.createElement("div");
            evItem.className = "evidence-item";
            evItem.innerHTML =
                '<div class="ev-header"><span>' + escapeHtml(ev.source) + " · " + pageLabel + '</span>' +
                '<span>LLM:' + (ev.llm_score || 0).toFixed(1) + '</span></div>' +
                '<div>' + escapeHtml(ev.content) + '</div>';
            evList.appendChild(evItem);
        });
        bubbleWrapper.appendChild(evList);

        toggleBtn.addEventListener("click", function () {
            if (evList.style.display === "none") {
                evList.style.display = "flex";
                toggleBtn.textContent = "📎 收起证据";
            } else {
                evList.style.display = "none";
                toggleBtn.textContent = "📎 查看引用证据 (" + evidence.length + ")";
            }
        });
    }

    dom.chatMessages.appendChild(msgDiv);
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

function addLoading() {
    var welcome = dom.chatMessages.querySelector(".welcome");
    if (welcome) welcome.remove();

    var msgDiv = document.createElement("div");
    msgDiv.className = "msg bot";
    msgDiv.id = "loading-msg";
    msgDiv.innerHTML =
        '<div class="avatar">🤖</div>' +
        '<div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
    dom.chatMessages.appendChild(msgDiv);
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

function removeLoading() {
    var el = document.getElementById("loading-msg");
    if (el) el.remove();
}

function setInputEnabled(enabled) {
    dom.questionInput.disabled = !enabled;
    dom.sendBtn.disabled = !enabled;
}

// ========================
//  Send
// ========================

function sendQuestion() {
    var question = dom.questionInput.value.trim();
    if (!question) return;
    if (!state.activeFileHash) {
        alert("请先上传或选择一个 PDF 文件");
        return;
    }

    dom.questionInput.value = "";
    autoResize(dom.questionInput);
    addMessage("user", question);
    addLoading();
    setInputEnabled(false);

    fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            file_hash: state.activeFileHash,
            question: question
        })
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            removeLoading();
            if (data.detail) throw new Error(data.detail);
            var answer = data.answer;
            if (data.rewritten && data.search_query !== question) {
                answer += '\n<span class="search-query-label">🔍 改写查询: ' +
                    escapeHtml(data.search_query) + '</span>';
            }
            addMessage("bot", answer, data.evidence);
            setInputEnabled(true);
            dom.questionInput.focus();
        })
        .catch(function (err) {
            removeLoading();
            addMessage("bot", "⚠️ 出错了: " + err.message);
            setInputEnabled(true);
        });
}

dom.sendBtn.addEventListener("click", sendQuestion);

dom.questionInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

// ========================
//  Helpers
// ========================

function autoResize(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

dom.questionInput.addEventListener("input", function () {
    autoResize(this);
});

function escapeHtml(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function formatText(text) {
    return escapeHtml(text)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}

// ========================
//  Health check on load
// ========================

fetch("/api/health")
    .then(function (r) { return r.json(); })
    .then(function (d) {
        if (!d.api_key_configured) {
            console.warn("DASHSCOPE_API_KEY 未配置，请设置环境变量");
        }
    })
    .catch(function () {
        console.error("后端未连接");
    });