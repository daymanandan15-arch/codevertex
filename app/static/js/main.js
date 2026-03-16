/* ============================================================
   main.js  — Engineering Portal
   - 4-section horizontal sliders (News, Roadmaps, Resources, Jobs)
   - 30-second live news polling with badge flash
   - LinkedIn-style Community Chat drawer
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    /* ── 1. Horizontal Sliders ── */
    const SCROLL_AMOUNT = 420; // px per arrow click

    document.querySelectorAll('.slider-wrapper').forEach(wrapper => {
        const list = wrapper.querySelector('.card-list');
        const prevBtn = wrapper.querySelector('.prev-btn');
        const nextBtn = wrapper.querySelector('.next-btn');
        if (!list) return;

        prevBtn && prevBtn.addEventListener('click', () => {
            list.scrollBy({ left: -SCROLL_AMOUNT, behavior: 'smooth' });
        });
        nextBtn && nextBtn.addEventListener('click', () => {
            list.scrollBy({ left: SCROLL_AMOUNT, behavior: 'smooth' });
        });
    });

    /* ── 2. Live News Polling with badge pulse ── */
    const liveBadge = document.getElementById('live-badge');

    function flashLiveBadge() {
        if (!liveBadge) return;
        liveBadge.classList.add('synced');
        setTimeout(() => liveBadge.classList.remove('synced'), 1500);
    }

    async function fetchLatestNews() {
        try {
            const res = await fetch('/api/feed');
            if (!res.ok) return;
            const data = await res.json();
            const list = document.getElementById('news-slider');
            if (!list || !data.news || data.news.length === 0) return;

            list.innerHTML = data.news.map(n => `
        <article class="card">
          <div class="card-meta">
            <span class="source badge">${n.source}</span>
            <time>${n.published_at}</time>
          </div>
          <h3><a href="${n.url}" target="_blank" rel="noopener noreferrer">${n.title}</a></h3>
        </article>
      `).join('');

            flashLiveBadge();
        } catch (err) {
            console.warn('[CoreStack] News poll failed:', err);
        }
    }

    fetchLatestNews();                         // immediate on load
    setInterval(fetchLatestNews, 30_000);      // then every 30 s

    /* ── 3. LinkedIn-Style Chat Drawer ── */
    const fab = document.getElementById('chat-fab');
    const drawer = document.getElementById('chat-drawer');
    const closeBtn = document.getElementById('chat-close-btn');
    const listView = document.getElementById('chat-list-view');
    const convoView = document.getElementById('chat-convo');
    const backBtn = document.getElementById('chat-back-btn');
    const msgsList = document.getElementById('chat-messages-list');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const badgeDot = document.getElementById('chat-badge');
    const threadsContainer = document.getElementById('chat-threads-container');
    const convoName = document.getElementById('convo-name');
    const convoAvatar = document.getElementById('convo-avatar');

    if (!fab || !drawer) return; // Chat not in DOM on some pages

    // We only have one global thread for now
    let unreadCount = 0;
    let socket = null;

    const THREADS = [
        { id: 1, name: 'Global Chat', initials: '🌎', preview: 'Join the developer lounge', time: 'Now' }
    ];

    function renderThreads() {
        threadsContainer.innerHTML = THREADS.map(t => `
      <div class="chat-thread" data-id="${t.id}">
        <div class="chat-avatar" style="background: linear-gradient(135deg,var(--accent),#8b5cf6);">${t.initials}</div>
        <div class="chat-thread-info">
          <div class="chat-thread-name">${t.name}</div>
          <div class="chat-thread-preview">${t.preview}</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.4rem;">
          <span class="chat-thread-meta">${t.time}</span>
        </div>
      </div>
    `).join('');

        threadsContainer.querySelectorAll('.chat-thread').forEach(el => {
            el.addEventListener('click', () => openConvo(+el.dataset.id));
        });
    }

    function initSocket() {
        if (!socket) {
            socket = io();
            const myUsername = window.CURRENT_USERNAME || 'Anonymous';
            socket.emit('join', { username: myUsername });

            socket.on('chat_message', (data) => {
                appendMessage(data.username, data.msg);
                if (!drawer.classList.contains('open') || convoView.style.display === 'none') {
                    unreadCount++;
                    updateBadge();
                }
            });

            socket.on('system_message', (data) => {
                appendSystemMessage(data.msg);
            });
        }
    }

    function appendMessage(sender, text) {
        const bubble = document.createElement('div');
        const isMe = (sender === window.CURRENT_USERNAME && window.CURRENT_USERNAME !== '');
        bubble.className = `chat-bubble ${isMe ? 'me' : 'them'}`;
        
        let content = '';
        if (!isMe) {
            content += `<div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:0.2rem; font-weight:600;">@${sender}</div>`;
        }
        content += `<div>${text.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>`;
        
        bubble.innerHTML = content;
        msgsList.appendChild(bubble);
        msgsList.scrollTop = msgsList.scrollHeight;
    }

    function appendSystemMessage(text) {
        const sys = document.createElement('div');
        sys.style.textAlign = 'center';
        sys.style.fontSize = '0.75rem';
        sys.style.color = 'var(--text-muted)';
        sys.style.margin = '0.5rem 0';
        sys.textContent = text;
        msgsList.appendChild(sys);
        msgsList.scrollTop = msgsList.scrollHeight;
    }

    function openConvo(id) {
        const thread = THREADS.find(t => t.id === id);
        if (!thread) return;
        unreadCount = 0;
        updateBadge();
        
        convoName.textContent = thread.name;
        convoAvatar.textContent = thread.initials;

        listView.style.display = 'none';
        convoView.style.display = 'flex';
        convoView.classList.add('visible');
        chatInput.focus();
        
        initSocket(); // Connect on open if not already
    }

    function closeConvo() {
        convoView.classList.remove('visible');
        convoView.style.display = 'none';
        listView.style.display = '';
        renderThreads();
    }

    function updateBadge() {
        if (badgeDot) {
            badgeDot.textContent = unreadCount || '';
            badgeDot.style.display = unreadCount ? 'flex' : 'none';
        }
    }

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        initSocket(); 
        const myUsername = window.CURRENT_USERNAME || 'Anonymous';
        socket.emit('chat_message', { username: myUsername, msg: text });
        
        chatInput.value = '';
    }

    // Toggle drawer
    fab.addEventListener('click', () => {
        const isOpen = drawer.classList.toggle('open');
        fab.setAttribute('aria-expanded', isOpen);
        if (isOpen) {
            renderThreads();
            initSocket();
        }
    });

    closeBtn && closeBtn.addEventListener('click', () => {
        drawer.classList.remove('open');
        fab.setAttribute('aria-expanded', false);
        closeConvo();
    });

    backBtn && backBtn.addEventListener('click', closeConvo);

    sendBtn && sendBtn.addEventListener('click', sendMessage);
    chatInput && chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') sendMessage();
    });

    updateBadge();

});
