// script.js - Main JavaScript File

// Global variables for managing user state
if (typeof currentUser === 'undefined') {
    let currentUser = JSON.parse(localStorage.getItem('currentUser')) || null;
    let userType = currentUser ? currentUser.type : null;
    
    // Initialize userSkills array
    let userSkills = [];
}

// Function to verify token and protect routes
async function verifyToken() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user || !user.token) {
        window.location.replace('index.html');
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/verify-token', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${user.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Token verification failed');
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error('Token invalid');
        }

        return data;
    } catch (error) {
        console.error('Token verification failed:', error);
        localStorage.removeItem('currentUser');
        window.location.replace('index.html');
    }
}

// Protect dashboard routes
if (window.location.pathname.includes('dashboard')) {
    verifyToken().catch(() => {
        window.location.replace('index.html');
    });
}

// Wait for the DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Only set up login-related functionality if we're on the login/landing page
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/') {
        // Set up tab switching
        setupTabSwitching();
        
        // Set up registration links
        setupRegistrationLinks();
        
        // Set up modal close functionality
        setupModalClose();

        // Set up login form handlers
        setupLoginForms();
        
        // Set up registration form handler
        document.addEventListener('submit', function(event) {
            if (event.target.id === 'registration-form') {
                event.preventDefault();
                const type = document.getElementById('register-modal').dataset.userType;
                registerUser(event, type);
            }
        });
        
        // Set initial active tab based on URL parameter or default to jobseeker
        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('type') || 'jobseeker';
        switchTabs(initialTab);
    }
});

// Setup tab switching functionality
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.id.replace('-tab', '');
            switchTabs(type);
        });
    });
}

function switchTabs(type) {
    console.log(`Switching tabs to: ${type}`);
    
    // Remove active class from all tabs and forms
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.classList.remove('active');
        console.log(`Removed active class from tab: ${tab.id}`);
    });
    
    document.querySelectorAll('.login-form').forEach(form => {
        form.classList.remove('active');
        console.log(`Removed active class from form: ${form.id}`);
    });

    // Add active class to selected tab and form
    const selectedTab = document.getElementById(`${type}-tab`);
    const selectedForm = document.getElementById(`${type}-form`);

    console.log('Selected elements:', { 
        tab: selectedTab ? selectedTab.id : 'not found', 
        form: selectedForm ? selectedForm.id : 'not found'
    });

    if (selectedTab && selectedForm) {
        selectedTab.classList.add('active');
        selectedForm.classList.add('active');
        console.log('Added active classes to selected elements');
        
        // Update URL without page reload
        const url = new URL(window.location.href);
        url.searchParams.set('type', type);
        window.history.replaceState({}, '', url);
        console.log('Updated URL:', url.href);
    } else {
        console.error('Could not find tab or form elements for type:', type);
    }
}

function setupRegistrationLinks() {
    const registerLinks = document.querySelectorAll('.register-link');
    registerLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const userType = this.getAttribute('data-type');
            showRegisterForm(userType);
        });
    });
}

function setupModalClose() {
    const modal = document.getElementById('register-modal');
    const closeBtn = document.querySelector('.close-btn');
    
    // Close on X button click
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    // Close on clicking outside modal
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// Remove any previous error messages
function clearErrors() {
    document.querySelectorAll('.error-message').forEach(error => {
        if (error.style) {
            error.style.display = 'none';
            error.textContent = '';
        }
    });
}

function showLoginError(formId, message) {
    const form = document.getElementById(formId);
    if (!form) return;

    const errorContainer = form.querySelector('.error-message');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    }
}

function showError(formId, message) {
    clearErrors(); // Clear any existing errors
    
    // For registration form
    if (formId === 'registration-form') {
        const errorDiv = document.getElementById('registration-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            return;
        }
    }
    
    // For login forms
    const form = document.getElementById(formId);
    if (!form) {
        console.error('Form not found:', formId);
        return;
    }
    
    const errorDiv = form.querySelector('.error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    } else {
        console.error('Error message container not found in form:', formId);
    }
}

// Set up login form handlers
function setupLoginForms() {
    const jobseekerForm = document.getElementById('jobseeker-login-form');
    const recruiterForm = document.getElementById('recruiter-login-form');

    if (jobseekerForm) {
        jobseekerForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            await loginUser(event, 'jobseeker');
        });
    }

    if (recruiterForm) {
        recruiterForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            await loginUser(event, 'recruiter');
        });
    }
}

// Unified login function for both user types
async function loginUser(event, userType) {
    event.preventDefault();
    clearErrors();

    const formId = `${userType}-form`;
    const emailId = userType === 'jobseeker' ? 'js-email' : 'rec-email';
    const passwordId = userType === 'jobseeker' ? 'js-password' : 'rec-password';
    
    const email = document.getElementById(emailId).value;
    const password = document.getElementById(passwordId).value;
    
    // Simple validation
    if (!email || !password) {
        showError(formId, 'Please enter both email and password');
        return;
    }
    
    try {
        const loginData = {
            userEmail: email,
            password: password,
            userType: userType
        };
        console.log('Sending login request with data:', loginData);
        
        const response = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });

        console.log('Login response status:', response.status);
        const data = await response.json();
        console.log('Login response data:', data);
        if (response.ok && (data.token || data.access_token)) {
            // Store user data
            const userData = {
                email: email,
                type: userType,
                token: data.token || data.access_token
            };
            localStorage.setItem('currentUser', JSON.stringify(userData));
            
            // Redirect to appropriate dashboard
            const dashboardUrl = `${userType}-dashboard.html`;
            console.log('Redirecting to dashboard:', dashboardUrl);
            window.location.replace(dashboardUrl); // Using replace to prevent back navigation to login
        } else {
            showLoginError(formId, data.detail || 'Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showLoginError(formId, 'Network error. Please try again.');
    }
}

// Registration Modal functions
function showRegisterForm(type) {
    const modal = document.getElementById('register-modal');
    const container = document.getElementById('register-form-container');
    
    // Clear any existing errors
    clearErrors();
    
    // Store the user type for registration
    modal.dataset.userType = type;
    
    const formHtml = `
        <h2>${type === 'jobseeker' ? 'Job Seeker' : 'Recruiter'} Registration</h2>
        <form id="registration-form" class="registration-form">
            <div id="registration-error" class="error-message" style="display: none; color: red; margin-bottom: 10px;"></div>
            <div class="input-group">
                <label for="reg-name">Full Name*</label>
                <input type="text" id="reg-name" name="name" required>
            </div>
            <div class="input-group">
                <label for="reg-email">Email Address*</label>
                <input type="email" id="reg-email" name="email" required>
            </div>
            <div class="input-group">
                <label for="reg-password">Password*</label>
                <input type="password" id="reg-password" name="password" required 
                       minlength="6" title="Password must be at least 6 characters long">
            </div>
            ${type === 'jobseeker' ? `
                <div class="input-group">
                    <label for="reg-phone">Phone Number*</label>
                    <input type="tel" id="reg-phone" name="phone" required>
                </div>
                <div class="input-group">
                    <label for="reg-location">Location</label>
                    <input type="text" id="reg-location" name="location">
                </div>
            ` : `
                <div class="input-group">
                    <label for="reg-company">Company Name*</label>
                    <input type="text" id="reg-company" name="company" required>
                </div>
                <div class="input-group">
                    <label for="reg-industry">Industry*</label>
                    <select id="reg-industry" name="industry" required>
                        <option value="">Select Industry</option>
                        <option value="technology">Technology</option>
                        <option value="finance">Finance</option>
                        <option value="healthcare">Healthcare</option>
                        <option value="education">Education</option>
                        <option value="manufacturing">Manufacturing</option>
                        <option value="retail">Retail</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            `}
            <p class="form-note">* Required fields</p>
            <button type="submit" class="login-btn ${type === 'recruiter' ? 'recruiter-btn' : ''}">
                Register as ${type === 'jobseeker' ? 'Job Seeker' : 'Recruiter'}
            </button>
        </form>
    `;
    
    container.innerHTML = formHtml;
    modal.style.display = 'block';
}

function closeModal() {
    console.log('Closing registration modal');
    clearErrors();
    const modal = document.getElementById('register-modal');
    if (modal) {
        modal.style.display = 'none';
        console.log('Modal hidden');
    } else {
        console.error('Modal element not found');
    }
}

async function registerUser(event, type) {
    event.preventDefault();
    clearErrors();
    
    const formData = {
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        name: document.getElementById('reg-name').value,
        userType: type
    };

    // Validate required fields
    if (!formData.email || !formData.password || !formData.name) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.marginTop = '10px';
        errorDiv.textContent = 'Please fill in all required fields';
        document.querySelector('#register-form-container form').appendChild(errorDiv);
        return;
    }

    // Add specific fields based on user type
    if (type === 'jobseeker') {
        const phone = document.getElementById('reg-phone').value;
        if (!phone) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.color = 'red';
            errorDiv.style.marginTop = '10px';
            errorDiv.textContent = 'Phone number is required';
            document.querySelector('#register-form-container form').appendChild(errorDiv);
            return;
        }
        formData.phone = phone;
    } else {
        const company = document.getElementById('reg-company').value;
        if (!company) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.color = 'red';
            errorDiv.style.marginTop = '10px';
            errorDiv.textContent = 'Company name is required';
            document.querySelector('#register-form-container form').appendChild(errorDiv);
            return;
        }
        formData.company = company;
    }

    try {
        console.log('Starting registration process...');
        // console.log('Registration data:', formData);
        
        // Send registration request directly
        console.log('Sending registration request to server...');
        let response;
        try {
            response = await fetch('http://localhost:8000/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            console.log('Raw response received:', response);
        } catch (fetchError) {
            console.error('Fetch error:', fetchError);
            throw new Error('Network error while trying to register');
        }

        console.log('Registration response status:', response.status);
        let data;
        try {
            const textData = await response.text();
            console.log('Raw response text:', textData);
            try {
                data = JSON.parse(textData);
                console.log('Parsed registration response data:', data);
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                console.log('Failed to parse response text:', textData);
                throw new Error('Invalid response format from server');
            }
        } catch (textError) {
            console.error('Error reading response text:', textError);
            throw new Error('Error reading server response');
        }

        if (!response.ok) {
            console.log('Registration failed with status:', response.status);
            if (data.detail === "User already exists") {
                showError('registration-form', 'This email is already registered. Please use a different email or try logging in.');
            } else {
                showError('registration-form', data.detail || 'Registration failed. Please try again.');
            }
            return;
        }

        try {
            // Registration successful
            console.log('Registration successful:', data);
            
            // Close modal first
            console.log('Closing modal...');
            const modal = document.getElementById('register-modal');
            if (modal) {
                modal.style.display = 'none';
            }
            
            // Then show alert
            console.log('Showing success alert...');
            alert('Registration successful! Please login with your credentials.');
            
            // Finally switch tab and pre-fill email
            console.log('Switching to login tab and pre-filling email...');
            const emailInput = document.getElementById(type === 'jobseeker' ? 'js-email' : 'rec-email');
            if (emailInput) {
                emailInput.value = formData.email;
                console.log('Email pre-filled:', formData.email);
            }
            
            switchTabs(type);
        } catch (error) {
            console.error('Error in post-registration steps:', error);
        }
    } catch (error) {
        console.error('Registration error:', error);
        console.error('Error stack:', error.stack);
        showError('registration-form', 'Network error. Please try again.');
    }
    
    return false; // Prevent form submission
}

// Dashboard initialization and authentication

// Authentication check with backend verification
async function checkAuth() {
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (!user || !user.token) {
            window.location.href = 'index.html';
            return false;
        }

        // Verify token with backend
        const response = await fetch('http://localhost:8000/verify-token', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${user.token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Invalid token');
        }

        const data = await response.json();
        return data.user_type === user.type;
    } catch (error) {
        console.error('Authentication error:', error);
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
        return false;
    }
}

// Logout function
function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

// Sample candidate data for demonstration
if (typeof candidatesDatabase === 'undefined') {
    const candidatesDatabase = [
        {
            id: 1,
            name: "Rahul Kumar",
            email: "rahul@email.com",
            skills: ["Python", "Django", "Machine Learning", "SQL", "AWS"],
            experience: "3 years",
            location: "Bangalore",
            education: "B.Tech Computer Science",
            match: 95
        },
        {
            id: 2,
            name: "Priya Sharma",
            email: "priya@email.com",
            skills: ["React", "Node.js", "JavaScript", "MongoDB", "Express"],
            experience: "2 years",
            location: "Mumbai",
            education: "MCA",
            match: 88
        },
        {
            id: 3,
            name: "Amit Patel",
            email: "amit@email.com",
            skills: ["Java", "Spring Boot", "Microservices", "Docker", "Kubernetes"],
            experience: "4 years",
            location: "Pune",
            education: "B.Tech IT",
            match: 92
        },
        {
            id: 4,
            name: "Sneha Reddy",
            email: "sneha@email.com",
            skills: ["Python", "Flask", "Data Science", "Pandas", "NumPy"],
            experience: "1.5 years",
            location: "Hyderabad",
            education: "M.Tech Data Science",
            match: 85
        },
        {
            id: 5,
            name: "Vikash Singh",
            email: "vikash@email.com",
            skills: ["PHP", "Laravel", "MySQL", "HTML", "CSS", "JavaScript"],
            experience: "3 years",
            location: "Delhi",
            education: "BCA",
            match: 78
        },
        {
            id: 6,
            name: "Anita Gupta",
            email: "anita@email.com",
            skills: ["React Native", "Flutter", "Mobile Development", "Firebase"],
            experience: "2.5 years",
            location: "Chennai",
            education: "B.Tech CSE",
            match: 90
        }
    ];
}

// Login page functions
function switchUserType(type) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(type + '-tab').classList.add('active');
    
    // Show/hide forms
    document.querySelectorAll('.login-form').forEach(form => form.classList.remove('active'));
    document.getElementById(type + '-form').classList.add('active');
}

async function loginJobSeeker(event) {
    event.preventDefault();
    const email = document.getElementById('js-email').value;
    const password = document.getElementById('js-password').value;
    
    // Remove any previous error
    clearErrors();
    
    // Simple validation
    if (!email || !password) {
        showError('jobseeker-form', 'Please enter both email and password');
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userEmail: email,
                password: password,
                userType: 'jobseeker'
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            showError('jobseeker-form', data.detail || 'Login failed. Please check your credentials.');
            return;
        }

        if (data.success) {
            localStorage.setItem('currentUser', JSON.stringify({
                email: data.user.email,
                type: data.user.type,
                token: data.token
            }));
            window.location.href = 'jobseeker-dashboard.html';
        } else {
            showError('jobseeker-form', data.detail || 'Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('jobseeker-form', 'Network error. Please try again.');
    }
}

async function loginRecruiter(event) {
    event.preventDefault();
    const email = document.getElementById('rec-email').value;
    const password = document.getElementById('rec-password').value;
    
    // Remove any previous error
    clearErrors();
    
    // Simple validation
    if (!email || !password) {
        showError('recruiter-form', 'Please enter both email and password');
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userEmail: email,
                password: password,
                userType: 'recruiter'
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            showError('recruiter-form', data.detail || 'Login failed. Please check your credentials.');
            return;
        }

        if (data.success) {
            localStorage.setItem('currentUser', JSON.stringify({
                email: data.user.email,
                type: data.user.type,
                token: data.token
            }));
            window.location.href = 'recruiter-dashboard.html';
        } else {
            showError('recruiter-form', data.detail || 'Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('recruiter-form', 'Network error. Please try again.');
    }
}

// Register functions have been moved and combined into registerUser

function closeModal() {
    document.getElementById('register-modal').style.display = 'none';
}

// Dashboard initialization functions
async function initJobseekerDashboard() {
    if (!(await checkAuth())) return;
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (user.type !== 'jobseeker') {
            alert('Please login as a job seeker');
            // window.location.href = 'index.html';
            return;
        }
        
        const welcomeMsg = document.getElementById('welcome-message');
        if (welcomeMsg) {
            welcomeMsg.textContent = `Welcome, ${user.email}`;
        }
        
        // Initialize dashboard data
        await loadJobSeekerDashboard();
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        // window.location.href = 'index.html';
    }
}

async function initRecruiterDashboard() {
    if (!(await checkAuth())) return;
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (user.type !== 'recruiter') {
            alert('Please login as a recruiter');
            // window.location.href = 'index.html';
            return;
        }
        
        const welcomeMsg = document.getElementById('welcome-message');
        if (welcomeMsg) {
            welcomeMsg.textContent = `Welcome, ${user.email}`;
        }
        
        // Initialize dashboard data
        await loadRecruiterDashboard();
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        // window.location.href = 'index.html';
    }
}

// Helper functions for loading dashboard data
async function loadJobSeekerDashboard() {
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (!user || !user.token) {
            console.error('No user data or token found');
            window.location.replace('index.html');
            return;
        }

        console.log('Fetching dashboard data...');
        const response = await fetch('http://localhost:8000/jobseeker/dashboard', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${user.token}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('Dashboard response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Dashboard error:', errorData);
            
            if (response.status === 401 || response.status === 403) {
                // Authentication or authorization error
                localStorage.removeItem('currentUser');
                window.location.replace('index.html');
                return;
            }
            
            throw new Error(errorData.detail || 'Failed to load dashboard');
        }

        const data = await response.json();
        console.log('Dashboard data received:', data);
        
        if (data.success && data.user) {
            // Initialize skills array if it exists in user data
            window.userSkills = data.user.skills || [];
            
            // Update the UI with user data
            document.getElementById('user-name').value = data.user.name || '';
            document.getElementById('user-email').value = data.user.email || '';
            document.getElementById('user-phone').value = data.user.phone || '';
            
            // Display skills if they exist
            if (typeof displaySkills === 'function') {
                displaySkills();
            }
        }
    } catch (error) {
        console.error('Error in loadJobSeekerDashboard:', error);
        alert('Failed to load dashboard data. Please try again.');
    }
}

async function loadRecruiterDashboard() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    try {
        const response = await fetch('http://localhost:8000/recruiter/dashboard', {
            headers: {
                'Authorization': `Bearer ${user.token}`,
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            const data = await response.json();
            // Update dashboard with received data
            updateRecruiterDashboard(data);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Dashboard functions
function redirectToDashboard(userType) {
    window.location.href = userType === 'recruiter' ? 'recruiter-dashboard.html' : 'jobseeker-dashboard.html';
}



// Recruiter Dashboard Functions
function searchCandidates() {
    const searchQuery = document.getElementById('candidate-search').value.toLowerCase();
    
    if (!searchQuery.trim()) {
        alert('Please enter search criteria');
        return;
    }
    
    // Show loading
    document.getElementById('search-results').style.display = 'block';
    document.getElementById('candidates-list').innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>AI is analyzing candidates...</p>
        </div>
    `;
    
    // Simulate AI search processing
    setTimeout(() => {
        const results = performAISearch(searchQuery);
        displayCandidates(results);
    }, 2000);
}

function performAISearch(query) {
    // Simulate AI-powered hybrid search
    let matchedCandidates = candidatesDatabase.map(candidate => {
        let score = 0;
        const queryWords = query.split(' ');
        
        // Check skills match
        queryWords.forEach(word => {
            candidate.skills.forEach(skill => {
                if (skill.toLowerCase().includes(word)) {
                    score += 30;
                }
            });
            
            // Check other fields
            if (candidate.name.toLowerCase().includes(word) ||
                candidate.education.toLowerCase().includes(word) ||
                candidate.location.toLowerCase().includes(word)) {
                score += 10;
            }
        });
        
        return { ...candidate, match: Math.min(score, 100) };
    });
    
    // Filter and sort by match score
    return matchedCandidates
        .filter(candidate => candidate.match > 0)
        .sort((a, b) => b.match - a.match);
}

function displayCandidates(candidates) {
    const container = document.getElementById('candidates-list');
    
    if (candidates.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #718096;">No candidates found matching your criteria</p>';
        return;
    }
    
    let html = '';
    candidates.forEach(candidate => {
        html += `
            <div class="candidate-card">
                <div class="candidate-header">
                    <div>
                        <div class="candidate-name">${candidate.name}</div>
                        <div class="candidate-details">
                            📧 ${candidate.email} • 📍 ${candidate.location} • 🎓 ${candidate.education}
                        </div>
                    </div>
                    <div class="match-score">${candidate.match}% Match</div>
                </div>
                <div class="candidate-skills">
                    ${candidate.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                </div>
                <div class="candidate-details">
                    💼 Experience: ${candidate.experience}
                </div>
                <button class="add-to-table-btn" onclick="addToShortlist(${candidate.id})">
                    Add to Shortlist
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function addToShortlist(candidateId) {
    const candidate = candidatesDatabase.find(c => c.id === candidateId);
    
    if (candidate && !shortlistedCandidates.find(c => c.id === candidateId)) {
        shortlistedCandidates.push(candidate);
        updateShortlistDisplay();
        alert(`${candidate.name} added to shortlist!`);
    } else if (shortlistedCandidates.find(c => c.id === candidateId)) {
        alert('Candidate already in shortlist!');
    }
}

function updateShortlistDisplay() {
    const container = document.getElementById('shortlist-container');
    
    if (shortlistedCandidates.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">No candidates shortlisted yet</p>';
        return;
    }
    
    let html = '';
    shortlistedCandidates.forEach((candidate, index) => {
        html += `
            <div class="shortlist-item">
                <div>
                    <strong>${candidate.name}</strong> - ${candidate.skills.join(', ')}
                    <br>
                    <small>📧 ${candidate.email} • 📍 ${candidate.location} • Match: ${candidate.match}%</small>
                </div>
                <button class="remove-btn" onclick="removeFromShortlist(${candidate.id})">Remove</button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function removeFromShortlist(candidateId) {
    shortlistedCandidates = shortlistedCandidates.filter(c => c.id !== candidateId);
    updateShortlistDisplay();
}

function clearShortlist() {
    if (confirm('Are you sure you want to clear all shortlisted candidates?')) {
        shortlistedCandidates = [];
        updateShortlistDisplay();
    }
}

// Job Seeker Dashboard Functions
function saveProfile() {
    const name = document.getElementById('user-name').value;
    const phone = document.getElementById('user-phone').value;
    const location = document.getElementById('user-location').value;
    const experience = document.getElementById('user-experience').value;
    const education = document.getElementById('user-education').value;
    const currentRole = document.getElementById('user-current-role').value;
    
    if (!name || !phone || !location) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Save to current user object (in real app, this would be saved to database)
    currentUser.profile = {
        name, phone, location, experience, education, currentRole
    };
    
    alert('Profile saved successfully!');
}

function addSkill() {
    const skillInput = document.getElementById('skill-input');
    const skill = skillInput.value.trim();
    
    if (!skill) {
        alert('Please enter a skill');
        return;
    }
    
    if (userSkills.includes(skill)) {
        alert('Skill already added');
        return;
    }
    
    userSkills.push(skill);
    skillInput.value = '';
    displaySkills();}

function displaySkills() {
    const container = document.getElementById('skills-display');
    if (!container) return; // Guard clause if not on skills page
    
    // Initialize userSkills if not exists
    if (typeof userSkills === 'undefined') {
        window.userSkills = [];
    }
    
    if (userSkills.length === 0) {
        container.innerHTML = '<p style="color: #718096;">No skills added yet. Add your skills to improve job matching.</p>';
        return;
    }
    
    let html = '';
    userSkills.forEach((skill, index) => {
        html += `
            <div class="skill-item">
                ${skill}
                <span class="remove-skill" onclick="removeSkill(${index})">×</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function removeSkill(index) {
    userSkills.splice(index, 1);
    displaySkills();
}

function triggerFileUpload() {
    document.getElementById('resume-file').click();
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Simulate file processing
        setTimeout(() => {
            document.getElementById('uploaded-resume').style.display = 'block';
            currentUser.resume = { name: file.name, type: file.type };
        }, 1000);
    }
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf' || 
            file.type === 'application/msword' || 
            file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
            
            setTimeout(() => {
                document.getElementById('uploaded-resume').style.display = 'block';
                currentUser.resume = { name: file.name, type: file.type };
            }, 1000);
        } else {
            alert('Please upload PDF, DOC, or DOCX files only');
        }
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

function viewResume() {
    if (currentUser.resume) {
        alert(`Resume: ${currentUser.resume.name} (${currentUser.resume.type})`);
        // In real app, this would open the resume file
    }
}

function generateResume() {
    const objective = document.getElementById('resume-objective').value;
    const company = document.getElementById('resume-company').value;
    const duration = document.getElementById('resume-duration').value;
    const description = document.getElementById('resume-description').value;
    const projects = document.getElementById('resume-projects').value;
    const certifications = document.getElementById('resume-certifications').value;
    
    if (!objective || !company || !description) {
        alert('Please fill in the required fields');
        return;
    }
    
    // Simulate resume generation
    const generateBtn = document.querySelector('.generate-resume-btn');
    generateBtn.textContent = 'Generating Resume...';
    generateBtn.disabled = true;
    
    setTimeout(() => {
        alert('Resume generated successfully! You can now download it.');
        generateBtn.textContent = 'Download Resume';
        generateBtn.onclick = function() {
            downloadResume();
        };
        generateBtn.disabled = false;
        
        // Save resume data
        currentUser.generatedResume = {
            objective, company, duration, description, projects, certifications,
            skills: userSkills,
            profile: currentUser.profile
        };
    }, 3000);
}

function downloadResume() {
    if (currentUser.generatedResume) {
        // Create a simple text resume (in real app, this would generate PDF)
        const resumeContent = createResumeContent();
        const blob = new Blob([resumeContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'resume.txt';
        a.click();
        URL.revokeObjectURL(url);
    }
}

function createResumeContent() {
    const data = currentUser.generatedResume;
    const profile = currentUser.profile || {};
    
    return `
==============================================
              PROFESSIONAL RESUME
==============================================

Name: ${profile.name || 'Your Name'}
Email: ${currentUser.email}
Phone: ${profile.phone || 'Your Phone'}
Location: ${profile.location || 'Your Location'}

==============================================
CAREER OBJECTIVE
==============================================
${data.objective}

==============================================
PROFESSIONAL EXPERIENCE
==============================================
Company: ${data.company}
Duration: ${data.duration}
Role: ${profile.currentRole || 'Your Role'}

Description:
${data.description}

==============================================
TECHNICAL SKILLS
==============================================
${userSkills.join(', ') || 'Your Skills'}

==============================================
PROJECTS
==============================================
${data.projects}

==============================================
CERTIFICATIONS
==============================================
${data.certifications}

==============================================
EDUCATION
==============================================
${profile.education || 'Your Education'}

Generated by JobPortal Pro
    `;
}