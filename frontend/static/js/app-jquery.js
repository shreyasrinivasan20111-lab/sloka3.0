// Student Course Management System - jQuery Implementation
// Modern, clean jQuery code with best practices

(function($) {
    'use strict';

    // ==================== Configuration ====================
    const API_BASE = '/api';

    // ==================== State Management ====================
    const AppState = {
        currentUser: null,
        currentView: 'login',
        courses: [],
        students: [],
        quillEditor: null,
        lyricsEditor: null,
        audioEditor: null,
        editingCourse: null,
        viewingCourse: null,
        assigningCourse: null
    };

    // ==================== API Service ====================
    const API = {
        // Generic AJAX call with error handling
        call: function(endpoint, options = {}) {
            const settings = $.extend({
                url: API_BASE + endpoint,
                method: 'GET',
                dataType: 'json',
                xhrFields: { withCredentials: true },
                contentType: 'application/json'
            }, options);

            const request = $.ajax(settings);
            
            // Handle failures without throwing errors that cause "[object Object]"
            request.fail(function(xhr) {
                const error = {
                    message: xhr.responseJSON?.error || `HTTP Error ${xhr.status}`,
                    status: xhr.status,
                    url: settings.url,
                    response: xhr.responseJSON,
                    type: 'API Error'
                };
                ErrorHandler.show(error);
                console.error('API Call Failed:', error);
            });
            
            return request;
        },

        // Authentication
        login: function(email, password) {
            return this.call('/login', {
                method: 'POST',
                data: JSON.stringify({ email, password })
            });
        },

        signup: function(email, password) {
            return this.call('/signup', {
                method: 'POST',
                data: JSON.stringify({ email, password })
            });
        },

        logout: function() {
            return this.call('/logout', { method: 'POST' });
        },

        checkAuth: function() {
            return this.call('/check-auth');
        },

        // Courses
        getCourses: function() {
            return this.call('/courses');
        },

        getCourse: function(id) {
            return this.call(`/courses/${id}`);
        },

        createCourse: function(courseData) {
            return this.call('/courses', {
                method: 'POST',
                data: JSON.stringify(courseData)
            });
        },

        updateCourse: function(id, courseData) {
            return this.call(`/courses/${id}`, {
                method: 'PUT',
                data: JSON.stringify(courseData)
            });
        },

        deleteCourse: function(id) {
            return this.call(`/courses/${id}`, { method: 'DELETE' });
        },

        // Students & Assignments
        getStudents: function() {
            return this.call('/students');
        },

        getCourseAssignments: function(courseId) {
            return this.call(`/courses/${courseId}/assignments`);
        },

        assignCourse: function(courseId, studentIds) {
            return this.call(`/courses/${courseId}/assign`, {
                method: 'POST',
                data: JSON.stringify({ student_ids: studentIds })
            });
        },

        // Files
        uploadFile: function(courseId, file) {
            const formData = new FormData();
            formData.append('file', file);

            return $.ajax({
                url: `${API_BASE}/courses/${courseId}/upload`,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                xhrFields: { withCredentials: true }
            });
        },

        deleteFile: function(fileId) {
            return this.call(`/files/${fileId}`, { method: 'DELETE' });
        },

        getFileDownloadUrl: function(fileId) {
            return `${API_BASE}/files/${fileId}/download`;
        }
    };

    // ==================== Error Handler ====================
    const ErrorHandler = {
        currentError: null,

        show: function(error) {
            this.currentError = error;

            console.error('Error:', error);

            $('#error-message-text').text(error.message || 'An unknown error occurred');
            $('#error-type').text(error.type || 'Error');
            $('#error-timestamp').text(new Date().toLocaleString());
            $('#error-url').text(error.url || 'N/A');
            $('#error-status').text(error.status || 'N/A');

            if (error.stack) {
                $('#error-stack').text(error.stack);
                $('#error-stack-section').show();
            } else {
                $('#error-stack-section').hide();
            }

            if (error.response) {
                $('#error-response').text(JSON.stringify(error.response, null, 2));
                $('#error-response-section').show();
            } else {
                $('#error-response-section').hide();
            }

            $('#error-details').hide();
            $('#error-widget').fadeIn(300);
        },

        close: function() {
            $('#error-widget').fadeOut(300);
        },

        toggleDetails: function() {
            $('#error-details').slideToggle(300);
            const $btn = $('#toggle-error-details');
            $btn.text($btn.text() === 'Show Details' ? 'Hide Details' : 'Show Details');
        },

        copyToClipboard: function() {
            const errorText = `
ERROR DETAILS
=============
Message: ${this.currentError.message}
Type: ${this.currentError.type || 'Error'}
Timestamp: ${new Date().toLocaleString()}
${this.currentError.url ? `URL: ${this.currentError.url}` : ''}
${this.currentError.status ? `Status Code: ${this.currentError.status}` : ''}
${this.currentError.stack ? `Stack Trace:\n${this.currentError.stack}` : ''}
            `.trim();

            navigator.clipboard.writeText(errorText).then(function() {
                MessageHandler.show('Error details copied to clipboard!');
            });
        }
    };

    // ==================== Message Handler ====================
    const MessageHandler = {
        show: function(message, type = 'success') {
            const $toast = $('<div>')
                .addClass('message-toast')
                .addClass(type)
                .text(message)
                .appendTo('body')
                .fadeIn(300);

            setTimeout(function() {
                $toast.fadeOut(300, function() {
                    $(this).remove();
                });
            }, 3000);
        }
    };

    // ==================== View Manager ====================
    const ViewManager = {
        show: function(viewName) {
            $('.view').hide();
            $(`#${viewName}-view`).fadeIn(300);
            AppState.currentView = viewName;
        },

        showLogin: function() {
            this.show('login');
            $('#login-email').focus();
        },

        showSignup: function() {
            this.show('signup');
            $('#signup-email').focus();
        },

        showAdminDashboard: function() {
            this.show('admin');
            $('#admin-user-email').text(AppState.currentUser.email);
            CourseManager.loadCourses();
        },

        showStudentDashboard: function() {
            this.show('student');
            $('#student-user-email').text(AppState.currentUser.email);
            CourseManager.loadCourses();
        }
    };

    // ==================== Authentication ====================
    const Auth = {
        init: function() {
            // Login form
            $('#login-form').on('submit', function(e) {
                e.preventDefault();
                const email = $('#login-email').val();
                const password = $('#login-password').val();
                Auth.login(email, password);
            });

            // Signup form
            $('#signup-form').on('submit', function(e) {
                e.preventDefault();
                const email = $('#signup-email').val();
                const password = $('#signup-password').val();
                const confirmPassword = $('#signup-confirm-password').val();

                if (password !== confirmPassword) {
                    ErrorHandler.show({ message: 'Passwords do not match', type: 'Validation Error' });
                    return;
                }

                if (password.length < 6) {
                    ErrorHandler.show({ message: 'Password must be at least 6 characters', type: 'Validation Error' });
                    return;
                }

                Auth.signup(email, password);
            });

            // Logout buttons
            $(document).on('click', '.logout-btn', function() {
                Auth.logout();
            });

            // Navigation links
            $('#show-signup').on('click', function(e) {
                e.preventDefault();
                ViewManager.showSignup();
            });

            $('#show-login').on('click', function(e) {
                e.preventDefault();
                ViewManager.showLogin();
            });

            // Check authentication on load
            this.checkAuth();
        },

        login: function(email, password) {
            const $btn = $('#login-form button[type="submit"]');
            $btn.prop('disabled', true).text('Logging in...');

            // Use enhanced auth handler if available
            if (window.authHandler && window.authHandler.login) {
                window.authHandler.login(email, password)
                    .then(function(result) {
                        AppState.currentUser = result.user;
                        MessageHandler.show('Login successful!');

                        if (result.user.role === 'admin') {
                            ViewManager.showAdminDashboard();
                        } else {
                            ViewManager.showStudentDashboard();
                        }
                    })
                    .catch(function(error) {
                        MessageHandler.show(error.message || 'Login failed', 'error');
                    })
                    .finally(function() {
                        $btn.prop('disabled', false).text('Login');
                    });
            } else {
                // Fallback to original API call
                API.login(email, password)
                    .done(function(result) {
                        AppState.currentUser = result.user;
                        MessageHandler.show('Login successful!');

                        if (result.user.role === 'admin') {
                            ViewManager.showAdminDashboard();
                        } else {
                            ViewManager.showStudentDashboard();
                        }
                    })
                    .fail(function() {
                        // Error already handled by API.call
                    })
                    .always(function() {
                        $btn.prop('disabled', false).text('Login');
                        $('#login-password').val('');
                    });
            }
        },

        signup: function(email, password) {
            const $btn = $('#signup-form button[type="submit"]');
            $btn.prop('disabled', true).text('Signing up...');

            // Use enhanced auth handler if available
            if (window.authHandler && window.authHandler.signup) {
                window.authHandler.signup(email, password)
                    .then(function(result) {
                        AppState.currentUser = result.user;
                        MessageHandler.show('Signup successful! You are now logged in.');
                        ViewManager.showStudentDashboard();
                    })
                    .catch(function(error) {
                        MessageHandler.show(error.message || 'Signup failed', 'error');
                    })
                    .finally(function() {
                        $btn.prop('disabled', false).text('Sign Up');
                        $('#signup-form')[0].reset();
                    });
            } else {
                // Fallback to original API call
                API.signup(email, password)
                    .done(function(result) {
                        AppState.currentUser = result.user;
                        MessageHandler.show('Signup successful! You are now logged in.');
                        ViewManager.showStudentDashboard();
                    })
                    .fail(function() {
                        // Error already shown by API.call
                    })
                    .always(function() {
                        $btn.prop('disabled', false).text('Sign Up');
                        $('#signup-form')[0].reset();
                    });
            }
        },

        logout: function() {
            // Use enhanced auth handler if available
            if (window.authHandler && window.authHandler.logout) {
                window.authHandler.logout();
            } else {
                // Fallback to original API call
                API.logout()
                    .done(function() {
                        AppState.currentUser = null;
                        MessageHandler.show('Logged out successfully');
                        ViewManager.showLogin();
                    })
                    .fail(function() {
                        // Still clear user and redirect on failure
                        AppState.currentUser = null;
                        ViewManager.showLogin();
                    });
            }
        },

        checkAuth: function() {
            API.checkAuth()
                .done(function(data) {
                    if (data.authenticated) {
                        AppState.currentUser = data.user;
                        if (data.user.role === 'admin') {
                            ViewManager.showAdminDashboard();
                        } else {
                            ViewManager.showStudentDashboard();
                        }
                    } else {
                        ViewManager.showLogin();
                    }
                })
                .fail(function() {
                    ViewManager.showLogin();
                });
        }
    };

    // ==================== Course Manager ====================
    const CourseManager = {
        init: function() {
            // Create course button
            $('#create-course-btn').on('click', function() {
                CourseManager.showCourseEditor();
            });

            // Course editor save
            $('#save-course-btn').on('click', function() {
                CourseManager.saveCourse();
            });

            // Course editor cancel
            $('#cancel-course-editor').on('click', function() {
                CourseManager.hideCourseEditor();
            });

            // File upload
            $('#course-file-input').on('change', function() {
                CourseManager.uploadFile();
            });

            // Course view close
            $('#close-course-view').on('click', function() {
                CourseManager.hideCourseView();
            });

            // Event delegation for dynamic buttons
            $(document).on('click', '.view-course-btn', function() {
                const courseId = $(this).data('course-id');
                CourseManager.viewCourse(courseId);
            });

            $(document).on('click', '.edit-course-btn', function() {
                const courseId = $(this).data('course-id');
                CourseManager.editCourse(courseId);
            });

            $(document).on('click', '.delete-course-btn', function() {
                const courseId = $(this).data('course-id');
                const courseTitle = $(this).data('course-title');
                try {
                    CourseManager.deleteCourse(courseId, courseTitle);
                } catch (error) {
                    console.error('Error in delete course handler:', error);
                    ErrorHandler.show({
                        message: 'Failed to delete course: ' + (error.message || error),
                        type: 'Delete Error'
                    });
                }
            });

            $(document).on('click', '.assign-course-btn', function() {
                const courseId = $(this).data('course-id');
                const courseTitle = $(this).data('course-title');
                CourseManager.showAssignmentModal(courseId, courseTitle);
            });

            $(document).on('click', '.delete-file-btn', function() {
                const fileId = $(this).data('file-id');
                CourseManager.deleteFile(fileId);
            });
        },

        loadCourses: function() {
            const isAdmin = AppState.currentUser && AppState.currentUser.role === 'admin';

            // Use correct IDs based on role
            const loadingId = isAdmin ? '#courses-loading' : '#courses-loading-student';
            const gridId = isAdmin ? '#courses-grid' : '#courses-grid-student';
            const emptyId = isAdmin ? '#courses-empty' : '#courses-empty-student';

            $(loadingId).show();
            $(gridId).empty();
            $(emptyId).hide();

            API.getCourses()
                .done(function(data) {
                    AppState.courses = data.courses || [];
                    CourseManager.renderCourses();
                })
                .fail(function() {
                    $(loadingId).hide();
                });
        },

        renderCourses: function() {
            const isAdmin = AppState.currentUser.role === 'admin';

            // Use correct IDs based on role
            const loadingId = isAdmin ? '#courses-loading' : '#courses-loading-student';
            const gridId = isAdmin ? '#courses-grid' : '#courses-grid-student';
            const emptyId = isAdmin ? '#courses-empty' : '#courses-empty-student';

            $(loadingId).hide();
            const $grid = $(gridId).empty();

            if (AppState.courses.length === 0) {
                $(emptyId).show();
                return;
            }

            $(emptyId).hide();

            AppState.courses.forEach(function(course) {
                const $card = $(`
                    <div class="course-card">
                        <h3>${$('<div>').text(course.title).html()}</h3>
                        <p class="course-description">${$('<div>').text(course.description || '').html()}</p>
                        <p class="course-meta">
                            Created: ${new Date(course.created_at).toLocaleDateString()}
                        </p>
                        <div class="course-actions">
                            <button class="btn btn-primary btn-sm view-course-btn" data-course-id="${course.id}">
                                View
                            </button>
                            ${isAdmin ? `
                                <button class="btn btn-secondary btn-sm edit-course-btn" data-course-id="${course.id}">
                                    Edit
                                </button>
                                <button class="btn btn-secondary btn-sm assign-course-btn"
                                        data-course-id="${course.id}"
                                        data-course-title="${$('<div>').text(course.title).html()}">
                                    Assign Students
                                </button>
                                <button class="btn btn-danger btn-sm delete-course-btn"
                                        data-course-id="${course.id}"
                                        data-course-title="${$('<div>').text(course.title).html()}">
                                    Delete
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `);
                $grid.append($card);
            });
        },

        showCourseEditor: function(courseId = null) {
            AppState.editingCourse = courseId;

            if (courseId) {
                // Editing existing course
                $('#course-editor-title-text').text('Edit Course');
                const course = AppState.courses.find(c => c.id === courseId);
                if (course) {
                    $('#course-title').val(course.title);
                    $('#course-description').val(course.description);

                    if (AppState.lyricsEditor) {
                        AppState.lyricsEditor.root.innerHTML = course.lyrics || course.content_richtext || '';
                    }
                    
                    if (AppState.audioEditor) {
                        AppState.audioEditor.root.innerHTML = course.audio || '';
                    }

                    // Load and show files
                    API.getCourse(courseId).done(function(data) {
                        CourseManager.renderCourseFiles(data.course.files || []);
                        $('#course-files-section').show();
                    });
                } else {
                    $('#course-files-section').hide();
                }
            } else {
                // Creating new course
                $('#course-editor-title-text').text('Create Course');
                $('#course-editor-form')[0].reset();
                if (AppState.lyricsEditor) {
                    AppState.lyricsEditor.root.innerHTML = '';
                }
                if (AppState.audioEditor) {
                    AppState.audioEditor.root.innerHTML = '';
                }
                $('#course-files-list').empty();
                $('#course-files-section').hide();
            }

            // Initialize Quill editors if not already
            if (!AppState.lyricsEditor && window.Quill) {
                AppState.lyricsEditor = new Quill('#lyrics-editor-container', {
                    theme: 'snow',
                    modules: {
                        toolbar: [
                            [{ 'header': [1, 2, 3, false] }],
                            ['bold', 'italic', 'underline'],
                            ['link'],
                            [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                            ['clean']
                        ]
                    }
                });
            }
            
            if (!AppState.audioEditor && window.Quill) {
                AppState.audioEditor = new Quill('#audio-editor-container', {
                    theme: 'snow',
                    modules: {
                        toolbar: [
                            [{ 'header': [1, 2, 3, false] }],
                            ['bold', 'italic', 'underline'],
                            ['link', 'image'],
                            [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                            ['clean']
                        ]
                    }
                });
            }
            
            // Keep old quillEditor for backward compatibility with content_richtext
            if (!AppState.quillEditor && AppState.lyricsEditor) {
                AppState.quillEditor = AppState.lyricsEditor;
            }

            $('#course-editor-modal').fadeIn(300);
        },

        hideCourseEditor: function() {
            $('#course-editor-modal').fadeOut(300);
            AppState.editingCourse = null;
        },

        saveCourse: function() {
            const title = $('#course-title').val().trim();
            const description = $('#course-description').val().trim();
            const content_richtext = AppState.quillEditor ? AppState.quillEditor.root.innerHTML : '';
            const lyrics = AppState.lyricsEditor ? AppState.lyricsEditor.root.innerHTML : '';
            const audio = AppState.audioEditor ? AppState.audioEditor.root.innerHTML : '';

            if (!title) {
                ErrorHandler.show({ message: 'Course title is required', type: 'Validation Error' });
                return;
            }

            const courseData = { title, description, content_richtext, lyrics, audio };
            const $btn = $('#save-course-btn');
            $btn.prop('disabled', true).text('Saving...');

            const apiCall = AppState.editingCourse
                ? API.updateCourse(AppState.editingCourse, courseData)
                : API.createCourse(courseData);

            apiCall
                .done(function() {
                    MessageHandler.show(AppState.editingCourse ? 'Course updated successfully!' : 'Course created successfully!');
                    CourseManager.hideCourseEditor();
                    CourseManager.loadCourses();
                })
                .fail(function() {
                    // Error already shown
                })
                .always(function() {
                    $btn.prop('disabled', false).text('Save Course');
                });
        },

        deleteCourse: function(courseId, courseTitle) {
            if (!confirm(`Are you sure you want to delete "${courseTitle}"?`)) {
                return;
            }

            API.deleteCourse(courseId)
                .done(function() {
                    MessageHandler.show('Course deleted successfully!');
                    CourseManager.loadCourses();
                })
                .fail(function(xhr, textStatus, errorThrown) {
                    // Error is already shown by API.call, but we can handle specific cases
                    console.error('Delete course failed:', {
                        status: xhr.status,
                        error: xhr.responseJSON?.error,
                        textStatus: textStatus
                    });
                });
        },

        editCourse: function(courseId) {
            CourseManager.showCourseEditor(courseId);
        },

        viewCourse: function(courseId) {
            API.getCourse(courseId)
                .done(function(data) {
                    const course = data.course;
                    $('#course-view-title').text(course.title);
                    $('#course-view-meta').text(`Created: ${new Date(course.created_at).toLocaleDateString()}`);

                    if (course.description) {
                        $('#course-view-description').html(`<h3>Description</h3><p>${$('<div>').text(course.description).html()}</p>`).show();
                    } else {
                        $('#course-view-description').hide();
                    }

                    if (course.lyrics) {
                        $('#course-view-lyrics').html(`<h3>Lyrics</h3><div class="course-content">${course.lyrics}</div>`).show();
                    } else {
                        $('#course-view-lyrics').hide();
                    }

                    if (course.audio) {
                        $('#course-view-audio').html(`<h3>Audio Content</h3><div class="course-content">${course.audio}</div>`).show();
                    } else {
                        $('#course-view-audio').hide();
                    }

                    // Keep backward compatibility with content_richtext
                    if (course.content_richtext && !course.lyrics && !course.audio) {
                        $('#course-view-content').html(`<h3>Content</h3><div class="course-content">${course.content_richtext}</div>`).show();
                    } else {
                        $('#course-view-content').hide();
                    }

                    if (course.files && course.files.length > 0) {
                        const $filesList = $('#course-view-files-list').empty();
                        course.files.forEach(function(file) {
                            const $fileItem = $(`
                                <div class="file-item">
                                    <a href="${API.getFileDownloadUrl(file.id)}" target="_blank">
                                        📄 ${$('<div>').text(file.original_filename).html()}
                                    </a>
                                    <span class="file-size">(${Math.round(file.file_size / 1024)} KB)</span>
                                </div>
                            `);
                            $filesList.append($fileItem);
                        });
                        $('#course-view-files').show();
                    } else {
                        $('#course-view-files').hide();
                    }

                    $('#course-view-modal').fadeIn(300);
                })
                .fail(function() {
                    // Error already shown
                });
        },

        hideCourseView: function() {
            $('#course-view-modal').fadeOut(300);
        },

        uploadFile: function() {
            const file = $('#course-file-input')[0].files[0];
            if (!file) return;

            if (!AppState.editingCourse) {
                ErrorHandler.show({ message: 'Please save the course first before uploading files', type: 'Validation Error' });
                return;
            }

            $('#save-course-btn').prop('disabled', true).text('Uploading...');

            API.uploadFile(AppState.editingCourse, file)
                .done(function(result) {
                    MessageHandler.show('File uploaded successfully!');
                    $('#course-file-input').val('');

                    // Reload course files
                    API.getCourse(AppState.editingCourse).done(function(data) {
                        CourseManager.renderCourseFiles(data.course.files || []);
                    });
                })
                .fail(function(xhr) {
                    ErrorHandler.show({
                        message: xhr.responseJSON?.error || 'File upload failed',
                        type: 'Upload Error'
                    });
                })
                .always(function() {
                    $('#save-course-btn').prop('disabled', false).text('Save Course');
                });
        },

        deleteFile: function(fileId) {
            if (!confirm('Are you sure you want to delete this file?')) {
                return;
            }

            API.deleteFile(fileId)
                .done(function() {
                    MessageHandler.show('File deleted successfully!');

                    // Reload course files
                    if (AppState.editingCourse) {
                        API.getCourse(AppState.editingCourse).done(function(data) {
                            CourseManager.renderCourseFiles(data.course.files || []);
                        });
                    }
                })
                .fail(function() {
                    // Error already shown
                });
        },

        renderCourseFiles: function(files) {
            const $filesList = $('#course-files-list').empty();

            files.forEach(function(file) {
                const $fileItem = $(`
                    <div class="file-item">
                        <a href="${API.getFileDownloadUrl(file.id)}" target="_blank">
                            📄 ${$('<div>').text(file.original_filename).html()}
                        </a>
                        <button class="btn btn-danger btn-sm delete-file-btn" data-file-id="${file.id}">
                            Delete
                        </button>
                    </div>
                `);
                $filesList.append($fileItem);
            });
        },

        showAssignmentModal: function(courseId, courseTitle) {
            AppState.assigningCourse = courseId;
            $('#assignment-course-title').text(courseTitle);
            $('#assignment-loading').show();
            $('#assignment-students-list').hide();
            $('#save-assignment-btn').prop('disabled', true);

            // Load students and current assignments
            $.when(API.getStudents(), API.getCourseAssignments(courseId))
                .done(function(studentsResp, assignmentsResp) {
                    const students = studentsResp[0].students || [];
                    const assignments = assignmentsResp[0].students || [];
                    const assignedIds = assignments.map(s => s.id);

                    AppState.students = students;

                    const $list = $('#assignment-students-list').empty();

                    students.forEach(function(student) {
                        const isChecked = assignedIds.includes(student.id);
                        const $label = $(`
                            <label class="student-checkbox">
                                <input type="checkbox" value="${student.id}" ${isChecked ? 'checked' : ''}>
                                ${$('<div>').text(student.email).html()}
                            </label>
                        `);
                        $list.append($label);
                    });

                    CourseManager.updateAssignmentCount();

                    $('#assignment-loading').hide();
                    $('#assignment-students-list').show();
                    $('#save-assignment-btn').prop('disabled', false);
                })
                .fail(function() {
                    $('#assignment-loading').hide();
                    ErrorHandler.show({ message: 'Failed to load students', type: 'Load Error' });
                });

            // Handle checkbox changes
            $('#assignment-students-list').off('change').on('change', 'input[type="checkbox"]', function() {
                CourseManager.updateAssignmentCount();
            });

            $('#assignment-modal').fadeIn(300);
        },

        hideAssignmentModal: function() {
            $('#assignment-modal').fadeOut(300);
            AppState.assigningCourse = null;
        },

        updateAssignmentCount: function() {
            const count = $('#assignment-students-list input:checked').length;
            $('#assignment-count').text(`Currently assigned: ${count} student${count !== 1 ? 's' : ''}`);
            $('#save-assignment-btn').text(`Save Assignment (${count} student${count !== 1 ? 's' : ''})`);
        },

        saveAssignment: function() {
            const selectedIds = $('#assignment-students-list input:checked').map(function() {
                return parseInt($(this).val());
            }).get();

            const $btn = $('#save-assignment-btn');
            $btn.prop('disabled', true).text('Assigning...');

            API.assignCourse(AppState.assigningCourse, selectedIds)
                .done(function() {
                    MessageHandler.show(selectedIds.length > 0
                        ? 'Course assigned successfully!'
                        : 'All assignments cleared');
                    CourseManager.hideAssignmentModal();
                })
                .fail(function() {
                    // Error already shown
                })
                .always(function() {
                    $btn.prop('disabled', false);
                    CourseManager.updateAssignmentCount();
                });
        }
    };

    // ==================== Modal Handlers ====================
    const ModalHandlers = {
        init: function() {
            // Close modals when clicking overlay
            $('.modal-overlay').on('click', function(e) {
                if (e.target === this) {
                    $(this).fadeOut(300);
                }
            });

            // Close buttons
            $('.modal-close').on('click', function() {
                $(this).closest('.modal-overlay').fadeOut(300);
            });

            // Error widget handlers
            $('#close-error-widget').on('click', function() {
                ErrorHandler.close();
            });

            $('#toggle-error-details').on('click', function() {
                ErrorHandler.toggleDetails();
            });

            $('#copy-error-btn').on('click', function() {
                ErrorHandler.copyToClipboard();
            });

            // Assignment modal handlers
            $('#cancel-assignment').on('click', function() {
                CourseManager.hideAssignmentModal();
            });

            $('#save-assignment-btn').on('click', function() {
                CourseManager.saveAssignment();
            });
        }
    };

    // ==================== Global Error Handlers ====================
    window.onerror = function(message, source, lineno, colno, error) {
        // Skip showing error widget for "[object Object]" errors from jQuery
        if (message && message.includes('[object Object]')) {
            console.error('Skipping [object Object] error display:', {
                message, source, lineno, colno, error
            });
            return true;
        }
        
        try {
            if (typeof ErrorHandler !== 'undefined' && ErrorHandler.show) {
                ErrorHandler.show({
                    message: message,
                    type: 'JavaScript Error',
                    url: source,
                    stack: error?.stack,
                    details: `Line ${lineno}, Column ${colno}`
                });
            } else {
                console.error('JavaScript Error (ErrorHandler not available):', {
                    message, source, lineno, colno, error
                });
            }
        } catch (e) {
            console.error('Error in error handler:', e);
        }
        return true;
    };

    window.onunhandledrejection = function(event) {
        const error = event.reason;
        
        // Skip showing error widget for jQuery AJAX failures that are already handled
        if (error && error.status && error.responseText !== undefined) {
            console.log('Skipping error widget for handled AJAX failure:', error.status);
            event.preventDefault();
            return;
        }
        
        let message;
        
        // Better error message handling
        if (typeof error === 'string') {
            message = error;
        } else if (error && error.message) {
            message = error.message;
        } else if (error && error.details && error.details.message) {
            message = error.details.message;
        } else {
            message = 'An unknown error occurred';
            console.error('Unhandled rejection with unclear error:', error);
        }
        
        // Only show error widget for genuine unhandled errors
        if (message !== 'An unknown error occurred' || !error.status) {
            ErrorHandler.show({
                message: message,
                type: 'Unhandled Promise Rejection',
                url: error.url || (error.details && error.details.url),
                status: error.status || (error.details && error.details.status),
                response: error.response || (error.details && error.details.response),
                stack: error.stack
            });
        }
        
        event.preventDefault();
    };

    // ==================== Global Utility Functions ====================
    
    // Make these functions available globally for auth handler
    window.updateUserDisplay = function(user) {
        if (user && user !== AppState.currentUser) {
            AppState.currentUser = user;
            // Refresh display if needed
            if (ViewManager.currentView !== 'login') {
                ViewManager.updateUserInfo();
            }
        }
    };
    
    window.clearUserState = function() {
        AppState.currentUser = null;
        // Clear any cached data
        AppState.courses = [];
        AppState.students = [];
        AppState.editingCourse = null;
        AppState.viewingCourse = null;
        AppState.assigningCourse = null;
    };

    // ==================== Initialize Application ====================
    $(document).ready(function() {
        try {
            console.log('jQuery Student Course Management System initialized');

            // Initialize components safely
            if (typeof Auth !== 'undefined' && Auth.init) {
                Auth.init();
            }
            
            if (typeof CourseManager !== 'undefined' && CourseManager.init) {
                CourseManager.init();
            }
            
            if (typeof ModalHandlers !== 'undefined' && ModalHandlers.init) {
                ModalHandlers.init();
            }
            
            console.log('Application initialization completed successfully');
            
        } catch (error) {
            console.error('Error during application initialization:', error);
            // Don't show error widget during init as it might not be ready
            if (typeof ErrorHandler !== 'undefined' && ErrorHandler.show) {
                setTimeout(function() {
                    ErrorHandler.show({
                        message: 'Application failed to initialize: ' + error.message,
                        type: 'Initialization Error',
                        stack: error.stack
                    });
                }, 1000);
            }
        }
    });

})(jQuery);
