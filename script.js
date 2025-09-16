// script.js - Main JavaScript File

// Global variables
let currentUser = null;
let userType = null;
let shortlistedCandidates = [];
let userSkills = [];
const backendurl = "http://localhost:3000";

// Sample candidate data for demonstration
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

// Login page functions
function switchUserType(type) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(type + '-tab').classList.add('active');
    
    // Show/hide forms
    document.querySelectorAll('.login-form').forEach(form => form.classList.remove('active'));
    document.getElementById(type + '-form').classList.add('active');
}

function loginJobSeeker(event) {
    event.preventDefault();
    const email = document.getElementById('js-email').value;
    const password = document.getElementById('js-password').value;
    fetch(backendurl+"/login", {
        method: "POST",
        body: JSON.stringify({
            userEmail: email,
            password: password
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
  .then((response) => location.href = '/jobseeker-dashboard.html') //Gets response from the backend whether login succeeded or failed
  .then((json) => console.log(json));



    // Simple validation (in real app, this would be server-side)
    if (email && password) {
        currentUser = { email: email, type: 'jobseeker' };
        userType = 'jobseeker';
        showJobSeekerDashboard();
    } else {
        alert('Please enter valid credentials');
    }
}
    
function loginRecruiter(event) {
    event.preventDefault();
    const email = document.getElementById('rec-email').value;
    const password = document.getElementById('rec-password').value;
    console.log("hi");
    
    fetch(backendurl+"/login", {
        method: "POST",
        body: JSON.stringify({
            userEmail: email,
            password: password
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
  .then((response) => location.href = '/recruiter-dashboard.html') //Gets response from the backend whether login succeeded or failed
  .then((json) => console.log(json));
    
}

function showRegisterForm(type) {
    const modal = document.getElementById('register-modal');
    const container = document.getElementById('register-form-container');
    
    let registerHTML = '';
    
    if (type === 'jobseeker') {
        registerHTML = `
            <h2>Register as Job Seeker</h2>
            <form onsubmit="registerJobSeeker(event)">
                <div class="input-group">
                    <label for="reg-name">Full Name</label>
                    <input type="text" id="reg-name" required>
                </div>
                <div class="input-group">
                    <label for="reg-email">Email Address</label>
                    <input type="email" id="reg-email" required>
                </div>
                <div class="input-group">
                    <label for="reg-password">Password</label>
                    <input type="password" id="reg-password" required>
                </div>
                <div class="input-group">
                    <label for="reg-phone">Phone Number</label>
                    <input type="tel" id="reg-phone" required>
                </div>
                <div class="input-group">
                    <label for="reg-location">Location</label>
                    <input type="text" id="reg-location" required>
                </div>
                <button type="submit" class="login-btn">Register</button>
            </form>
        `;
    } else {
        registerHTML = `
            <h2>Register as Recruiter/Company</h2>
            <form onsubmit="registerRecruiter(event)">
                <div class="input-group">
                    <label for="reg-company">Company Name</label>
                    <input type="text" id="reg-company" required>
                </div>
                <div class="input-group">
                    <label for="reg-email">Company Email</label>
                    <input type="email" id="reg-email" required>
                </div>
                <div class="input-group">
                    <label for="reg-password">Password</label>
                    <input type="password" id="reg-password" required>
                </div>
                <div class="input-group">
                    <label for="reg-website">Company Website</label>
                    <input type="url" id="reg-website">
                </div>
                <div class="input-group">
                    <label for="reg-industry">Industry</label>
                    <select id="reg-industry" required>
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
                <button type="submit" class="login-btn recruiter-btn">Register</button>
            </form>
        `;
    }
    
    container.innerHTML = registerHTML;
    modal.style.display = 'block';
}

function registerJobSeeker(event) {
    event.preventDefault();
    alert('Registration successful! Please login with your credentials.');
    closeModal();
}

function registerRecruiter(event) {
    event.preventDefault();
    alert('Registration successful! Please login with your credentials.');
    closeModal();
}

function closeModal() {
    document.getElementById('register-modal').style.display = 'none';
}

// Dashboard functions
function showRecruiterDashboard() {
    document.body.innerHTML = `
        <div class="dashboard">
            <div class="dashboard-header">
                <div class="dashboard-logo">JobPortal Pro - Recruiter</div>
                <div class="user-info">
                    <div class="user-avatar">R</div>
                    <span>Welcome, ${currentUser.email}</span>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>
            
            <div class="dashboard-content">
                <div class="search-container">
                    <h2 class="search-title">🔍 AI-Powered Candidate Search</h2>
                    <input type="text" id="candidate-search" class="search-box" 
                           placeholder="e.g., 'I want a Python programmer with machine learning skills and 3+ years experience'">
                    <button class="search-btn" onclick="searchCandidates()">Search Candidates</button>
                </div>
                
                <div id="search-results" class="results-container" style="display: none;">
                    <h3>Search Results</h3>
                    <div id="candidates-list"></div>
                </div>
                
                <div class="shortlist-table">
                    <div class="table-header">
                        <h3>📋 Shortlisted Candidates</h3>
                        <button class="clear-table-btn" onclick="clearShortlist()">Clear All</button>
                    </div>
                    <div id="shortlist-container">
                        <p style="color: #718096; text-align: center; padding: 20px;">No candidates shortlisted yet</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function showJobSeekerDashboard() {
    document.body.innerHTML = `
        <div class="dashboard">
            <div class="dashboard-header">
                <div class="dashboard-logo">JobPortal Pro - Job Seeker</div>
                <div class="user-info">
                    <div class="user-avatar">J</div>
                    <span>Welcome, ${currentUser.email}</span>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>
            
            <div class="dashboard-content">
                <div class="profile-section">
                    <h2 class="section-title">👤 Profile Management</h2>
                    <div class="profile-grid">
                        <div>
                            <div class="input-group">
                                <label for="user-name">Full Name</label>
                                <input type="text" id="user-name" placeholder="Enter your full name">
                            </div>
                            <div class="input-group">
                                <label for="user-email">Email</label>
                                <input type="email" id="user-email" value="${currentUser.email}" readonly>
                            </div>
                            <div class="input-group">
                                <label for="user-phone">Phone Number</label>
                                <input type="tel" id="user-phone" placeholder="Enter phone number">
                            </div>
                            <div class="input-group">
                                <label for="user-location">Location</label>
                                <input type="text" id="user-location" placeholder="Enter your location">
                            </div>
                        </div>
                        <div>
                            <div class="input-group">
                                <label for="user-experience">Experience (Years)</label>
                                <select id="user-experience">
                                    <option value="">Select Experience</option>
                                    <option value="0-1">0-1 years</option>
                                    <option value="1-3">1-3 years</option>
                                    <option value="3-5">3-5 years</option>
                                    <option value="5-10">5-10 years</option>
                                    <option value="10+">10+ years</option>
                                </select>
                            </div>
                            <div class="input-group">
                                <label for="user-education">Education</label>
                                <input type="text" id="user-education" placeholder="e.g., B.Tech Computer Science">
                            </div>
                            <div class="input-group">
                                <label for="user-current-role">Current Role</label>
                                <input type="text" id="user-current-role" placeholder="e.g., Software Developer">
                            </div>
                            <button class="login-btn" onclick="saveProfile()">Save Profile</button>
                        </div>
                    </div>
                </div>
                
                <div class="profile-section">
                    <h2 class="section-title">🛠️ Skills Management</h2>
                    <div class="skill-input-container">
                        <input type="text" id="skill-input" placeholder="Enter a skill (e.g., Python, JavaScript, etc.)">
                        <button class="add-skill-btn" onclick="addSkill()">Add Skill</button>
                    </div>
                    <div class="skills-display" id="skills-display">
                        <!-- Skills will be displayed here -->
                    </div>
                </div>
                
                <div class="profile-section">
                    <h2 class="section-title">📄 Resume Management</h2>
                    <div class="profile-grid">
                        <div>
                            <h3 style="margin-bottom: 15px;">Upload Resume</h3>
                            <div class="resume-upload-area" onclick="triggerFileUpload()" 
                                 ondrop="handleFileDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                                <div class="upload-icon">📁</div>
                                <p>Click to upload or drag & drop your resume</p>
                                <p style="font-size: 0.9rem; color: #718096;">PDF, DOC, DOCX files accepted</p>
                            </div>
                            <input type="file" id="resume-file" accept=".pdf,.doc,.docx" style="display: none;" onchange="handleFileUpload(event)">
                            <div id="uploaded-resume" style="display: none; margin-top: 15px;">
                                <p style="color: #48bb78;">✓ Resume uploaded successfully!</p>
                                <button class="search-btn" onclick="viewResume()">View Resume</button>
                            </div>
                        </div>
                        <div>
                            <h3 style="margin-bottom: 15px;">Create Resume</h3>
                            <div class="resume-builder">
                                <div class="form-row">
                                    <input type="text" id="resume-objective" placeholder="Career Objective">
                                </div>
                                <div class="form-row">
                                    <input type="text" id="resume-company" placeholder="Current/Previous Company">
                                    <input type="text" id="resume-duration" placeholder="Duration (e.g., 2020-2023)">
                                </div>
                                <div class="form-row">
                                    <textarea id="resume-description" placeholder="Job Description & Achievements" rows="4"></textarea>
                                </div>
                                <div class="form-row">
                                    <input type="text" id="resume-projects" placeholder="Key Projects">
                                    <input type="text" id="resume-certifications" placeholder="Certifications">
                                </div>
                                <button class="generate-resume-btn" onclick="generateResume()">Generate Resume</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    displaySkills();
}

function logout() {
    currentUser = null;
    userType = null;
    shortlistedCandidates = [];
    userSkills = [];
    location.reload();
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

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Add skill on Enter key press
    document.addEventListener('keypress', function(event) {
        if (event.target.id === 'skill-input' && event.key === 'Enter') {
            addSkill();
        }
    });
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('register-modal');
        if (event.target === modal) {
            closeModal();
        }
    };
});