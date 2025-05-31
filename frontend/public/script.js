// =========== GLOBAL SCOPE DEFINITIONS START ===========

// --- Global variables for search state ---
let currentSearchQuery = '';
let currentPage = 1;

// --- Global Timer for Drawer Auto-Close ---
let drawerCloseTimer = null;

// --- Global TTS Synth and Utterance ---
let globalSynth = window.speechSynthesis;
let globalCurrentUtterance = null;

// --- Global performSearch function ---
async function performSearch(query, page = 1) {
    console.log(`[Pagination Debug] performSearch called with query: "${query}", page: ${page}`);
    const searchResultsArea = document.getElementById('searchResultsArea');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const paginationControlsContainer = document.getElementById('paginationControls');

    if (!query) {
        console.log("[Pagination Debug] performSearch: Query is empty. Aborting.");
        if (searchResultsArea) searchResultsArea.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400">Please enter something to search for.</p>';
        if (paginationControlsContainer) paginationControlsContainer.innerHTML = '';
        return;
    }

    currentSearchQuery = query;
    currentPage = page;

    if (loadingIndicator) loadingIndicator.classList.remove('hidden');
    if (searchResultsArea) searchResultsArea.innerHTML = '';
    if (paginationControlsContainer) paginationControlsContainer.innerHTML = '';

    try {
        const response = await fetch('http://localhost:5001/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: query, page: page }),
        });

        if (loadingIndicator) loadingIndicator.classList.add('hidden');

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ reply: `Server error: ${response.status}` }));
            console.error('[Pagination Debug] performSearch: API request failed:', errorData);
            if (searchResultsArea) searchResultsArea.innerHTML = `<p class="text-red-500 text-center">${errorData.reply || 'Failed to fetch results.'}</p>`;
            return;
        }

        const data = await response.json();
        console.log("[Pagination Debug] performSearch: Data received from backend:", data);

        if (searchResultsArea) {
            searchResultsArea.innerHTML = data.reply;
            addDynamicEventListeners(); 
        }

        if (data.totalResults > 0 && data.totalPages > 0) {
            console.log(`[Pagination Debug] performSearch: Rendering pagination. Current: ${data.currentPage}, Total: ${data.totalPages}`);
            renderPaginationControls(data.currentPage, data.totalPages);
        } else {
            console.log("[Pagination Debug] performSearch: No results or no pages, not rendering pagination.");
            if (page === 1 && searchResultsArea && (!data.reply || !data.reply.includes('class="relative h-80'))) {
                if (searchResultsArea) searchResultsArea.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400">No recipes found for your query.</p>';
            }
        }
    } catch (error) {
        console.error('[Pagination Debug] performSearch: Critical error:', error);
        if (loadingIndicator) loadingIndicator.classList.add('hidden');
        if (searchResultsArea) searchResultsArea.innerHTML = '<p class="text-red-500 text-center">An unexpected error occurred. Please try again.</p>';
    }
}

// --- Global Drawer and Event Listener Functions ---
function toggleDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        document.querySelectorAll('.fixed[id^="drawer-"]').forEach(d => {
            if (d.id !== drawerId && !d.classList.contains('translate-x-full')) {
                d.classList.add('translate-x-full');
            }
        });
        drawer.classList.toggle('translate-x-full');
    }
}

function closeDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.add('translate-x-full');
    }
    if (globalSynth && globalSynth.speaking) {
        globalSynth.cancel();
    }
}

function handleDrawerMouseEnter() {
    if (drawerCloseTimer) {
        clearTimeout(drawerCloseTimer);
        drawerCloseTimer = null;
    }
}

function handleDrawerMouseLeave(event) {
    const drawer = event.currentTarget;
    if (drawerCloseTimer) clearTimeout(drawerCloseTimer);
    drawerCloseTimer = setTimeout(() => {
        if (!drawer.classList.contains('translate-x-full')) {
            drawer.classList.add('translate-x-full');
            if (globalSynth && globalSynth.speaking) {
                globalSynth.cancel();
            }
        }
    }, 700);
}

function toggleSpeakerIcon(buttonElement, isSpeaking) {
    const icon = buttonElement.querySelector('i');
    if (icon) {
        if (isSpeaking) {
            icon.classList.remove('fa-volume-up');
            icon.classList.add('fa-stop-circle');
            buttonElement.title = "Stop reading";
        } else {
            icon.classList.remove('fa-stop-circle');
            icon.classList.add('fa-volume-up');
            buttonElement.title = "Read content aloud";
        }
    }
}

function speakTextInDrawer(text, buttonElementForIconToggle) {
    if (globalSynth.speaking) {
        if (globalCurrentUtterance && globalCurrentUtterance.text === text) {
            globalSynth.cancel();
            if (buttonElementForIconToggle) toggleSpeakerIcon(buttonElementForIconToggle, false);
            globalCurrentUtterance = null;
            return;
        } else {
            globalSynth.cancel();
            document.querySelectorAll('.speak-drawer-button i.fa-stop-circle').forEach(icon => {
                const btn = icon.closest('.speak-drawer-button');
                if (btn) toggleSpeakerIcon(btn, false);
            });
        }
    }
    if (!text || text.trim() === "N/A" || text.trim() === "No ingredients listed." || text.trim() === "No instructions provided.") {
        const tempUtterance = new SpeechSynthesisUtterance("Nothing to read.");
        globalSynth.speak(tempUtterance);
        return;
    }
    globalCurrentUtterance = new SpeechSynthesisUtterance(text);
    globalCurrentUtterance.onstart = () => { if (buttonElementForIconToggle) toggleSpeakerIcon(buttonElementForIconToggle, true); };
    globalCurrentUtterance.onend = () => { if (buttonElementForIconToggle) toggleSpeakerIcon(buttonElementForIconToggle, false); globalCurrentUtterance = null; };
    globalCurrentUtterance.onerror = (event) => { 
        console.error('SpeechSynthesisUtterance.onerror', event); 
        if (buttonElementForIconToggle) toggleSpeakerIcon(buttonElementForIconToggle, false); 
        globalCurrentUtterance = null; 
    };
    globalSynth.speak(globalCurrentUtterance);
}

function handleSpeakButtonClick(contentTargetId, buttonElement) {
    const contentElement = document.getElementById(contentTargetId);
    if (contentElement) {
        const textToSpeak = contentElement.innerText || contentElement.textContent;
        speakTextInDrawer(textToSpeak.trim(), buttonElement);
    }
}

function addDynamicEventListeners() {
    console.log("[Event Listener Debug] addDynamicEventListeners called");
    function reattachListener(selector, eventType, handlerFnGenerator) {
        document.querySelectorAll(selector).forEach(element => {
            const newElement = element.cloneNode(true);
            element.parentNode.replaceChild(newElement, element);
            newElement.addEventListener(eventType, handlerFnGenerator(newElement));
        });
    }
    reattachListener('[data-drawer-target]', 'click', (el) => () => toggleDrawer(el.dataset.drawerTarget));
    reattachListener('[data-close-drawer]', 'click', (el) => () => closeDrawer(el.dataset.closeDrawer));
    reattachListener('.speak-drawer-button', 'click', (el) => () => handleSpeakButtonClick(el.dataset.contentTarget, el));
    document.querySelectorAll('.fixed[id^="drawer-"]').forEach(drawer => {
        drawer.removeEventListener('mouseleave', handleDrawerMouseLeave);
        drawer.addEventListener('mouseleave', handleDrawerMouseLeave);
        drawer.removeEventListener('mouseenter', handleDrawerMouseEnter);
        drawer.addEventListener('mouseenter', handleDrawerMouseEnter);
    });
    console.log("[Event Listener Debug] Dynamic event listeners re-attached.");
}

// --- Global renderPaginationControls function ---
function renderPaginationControls(currentPageNum, totalPagesNum) {
    console.log(`[Pagination Debug] renderPaginationControls called with currentPage: ${currentPageNum}, totalPages: ${totalPagesNum}`);
    const paginationControlsContainer = document.getElementById('paginationControls');
    if (!paginationControlsContainer) {
        console.error("[Pagination Debug] renderPaginationControls: paginationControls div not found!");
        return;
    }
    paginationControlsContainer.innerHTML = '';
    if (totalPagesNum <= 1) {
        console.log("[Pagination Debug] renderPaginationControls: Not enough pages to render controls.");
        return;
    }
    const ul = document.createElement('ul');
    ul.className = 'flex items-center justify-center space-x-1 sm:space-x-2 text-sm sm:text-base';
    if (currentPageNum > 1) {
        const prevLi = document.createElement('li');
        const prevButton = document.createElement('button');
        prevButton.innerHTML = '&laquo; Prev';
        prevButton.className = 'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:text-gray-700 dark:bg-slate-700 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-600 dark:hover:text-white transition-colors duration-150';
        prevButton.addEventListener('click', () => {
            console.log(`[Pagination Debug] Previous button clicked. Loading page: ${currentPageNum - 1}`);
            performSearch(currentSearchQuery, currentPageNum - 1);
        });
        prevLi.appendChild(prevButton);
        ul.appendChild(prevLi);
    }
    const maxPageButtons = 5;
    let startPage = Math.max(1, currentPageNum - Math.floor(maxPageButtons / 2));
    let endPage = Math.min(totalPagesNum, startPage + maxPageButtons - 1);
    if (endPage - startPage + 1 < maxPageButtons && startPage > 1) {
        startPage = Math.max(1, endPage - maxPageButtons + 1);
    }
    if (startPage > 1) {
        const firstLi = document.createElement('li');
        const firstButton = document.createElement('button');
        firstButton.textContent = '1';
        firstButton.className = 'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:text-gray-700 dark:bg-slate-700 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-600 dark:hover:text-white transition-colors duration-150';
        firstButton.addEventListener('click', () => {
            console.log("[Pagination Debug] Page 1 button clicked.");
            performSearch(currentSearchQuery, 1);
        });
        firstLi.appendChild(firstButton);
        ul.appendChild(firstLi);
        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.innerHTML = '<span class="px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-500 dark:text-gray-400">...</span>';
            ul.appendChild(ellipsisLi);
        }
    }
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        const pageButton = document.createElement('button');
        pageButton.textContent = i;
        pageButton.className = (i === currentPageNum) ? 
            'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-copper-600 bg-copper-50 border border-copper-500 rounded-md hover:bg-copper-100 hover:text-copper-700 dark:bg-copper-700 dark:border-copper-600 dark:text-white dark:hover:bg-copper-600 font-semibold z-10' :
            'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:text-gray-700 dark:bg-slate-700 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-600 dark:hover:text-white transition-colors duration-150';
        if (i === currentPageNum) pageButton.setAttribute('aria-current', 'page');
        pageButton.addEventListener('click', () => {
            console.log(`[Pagination Debug] Page ${i} button clicked.`);
            performSearch(currentSearchQuery, i);
        });
        pageLi.appendChild(pageButton);
        ul.appendChild(pageLi);
    }
    if (endPage < totalPagesNum) {
        if (endPage < totalPagesNum - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.innerHTML = '<span class="px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-500 dark:text-gray-400">...</span>';
            ul.appendChild(ellipsisLi);
        }
        const lastLi = document.createElement('li');
        const lastButton = document.createElement('button');
        lastButton.textContent = totalPagesNum;
        lastButton.className = 'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:text-gray-700 dark:bg-slate-700 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-600 dark:hover:text-white transition-colors duration-150';
        lastButton.addEventListener('click', () => {
            console.log(`[Pagination Debug] Last page (${totalPagesNum}) button clicked.`);
            performSearch(currentSearchQuery, totalPagesNum);
        });
        lastLi.appendChild(lastButton);
        ul.appendChild(lastLi);
    }
    if (currentPageNum < totalPagesNum) {
        const nextLi = document.createElement('li');
        const nextButton = document.createElement('button');
        nextButton.innerHTML = 'Next &raquo;';
        nextButton.className = 'px-3 py-2 sm:px-4 sm:py-2 leading-tight text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:text-gray-700 dark:bg-slate-700 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-600 dark:hover:text-white transition-colors duration-150';
        nextButton.addEventListener('click', () => {
            console.log(`[Pagination Debug] Next button clicked. Loading page: ${currentPageNum + 1}`);
            performSearch(currentSearchQuery, currentPageNum + 1);
        });
        nextLi.appendChild(nextButton);
        ul.appendChild(nextLi);
    }
    paginationControlsContainer.appendChild(ul);
}

// =========== GLOBAL SCOPE DEFINITIONS END ===========

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const resultsArea = document.getElementById('searchResultsArea');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    // --- Recent Searches --- (Variables and Constants)
    const RECENT_SEARCHES_KEY = 'tastoryRecentSearches';
    const MAX_RECENT_SEARCHES = 5;
    const recentSearchesContainer = document.getElementById('recentSearchesContainer');
    const recentSearchesSection = document.getElementById('recentSearchesSection');

    // --- Search Suggestions --- (Variables)
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    let suggestionDebounceTimer;
    const SUGGEST_API_URL = 'http://localhost:5001/suggest';

    // --- TTS Setup --- (Moved synth definition and voice logging setup higher)
    const synth = window.speechSynthesis;
    let currentUtterance = null;

    // --- Helper for logging voices, defined before setupSpeechSynthesis --- 
    function logAvailableVoicesHelper(synthInstance) { 
        const voices = synthInstance.getVoices();
        if (voices.length > 0) { 
            console.log("--- Available TTS Voices (DOMContentLoaded) ---");
            voices.forEach(v => console.log(`Voice: ${v.name}, Lang: ${v.lang}, Default: ${v.default}`)); 
        }
        else { console.log("No TTS voices available or still loading within logAvailableVoicesHelper."); }
    }

    // --- TTS Setup (uses logAvailableVoicesHelper) ---
    function setupSpeechSynthesis() {
        const synth = window.speechSynthesis; // Can keep synth local to this setup if only used here for onvoiceschanged
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => logAvailableVoicesHelper(synth);
        } else {
            // Fallback if onvoiceschanged is not supported or to catch voices loaded by this time
            logAvailableVoicesHelper(synth);
        }
        // Initial call in case voices are already loaded
        logAvailableVoicesHelper(synth);
    }

    // Call TTS setup early
    setupSpeechSynthesis();

    // --- Recent Searches Functions ---
    function getRecentSearches() {
        const searches = localStorage.getItem(RECENT_SEARCHES_KEY);
        return searches ? JSON.parse(searches) : [];
    }

    function saveSearchTerm(term) {
        if (!term || term.trim() === '') return;
        let searches = getRecentSearches();
        // Remove term if it already exists to move it to the front
        searches = searches.filter(s => s.toLowerCase() !== term.toLowerCase());
        searches.unshift(term); // Add to the beginning
        searches = searches.slice(0, MAX_RECENT_SEARCHES); // Limit to max number
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(searches));
        displayRecentSearches(); // Update display after saving
    }

    function displayRecentSearches() {
        if (!recentSearchesContainer || !recentSearchesSection) return;
        const searches = getRecentSearches();
        recentSearchesContainer.innerHTML = ''; // Clear current items

        if (searches.length === 0) {
            recentSearchesSection.classList.add('hidden');
            return;
        }
        recentSearchesSection.classList.remove('hidden');

        searches.forEach(term => {
            const termElement = document.createElement('button');
            termElement.textContent = term;
            termElement.classList.add(
                'px-3', 'py-1', 'text-sm', 'rounded-full', 'cursor-pointer',
                'bg-copper-500', 'text-white', 'hover:bg-copper-600',
                'dark:bg-copper-500', 'dark:text-white', 'dark:hover:bg-copper-400',
                'transition-colors', 'duration-150', 'focus:outline-none',
                'focus:ring-2', 'focus:ring-copper-400', 'focus:ring-opacity-75'
            );
            termElement.addEventListener('click', () => {
                searchInput.value = term;
                currentPage = 1; // Reset to first page
                performSearch(term, currentPage);
                hideSuggestions(); // Also hide suggestions if any are open
            });
            recentSearchesContainer.appendChild(termElement);
        });
    }

    // --- Search Suggestions Functions ---
    function clearSuggestions() {
        if (suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.classList.add('hidden');
        }
    }

    async function fetchAndDisplaySuggestions(query) {
        if (!suggestionsContainer) return;
        console.log("[Suggest] Fetching for query:", query);
        if (query.length < 2) { // Consistent with backend minimum
            clearSuggestions();
            console.log("[Suggest] Query too short, clearing.");
            return;
        }

        try {
            const response = await fetch(`${SUGGEST_API_URL}?query=${encodeURIComponent(query)}`);
            console.log("[Suggest] API Response Status:", response.status);
            if (!response.ok) {
                clearSuggestions();
                console.error("[Suggest] API response not OK:", response.statusText);
                return;
            }
            const suggestions = await response.json();
            console.log("[Suggest] Suggestions received:", suggestions);
            if (suggestions.length > 0) {
                suggestionsContainer.innerHTML = ''; // Clear previous
                suggestions.forEach(suggestion => {
                    const suggestionElement = document.createElement('div');
                    suggestionElement.textContent = suggestion;
                    suggestionElement.classList.add(
                        'px-4', 'py-2', 'cursor-pointer', 
                        'text-gray-900', 'hover:bg-gray-100', // Light mode text and hover bg
                        'dark:text-gray-200', 'dark:hover:bg-gray-700', 'dark:hover:text-gray-100' // Dark mode text and hover bg/text
                    );
                    suggestionElement.addEventListener('click', () => {
                        searchInput.value = suggestion;
                        clearSuggestions();
                        currentPage = 1; // Reset to first page
                        performSearch(suggestion, currentPage);
                        saveSearchTerm(suggestion); // Also save suggestion as a recent search
                        displayRecentSearches();
                    });
                    suggestionsContainer.appendChild(suggestionElement);
                });
                suggestionsContainer.classList.remove('hidden');
                console.log("[Suggest] Suggestions displayed.");
            } else {
                clearSuggestions();
                console.log("[Suggest] No suggestions returned from API or suggestions array empty.");
            }
        } catch (error) {
            console.error("[Suggest] Error fetching or processing suggestions:", error);
            clearSuggestions();
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(suggestionDebounceTimer);
            const query = searchInput.value.trim();
            if (query.length === 0) {
                clearSuggestions();
                return;
            }
            suggestionDebounceTimer = setTimeout(() => {
                fetchAndDisplaySuggestions(query);
            }, 300); // Debounce time: 300ms
        });

        // Hide suggestions if user clicks outside
        document.addEventListener('click', (event) => {
            if (!searchInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
                clearSuggestions();
            }
        });
        
        // Hide suggestions if user presses Escape key
        searchInput.addEventListener('keydown', (event) => {
            if (event.key === "Escape") {
                clearSuggestions();
            }
        });
    }

    // Theme toggle functionality
    function applyTheme(isDarkMode) {
        if (isDarkMode) {
            htmlElement.classList.add('dark');
        } else {
            htmlElement.classList.remove('dark');
        }
        updateThemeIcon(isDarkMode);
    }

    function updateThemeIcon(isDarkMode) {
        if (!themeToggle) return; // Guard clause if themeToggle is not found
        const sunIcon = themeToggle.querySelector('.sun-icon');
        const moonIcon = themeToggle.querySelector('.moon-icon');
        
        if (!sunIcon || !moonIcon) return; // Guard if icons not found

        if (isDarkMode) {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        } else {
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        }
    }

    // Theme toggle event listener
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDarkMode = !htmlElement.classList.contains('dark');
            applyTheme(isDarkMode);
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        });
    }

    // Check localStorage for saved theme preference on load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme === 'dark');
    } else {
        // Check system preference
        if (window.matchMedia) { // Ensure matchMedia is supported
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark);
        } else {
            applyTheme(false); // Default to light mode if system preference can't be checked
        }
    }
    // Initialize icon state based on current theme after loading
    if (htmlElement.classList.contains('dark')) {
        updateThemeIcon(true);
    } else {
        updateThemeIcon(false);
    }

    // Search functionality
    const CHAT_API_URL = 'http://localhost:5001/chat';

    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            console.log("[Search Debug] Search button clicked!");
            const query = searchInput.value.trim();
            if (query) {
                console.log("[Pagination Debug] New search initiated from button click.");
                performSearch(query, 1);
                if (typeof saveSearchTerm === 'function') saveSearchTerm(query);
                if (typeof displayRecentSearches === 'function') displayRecentSearches();
                if (typeof clearSuggestions === 'function') clearSuggestions();
            }
        });
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                console.log("[Search Debug] Enter key pressed in search input!");
                const query = searchInput.value.trim();
                if (query) {
                    console.log("[Pagination Debug] New search initiated from Enter key.");
                    performSearch(query, 1);
                    if (typeof saveSearchTerm === 'function') saveSearchTerm(query);
                    if (typeof displayRecentSearches === 'function') displayRecentSearches();
                    if (typeof clearSuggestions === 'function') clearSuggestions();
                }
            }
        });
    }

    // --- Drawer Functionality ---
    let currentlyOpenDrawer = null;

    function closeDrawer(drawer) {
        if (drawer) {
            drawer.classList.add('translate-x-full');
            drawer.classList.remove('translate-x-0');
            if (currentlyOpenDrawer === drawer) {
                currentlyOpenDrawer = null;
            }
        }
    }

    function openDrawer(drawer) {
        if (currentlyOpenDrawer && currentlyOpenDrawer !== drawer) {
            closeDrawer(currentlyOpenDrawer);
        }
        drawer.classList.remove('translate-x-full');
        drawer.classList.add('translate-x-0');
        currentlyOpenDrawer = drawer;
    }

    function addToggleEventListenersToResults() {
        if (!resultsArea) return;
        // Event listeners for expandable panels (Ingredients, Instructions, Nutrition)
        // These are the panels *within* the cards, not the main info drawer
        resultsArea.querySelectorAll('[data-target]').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = toggle.dataset.target;
                const panel = document.getElementById(targetId);
                if (panel) {
                    panel.classList.toggle('hidden');
                    // Adjust icon opacity based on current text color (text-white or text-white/80)
                    // This logic assumes icons use these classes for their states
                    if (toggle.classList.contains('text-white/80')) {
                        toggle.classList.remove('text-white/80');
                        toggle.classList.add('text-white');
                    } else if (toggle.classList.contains('text-white')) { // Ensure it's not some other color before toggling back
                        toggle.classList.remove('text-white');
                        toggle.classList.add('text-white/80');
                    }
                }
            });
        });

        // Event listeners for opening drawers (Info icons on cards)
        resultsArea.querySelectorAll('[data-drawer-target]').forEach(infoIcon => {
            infoIcon.addEventListener('click', (e) => {
                e.preventDefault();
                const drawerId = infoIcon.dataset.drawerTarget;
                const drawer = document.getElementById(drawerId); // Drawer is in the main document
                if (drawer) {
                    if (drawer.classList.contains('translate-x-0')) { // If already open, close it
                        closeDrawer(drawer);
                    } else {
                        openDrawer(drawer);
                    }
                }
            });
        });

        // Event listeners for closing drawers (via close button or mouseleave)
        // These drawers are direct children of body or a similar top-level container,
        // so querySelectorAll on 'document' is appropriate.
        document.querySelectorAll('[id^="drawer-info-"]').forEach(drawer => {
            const closeButton = drawer.querySelector('[data-close-drawer]');
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    closeDrawer(drawer);
                });
            }
            drawer.addEventListener('mouseleave', () => {
                 // Adding a small delay and check to prevent accidental closing
                 setTimeout(() => {
                    if (!drawer.matches(':hover')) { // Check if mouse is truly outside
                        closeDrawer(drawer);
                    }
                 }, 200); // 200ms delay
            });
        });
    }

    // Call for any initial content if necessary, or ensure it's called after dynamic loads
    addToggleEventListenersToResults(); 
    displayRecentSearches(); // Display recent searches on page load

    function addDynamicEventListeners() {
        console.log("[Event Listener Debug] addDynamicEventListeners called");

        function reattachListener(selector, eventType, handlerFnGenerator) {
            document.querySelectorAll(selector).forEach(element => {
                const newElement = element.cloneNode(true);
                element.parentNode.replaceChild(newElement, element);
                newElement.addEventListener(eventType, handlerFnGenerator(newElement));
            });
        }
        
        reattachListener('[data-drawer-target]', 'click', (el) => () => toggleDrawer(el.dataset.drawerTarget));
        reattachListener('[data-close-drawer]', 'click', (el) => () => closeDrawer(el.dataset.closeDrawer));
        reattachListener('.speak-drawer-button', 'click', (el) => () => handleSpeakButtonClick(el.dataset.contentTarget, el));

        // Mouseleave/mouseenter are trickier with cloneNode if they have complex internal state or rely on original instance
        // For simple cases or if handlers are stateless, direct re-attachment might be fine after removing old ones.
        document.querySelectorAll('.fixed[id^="drawer-"]').forEach(drawer => {
            drawer.removeEventListener('mouseleave', handleDrawerMouseLeave); 
            drawer.addEventListener('mouseleave', handleDrawerMouseLeave);
            drawer.removeEventListener('mouseenter', handleDrawerMouseEnter);
            drawer.addEventListener('mouseenter', handleDrawerMouseEnter);
        });
        console.log("[Event Listener Debug] Dynamic event listeners re-attached.");
    }

    function toggleDrawer(drawerId) {
        const drawer = document.getElementById(drawerId);
        if (drawer) {
            // Close other open drawers first
            document.querySelectorAll('.fixed[id^="drawer-"]').forEach(d => {
                if (d.id !== drawerId && !d.classList.contains('translate-x-full')) {
                    d.classList.add('translate-x-full');
                }
            });
            // Toggle current drawer
            drawer.classList.toggle('translate-x-full');
        }
    }
    function closeDrawer(drawerId) {
        const drawer = document.getElementById(drawerId);
        if (drawer) {
            drawer.classList.add('translate-x-full');
        }
        if (globalSynth && globalSynth.speaking) {
            globalSynth.cancel(); // Stop speech when drawer is closed
        }
    }

    function handleDrawerMouseEnter() {
        if (drawerCloseTimer) {
            clearTimeout(drawerCloseTimer);
            drawerCloseTimer = null;
        }
    }

    function handleDrawerMouseLeave(event) {
        const drawer = event.currentTarget;
        if (drawerCloseTimer) clearTimeout(drawerCloseTimer);
        drawerCloseTimer = setTimeout(() => {
            if (!drawer.classList.contains('translate-x-full')) {
                drawer.classList.add('translate-x-full');
                 if (globalSynth && globalSynth.speaking) {
                    globalSynth.cancel(); // Stop speech
                }
            }
        }, 700); // 700ms delay
    }

    function handleSpeakButtonClick(contentTargetId, buttonElement) {
        const contentElement = document.getElementById(contentTargetId);
        if (contentElement) {
            const textToSpeak = contentElement.innerText || contentElement.textContent;
            speakTextInDrawer(textToSpeak.trim(), buttonElement);
        }
    }

    // Make sure initializeTheme and other startup functions are called if they were in DOMContentLoaded
    initializeTheme();
    displayRecentSearches();
});

function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    function applyTheme(isDarkMode) {
        if (isDarkMode) {
            htmlElement.classList.add('dark');
        } else {
            htmlElement.classList.remove('dark');
        }
        updateThemeIcon(isDarkMode);
    }
    function updateThemeIcon(isDarkMode) {
        if (!themeToggle) return;
        const sunIcon = themeToggle.querySelector('.sun-icon');
        const moonIcon = themeToggle.querySelector('.moon-icon');
        if (!sunIcon || !moonIcon) return;
        if (isDarkMode) {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        } else {
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        }
    }
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme === 'dark');
    } else {
        if (window.matchMedia) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark);
        } else {
            applyTheme(false);
        }
    }
    if (htmlElement.classList.contains('dark')) updateThemeIcon(true);
    else updateThemeIcon(false);
}
