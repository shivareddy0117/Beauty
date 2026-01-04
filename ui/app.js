// State management
let state = {
    jobs: [],
    filters: {
        search: '',
        companies: new Set() // Selected companies
    },
    sort: 'newest' // 'newest' or 'oldest'
};

// Main entry point
document.addEventListener('DOMContentLoaded', () => {
    init();
});

async function init() {
    await loadJobs();
    setupEventListeners();
    renderApp();
}

async function loadJobs() {
    try {
        // Data is loaded via <script src="jobs.js"> which sets window.JOBS_DATA
        const data = window.JOBS_DATA || [];

        if (!data || data.length === 0) {
            console.warn('No data found in JOBS_DATA, checking for mock fallback...');
            throw new Error('No data loaded');
        }

        // Normalize
        state.jobs = data.map(normalizeJob);

        // Initialize filters
        const uniqueCompanies = [...new Set(state.jobs.map(j => j.company))];
        uniqueCompanies.forEach(c => state.filters.companies.add(c));

        // Render
        renderFilters();
        renderJobs();

    } catch (err) {
        console.error('Error loading jobs:', err);
        // Fallback to error message, DO NOT use mock data as it confuses the user
        const container = document.getElementById('job-container');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; color: white; padding: 2rem;">
                    <h3>Could not load job data.</h3>
                    <p>Please ensure <code>jobs.js</code> is present in the folder.</p>
                </div>`;
        }
    }
}

// Normalize different scraper outputs into a standard format
function normalizeJob(job) {
    // Determine company
    let company = job.company || job.company_name || 'Unknown';
    if (company.toLowerCase().includes('amazon')) company = 'Amazon';
    if (company.toLowerCase().includes('microsoft')) company = 'Microsoft';
    if (company.toLowerCase().includes('cvs')) company = 'CVS Health';

    // Parse Date
    // Formats: ISO string (MS), "December 30, 2025" (Amazon), or fallback
    let dateObj = new Date();
    const rawDate = job.posted_date || job.postedTs; // Handle both keys if they exist

    if (rawDate) {
        const parsed = new Date(rawDate);
        if (!isNaN(parsed.getTime())) {
            dateObj = parsed;
        }
    }

    // specific URL logic
    let url = job.url_next_step || '#';
    if (company === 'Amazon' && job.job_path) {
        url = 'https://www.amazon.jobs' + job.job_path;
    }

    return {
        id: job.id || Math.random().toString(36),
        displayId: job.id_icims || job.id, // Prefer short ID for Amazon if available
        title: job.title || 'No Title',
        company: company,
        location: job.location || 'Remote/Unknown',
        description: job.description_short || job.description || '',
        url: url,
        date: dateObj,
        rawJob: job
    };
}

function setupEventListeners() {
    const searchInput = document.getElementById('job-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            state.filters.search = e.target.value.toLowerCase();
            renderJobs();
        });
    }
}

function renderApp() {
    renderFilters();
    renderJobs();
}

function renderFilters() {
    const header = document.querySelector('header');

    // Create filter container if not exists
    let filterContainer = document.getElementById('filter-container');
    if (!filterContainer) {
        filterContainer = document.createElement('div');
        filterContainer.id = 'filter-container';
        // Insert after search
        const searchContainer = document.querySelector('.search-container');
        searchContainer.parentNode.insertBefore(filterContainer, searchContainer.nextSibling);
    }

    // Get unique companies from all jobs (not just filtered ones)
    const companies = [...new Set(state.jobs.map(j => j.company))].sort();

    // Build HTML for filters
    filterContainer.innerHTML = `
        <div class="filter-group">
            <span class="filter-label">Company:</span>
            ${companies.map(c => `
                <button class="filter-pill ${state.filters.companies.has(c) ? 'active' : ''}" 
                        onclick="toggleCompanyObject('${c}')">
                    ${c}
                </button>
            `).join('')}
        </div>
        <div class="filter-group right">
            <select id="sort-select" onchange="updateSort(this.value)">
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
            </select>
        </div>
    `;
}

// Global scope for onclick handlers
window.toggleCompanyObject = function (company) {
    if (state.filters.companies.has(company)) {
        // Don't allow unselecting the last one (optional UX choice)
        if (state.filters.companies.size > 1) {
            state.filters.companies.delete(company);
        }
    } else {
        state.filters.companies.add(company);
    }
    renderFilters();
    renderJobs();
};

window.updateSort = function (val) {
    state.sort = val;
    renderJobs();
};

function renderJobs() {
    const container = document.getElementById('job-container');
    const countEl = document.getElementById('job-count');

    // Filter
    const filtered = state.jobs.filter(job => {
        // Search filter
        const matchesSearch =
            job.title.toLowerCase().includes(state.filters.search) ||
            job.company.toLowerCase().includes(state.filters.search) ||
            job.location.toLowerCase().includes(state.filters.search);

        // Company filter
        const matchesCompany = state.filters.companies.has(job.company);

        return matchesSearch && matchesCompany;
    });

    // Sort
    filtered.sort((a, b) => {
        if (state.sort === 'newest') return b.date - a.date;
        return a.date - b.date;
    });

    // Update count
    countEl.textContent = `${filtered.length} Jobs Found`;

    // Render
    container.innerHTML = filtered.map(job => `
        <div class="job-card" style="border-left: 4px solid ${getCompanyColor(job.company)}">
            <div class="job-header">
                <h3>${highlightText(job.title, state.filters.search)}</h3>
                <span class="company-badge" style="background: ${getCompanyColor(job.company)}20; color: ${getCompanyColor(job.company)}">
                    ${job.company}
                </span>
            </div>
            <div class="job-meta">
                <span title="${job.location}">📍 ${formatLocation(job.location)}</span>
                <span title="${job.date.toLocaleDateString()}">📅 ${timeAgo(job.date)}</span>
                <span class="job-id-tag">🆔 ${job.displayId}</span>
            </div>
            <p class="job-desc">${truncate(job.description, 140)}</p>
            <div class="job-actions">
                <a href="${job.url}" target="_blank" class="apply-btn">Apply Now</a>
            </div>
        </div>
    `).join('');

    if (filtered.length === 0) {
        container.innerHTML = '<div class="no-results">No jobs found matching your criteria.</div>';
    }
}

// Helpers
function getCompanyColor(company) {
    if (company === 'Amazon') return '#FF9900'; // Amazon Orange
    if (company === 'Microsoft') return '#00A4EF'; // Microsoft Blue
    if (company === 'CVS Health') return '#CC0000'; // CVS Red
    return '#3b82f6'; // Default Blue
}

function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    return "Just now";
}

function formatLocation(loc) {
    // Simplify location string if tool long
    if (loc.length > 30) return loc.split(',')[0] + '...';
    return loc;
}

function truncate(str, n) {
    return (str.length > n) ? str.substr(0, n - 1) + '...' : str;
}

function highlightText(text, search) {
    if (!search) return text;
    const regex = new RegExp(`(${search})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function getMockJobs() {
    return [
        { title: "Senior Data Engineer", company: "Amazon", location: "Seattle, WA", description: "Big data...", posted_date: new Date().toISOString() },
        { title: "Software Engineer II", company: "Microsoft", location: "Redmond, WA", description: "Azure...", posted_date: new Date(Date.now() - 86400000).toISOString() }
    ];
}
