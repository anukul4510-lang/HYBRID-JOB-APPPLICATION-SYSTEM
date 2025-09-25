async function searchCandidates() {
    const searchInput = document.getElementById('candidate-search');
    const resultsContainer = document.getElementById('search-results');
    const candidatesList = document.getElementById('candidates-list');

    if (!searchInput || !resultsContainer || !candidatesList) {
        console.error("One or more elements not found for candidate search.");
        return;
    }

    const query = searchInput.value;
    if (!query) {
        alert('Please enter a search query.');
        return;
    }

    // Show loading state
    resultsContainer.style.display = 'block';
    candidatesList.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">Searching...</p>';

    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        const response = await fetch('http://localhost:8000/search/candidates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${user.token}`
            },
            body: JSON.stringify({ query: query })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                renderCandidates(data.results);
            } else {
                candidatesList.innerHTML = `<p style="color: red; text-align: center; padding: 20px;">Error: ${data.detail}</p>`;
            }
        } else {
            const errorText = await response.text();
            candidatesList.innerHTML = `<p style="color: red; text-align: center; padding: 20px;">Failed to fetch results: ${errorText}</p>`;
        }
    } catch (error) {
        console.error('Error searching candidates:', error);
        candidatesList.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">An error occurred. Please try again later.</p>';
    }
}

function renderCandidates(candidates) {
    const candidatesList = document.getElementById('candidates-list');
    if (!candidatesList) return;

    if (candidates.length === 0) {
        candidatesList.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">No candidates found matching your query.</p>';
        return;
    }

    candidatesList.innerHTML = candidates.map(candidate => `
        <div class="candidate-card">
            <div class="candidate-header">
                <div class="candidate-name">${candidate.name}</div>
            </div>
            <div class="candidate-details">
                <p><strong>Email:</strong> ${candidate.email}</p>
                <p><strong>Phone:</strong> ${candidate.phone || 'N/A'}</p>
                <p><strong>Location:</strong> ${candidate.location || 'N/A'}</p>
                <p><strong>Experience:</strong> ${candidate.experience_level || 'N/A'}</p>
                <p><strong>Education:</strong> ${candidate.education || 'N/A'}</p>
            </div>
        </div>
    `).join('');
}

// Dashboard initialization functions
async function initJobseekerDashboard() {
    try {
        if (!(await checkAuth())) {
            return;
        }

        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (user.type !== 'jobseeker') {
            alert('Access denied. Please login as a job seeker.');
            window.location.href = 'index.html';
            return;
        }

        document.getElementById('welcome-message').textContent = `Welcome, ${user.email}`;
        
        // Load dashboard data
        try {
            const response = await fetch('http://localhost:8000/jobseeker/dashboard', {
                headers: {
                    'Authorization': `Bearer ${user.token}`
                }
            });
            
            if (response.ok) {
                const dashboardData = await response.json();
                // Update dashboard UI with the received data
                updateDashboardUI(dashboardData);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        window.location.href = 'index.html';
    }
}

async function initRecruiterDashboard() {
    try {
        if (!(await checkAuth())) {
            return;
        }

        const user = JSON.parse(localStorage.getItem('currentUser'));
        if (user.type !== 'recruiter') {
            alert('Access denied. Please login as a recruiter.');
            window.location.href = 'index.html';
            return;
        }

        document.getElementById('welcome-message').textContent = `Welcome, ${user.email}`;
        
        // Load dashboard data
        try {
            const response = await fetch('http://localhost:8000/recruiter/dashboard', {
                headers: {
                    'Authorization': `Bearer ${user.token}`
                }
            });
            
            if (response.ok) {
                const dashboardData = await response.json();
                // Update dashboard UI with the received data
                updateRecruiterDashboardUI(dashboardData);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        window.location.href = 'index.html';
    }
}

// Helper function to update dashboard UI
function updateDashboardUI(data) {
    // Update profile information if available
    if (data.profile) {
        const { name, phone, location, education } = data.profile;
        document.getElementById('user-name').value = name || '';
        document.getElementById('user-phone').value = phone || '';
        document.getElementById('user-location').value = location || '';
        document.getElementById('user-education').value = education || '';
    }

    // Update skills if available
    if (data.skills && Array.isArray(data.skills)) {
        userSkills = data.skills;
        updateSkillsDisplay();
    }
}

function updateRecruiterDashboardUI(data) {
    // Update company information if available
    if (data.company) {
        const { name, industry, website } = data.company;
        document.getElementById('company-name').value = name || '';
        document.getElementById('company-industry').value = industry || '';
        document.getElementById('company-website').value = website || '';
    }

    // Update job postings if available
    if (data.jobPostings && Array.isArray(data.jobPostings)) {
        updateJobPostings(data.jobPostings);
    }

    // Load applications
    loadRecruiterApplications();
}

async function loadRecruiterApplications() {
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        const response = await fetch('http://localhost:8000/recruiter/applications', {
            headers: {
                'Authorization': `Bearer ${user.token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                renderApplications(data.applications);
            }
        } else {
            console.error('Failed to load applications:', await response.text());
        }
    } catch (error) {
        console.error('Error loading applications:', error);
    }
}

function renderApplications(applications) {
    const applicationsList = document.getElementById('applications-list');
    if (!applicationsList) return;

    if (applications.length === 0) {
        applicationsList.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">No applications received yet.</p>';
        return;
    }

    applicationsList.innerHTML = applications.map(app => `
        <div class="candidate-card">
            <div class="candidate-header">
                <div class="candidate-name">${app.jobseeker.name}</div>
                <div class="match-score">${app.job.title}</div>
            </div>
            <div class="candidate-details">
                <p><strong>Email:</strong> ${app.jobseeker.email}</p>
                <p><strong>Phone:</strong> ${app.jobseeker.phone}</p>
                <p><strong>Applied on:</strong> ${new Date(app.application_date).toLocaleDateString()}</p>
            </div>
        </div>
    `).join('');
}

function searchJobs() {
    const searchInput = document.getElementById('job-search-input');
    const locationFilter = document.getElementById('filter-location');
    const companyFilter = document.getElementById('filter-company');
    const salaryFilter = document.getElementById('filter-salary');
    const jobListings = document.getElementById('job-listings');

    if (!searchInput || !locationFilter || !companyFilter || !salaryFilter || !jobListings) {
        console.error("One or more elements not found for job search.");
        return;
    }

    const query = searchInput.value.toLowerCase();
    const location = locationFilter.value.toLowerCase();
    const company = companyFilter.value.toLowerCase();
    const salary = salaryFilter.value;

    const allJobs = [
        { id: 1, title: 'Software Engineer', company: 'Google', location: 'new york', salary: 120000, experience: 'mid', skills: ['javascript', 'react', 'nodejs'] },
        { id: 2, title: 'Frontend Developer', company: 'Facebook', location: 'san francisco', salary: 110000, experience: 'mid', skills: ['html', 'css', 'javascript', 'react'] },
        { id: 3, title: 'Data Scientist', company: 'Amazon', location: 'remote', salary: 130000, experience: 'senior', skills: ['python', 'pandas', 'sql'] },
        { id: 4, title: 'UX Designer', company: 'Apple', location: 'london', salary: 90000, experience: 'entry', skills: ['figma', 'sketch', 'photoshop'] },
        { id: 5, title: 'Product Manager', company: 'Microsoft', location: 'remote', salary: 140000, experience: 'senior', skills: ['agile', 'scrum', 'jira'] },
        { id: 6, title: 'Marketing Manager', company: 'Netflix', location: 'london', salary: 100000, experience: 'mid', skills: ['seo', 'sem', 'google analytics'] },
    ];

    const filteredJobs = allJobs.filter(job => {
        const titleMatch = job.title.toLowerCase().includes(query);
        const companyMatch = company ? job.company.toLowerCase().includes(company) : true;
        const locationMatch = location ? job.location.toLowerCase().includes(location) : true;
        const salaryMatch = salary ? job.salary >= parseInt(salary) : true;

        return titleMatch && companyMatch && locationMatch && salaryMatch;
    });

    renderJobListings(filteredJobs);
}

function renderJobListings(jobs) {
    const jobListings = document.getElementById('job-listings');
    jobListings.innerHTML = '';

    if (jobs.length === 0) {
        jobListings.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">No job listings found. Try adjusting your search criteria.</p>';
        return;
    }

    jobs.forEach(job => {
        const jobCard = document.createElement('div');
        jobCard.classList.add('candidate-card'); // Reusing candidate-card style
        jobCard.innerHTML = `
            <div class="candidate-header">
                <div class="candidate-name">${job.title}</div>
                <div class="match-score">${job.company}</div>
            </div>
            <div class="candidate-details">
                <p><strong>Location:</strong> ${job.location}</p>
                <p><strong>Salary:</strong> ${job.salary.toLocaleString()}</p>
                <p><strong>Experience:</strong> ${job.experience}</p>
                <p><strong>Skills:</strong> ${job.skills.join(', ')}</p>
            </div>
            <div class="job-card-buttons">
                <button class="search-btn">View Details</button>
                <button class="add-to-table-btn" onclick="applyForJob(${job.id})">Apply Now</button>
            </div>
        `;
        jobListings.appendChild(jobCard);
    });
}

async function applyForJob(jobId) {
    try {
        const user = JSON.parse(localStorage.getItem('currentUser'));
        const response = await fetch('http://localhost:8000/jobseeker/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${user.token}`
            },
            body: JSON.stringify({ job_id: jobId, jobseeker_email: user.email, application_date: new Date().toISOString() })
        });

        if (response.ok) {
            alert('Application submitted successfully!');
        } else {
            const errorData = await response.json();
            alert(`Failed to apply: ${errorData.detail}`);
        }
    } catch (error) {
        console.error('Failed to apply for job:', error);
        alert('An error occurred while applying for the job. Please try again later.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const createJobBtn = document.getElementById('create-job-btn');
    const modal = document.getElementById('post-job-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');

    if (createJobBtn) {
        createJobBtn.addEventListener('click', () => {
            modal.style.display = 'block';
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    // Multi-step form logic
    const multiStepForm = document.getElementById('multi-step-job-form');
    if (multiStepForm) {
        const steps = Array.from(multiStepForm.querySelectorAll('.form-step'));
        const nextBtns = Array.from(multiStepForm.querySelectorAll('.next-btn'));
        const prevBtns = Array.from(multiStepForm.querySelectorAll('.prev-btn'));
        const stepIndicators = Array.from(document.querySelectorAll('.step-indicator'));

        let currentStep = 0;

        nextBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (validateStep(currentStep)) {
                    currentStep++;
                    showStep(currentStep);
                }
            });
        });

        prevBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                currentStep--;
                showStep(currentStep);
            });
        });

        function showStep(stepIndex) {
            steps.forEach((step, index) => {
                step.classList.toggle('active', index === stepIndex);
            });
            stepIndicators.forEach((indicator, index) => {
                indicator.classList.toggle('active', index === stepIndex);
            });

            if (stepIndex === 2) { // Review step
                generateSummary();
            }
        }

        function validateStep(stepIndex) {
            const currentStepElement = steps[stepIndex];
            const inputs = Array.from(currentStepElement.querySelectorAll('input[required], select[required]'));
            let isValid = true;
            let missingFields = [];
            inputs.forEach(input => {
                if (!input.value) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    missingFields.push(input.previousElementSibling.textContent);
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!isValid) {
                alert(`Please fill out the following required fields: ${missingFields.join(', ')}`);
            }
            return isValid;
        }

        // Quill editor
        const editor = new Quill('#editor-container', {
            theme: 'snow',
            placeholder: 'Enter job description...'
        });

        // Skills input
        const skillsInput = document.getElementById('multi-required-skills');
        const skillsTagsContainer = document.querySelector('.skills-tags');
        let skills = [];

        skillsInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && skillsInput.value.trim() !== '') {
                e.preventDefault();
                const skill = skillsInput.value.trim();
                if (!skills.includes(skill)) {
                    skills.push(skill);
                    renderSkills();
                }
                skillsInput.value = '';
            }
        });

        function renderSkills() {
            skillsTagsContainer.innerHTML = '';
            skills.forEach(skill => {
                const tag = document.createElement('div');
                tag.classList.add('skill-tag');
                tag.innerHTML = `
                    <span>${skill}</span>
                    <span class="remove-skill" data-skill="${skill}">&times;</span>
                `;
                skillsTagsContainer.appendChild(tag);
            });
        }

        skillsTagsContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-skill')) {
                const skillToRemove = e.target.dataset.skill;
                skills = skills.filter(skill => skill !== skillToRemove);
                renderSkills();
            }
        });

        // Salary range sliders
        const minSalarySlider = document.getElementById('min-salary');
        const maxSalarySlider = document.getElementById('max-salary');
        const minSalaryValue = document.getElementById('min-salary-value');
        const maxSalaryValue = document.getElementById('max-salary-value');

        minSalarySlider.addEventListener('input', () => {
            minSalaryValue.textContent = `${parseInt(minSalarySlider.value).toLocaleString()}`;
            if (parseInt(minSalarySlider.value) > parseInt(maxSalarySlider.value)) {
                maxSalarySlider.value = minSalarySlider.value;
                maxSalaryValue.textContent = `${parseInt(maxSalarySlider.value).toLocaleString()}`;
            }
        });

        maxSalarySlider.addEventListener('input', () => {
            maxSalaryValue.textContent = `${parseInt(maxSalarySlider.value).toLocaleString()}`;
            if (parseInt(maxSalarySlider.value) < parseInt(minSalarySlider.value)) {
                minSalarySlider.value = maxSalarySlider.value;
                minSalaryValue.textContent = `${parseInt(minSalarySlider.value).toLocaleString()}`;
            }
        });

        // Generate summary
        function generateSummary() {
            const summaryContent = document.getElementById('summary-content');
            const jobTitle = document.getElementById('multi-job-title').value;
            const location = document.getElementById('multi-location').value;
            const employmentType = document.getElementById('multi-employment-type').value;
            const description = editor.root.innerHTML;
            const minSalary = minSalarySlider.value;
            const maxSalary = maxSalarySlider.value;

            summaryContent.innerHTML = `
                <p><strong>Job Title:</strong> ${jobTitle}</p>
                <p><strong>Location:</strong> ${location}</p>
                <p><strong>Employment Type:</strong> ${employmentType}</p>
                <p><strong>Skills:</strong> ${skills.join(', ')}</p>
                <p><strong>Salary Range:</strong> ${parseInt(minSalary).toLocaleString()} - ${parseInt(maxSalary).toLocaleString()}</p>
                <div><strong>Job Description:</strong> ${description}</div>
            `;
        }

        multiStepForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('title', document.getElementById('multi-job-title').value);
            formData.append('location', document.getElementById('multi-location').value);
            formData.append('employmentType', document.getElementById('multi-employment-type').value);
            formData.append('description', editor.root.innerHTML);
            formData.append('skills', JSON.stringify(skills));
            formData.append('minSalary', minSalarySlider.value);
            formData.append('maxSalary', maxSalarySlider.value);

            try {
                const user = JSON.parse(localStorage.getItem('currentUser'));
                const response = await fetch('http://localhost:8000/recruiter/jobs', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${user.token}`
                    },
                    body: formData
                });

                if (response.ok) {
                    alert('Job posted successfully!');
                    modal.style.display = 'none';
                    multiStepForm.reset();
                    editor.setText('');
                    skills = [];
                    renderSkills();
                    currentStep = 0;
                    showStep(0);
                } else {
                    const errorData = await response.json();
                    alert(`Failed to post job: ${errorData.detail}`);
                }
            } catch (error) {
                console.error('Failed to post job:', error);
                alert('An error occurred while posting the job. Please try again later.');
            }
        });
    }

    // Initial search for jobs on job seeker dashboard
    if(document.getElementById('search-jobs-btn')) {
        searchJobs();
    }

    // My Applications
    const applicationsList = document.getElementById('my-applications-list');
    const noApplicationsMessage = document.getElementById('no-applications-message');

    if (applicationsList && noApplicationsMessage) {
        if (applicationsList.children.length === 0) {
            noApplicationsMessage.style.display = 'block';
        } else {
            noApplicationsMessage.style.display = 'none';
        }
    }
});