# Quick Start Guide - Enrollment System

## For Students

### 1. Enrolling in a Course
- Navigate to any course detail page
- Click the "Enroll Now" button in the sidebar
- Confirm your enrollment when prompted
- You'll be redirected to the learning page

### 2. Accessing Your Courses
- Go to **My Learning** (navigation menu)
- See all your enrolled courses
- Filter by: All, In Progress, or Completed
- Search courses by title

### 3. Learning a Course
- Click "Start Learning" or "Continue Learning" from dashboard
- View modules in order
- Click "Mark Complete & Next" to progress
- Progress bar updates automatically
- Get a certificate when you reach 100%

### 4. Tracking Progress
- Each course shows a progress percentage
- Dashboard displays overall stats:
  - Total courses enrolled
  - Courses in progress
  - Courses completed
  - Average progress across all courses

### 5. Getting Certificates
- Complete a course (reach 100% progress)
- Click "Get Certificate" button
- Download your certificate

---

## For Facilitators

### 1. Viewing Your Students
- Go to **Dashboard** > **My Students**
- See table of all students in your courses
- Shows: Name, Email, Course, Progress, Enrollment Date, Status

### 2. Monitoring Progress
- Progress bar shows each student's completion percentage
- Filter students by:
  - Not Started (0%)
  - In Progress (1-99%)
  - Completed (100%)
- Search students by name, email, or course

### 3. Exporting Student Data
- Click "Export CSV" button
- Download spreadsheet with:
  - Student names and emails
  - Enrolled courses
  - Progress percentages
  - Enrollment dates
- Use for reporting, communication, or analysis

### 4. Student Statistics
- Dashboard shows:
  - Total courses created
  - Total students enrolled
  - Total enrollments
  - Average student progress

### 5. Notifications
- Receive notification when student enrolls
- Shows: Student name, course name, enrollment time
- Can be viewed in notification center

---

## API Reference

### Student Endpoints

#### Enroll in Course
```
POST /api/courses/courses/{course_slug}/enroll/
Authorization: Bearer {token}

Response: 201 Created
{
  "id": 1,
  "user": 2,
  "course": 5,
  "progress": 0,
  "enrolled_at": "2025-01-01T10:00:00Z",
  "course_title": "Python Basics",
  "course_slug": "python-basics",
  "user_name": "John Doe",
  "facilitator_name": "Jane Smith"
}
```

#### Get My Enrollments
```
GET /api/courses/courses/my_enrollments/
Authorization: Bearer {token}

Response: 200 OK
{
  "count": 3,
  "results": [
    { enrollment objects... }
  ]
}
```

#### Update Progress
```
POST /api/courses/courses/update_progress/
Authorization: Bearer {token}
Content-Type: application/json

{
  "course_id": 5,
  "progress": 50
}

Response: 200 OK
{ enrollment object }
```

#### Unenroll from Course
```
POST /api/courses/courses/unenroll/
Authorization: Bearer {token}
Content-Type: application/json

{
  "course_id": 5
}

Response: 200 OK
{
  "success": "Unenrolled successfully"
}
```

### Facilitator Endpoints

#### Get My Students
```
GET /api/courses/courses/my_students/
Authorization: Bearer {token}

Response: 200 OK
{
  "count": 25,
  "results": [
    { enrollment objects for all students... }
  ]
}
```

---

## Common Tasks

### Task: Check if User is Enrolled
```typescript
const { getMyEnrollments } = useEnrollment();
const enrollments = await getMyEnrollments();
const isEnrolled = enrollments.some(e => e.course === courseId);
```

### Task: Update Student Progress Manually
```typescript
const { updateProgress } = useEnrollment();
await updateProgress(courseId, 75); // 75% progress
```

### Task: Remove User from Course
```typescript
const { unenroll } = useEnrollment();
await unenroll(courseId);
```

### Task: Get Facilitator's Student Count
```typescript
const { getStudents } = useEnrollment();
const enrollments = await getStudents();
const uniqueStudents = new Set(enrollments.map(e => e.user)).size;
```

### Task: Export Students to CSV
```typescript
// Already implemented in FacilitatorDashboard
// Click "Export CSV" button
// Or manually via API and CSV formatting
```

---

## Troubleshooting

### Problem: "Already enrolled" error
- **Solution**: User is already enrolled. Use "Continue Learning" instead

### Problem: Progress not updating
- **Solution**: Check network connection, wait for API response
- Progress updates automatically in dashboard after 2-3 seconds

### Problem: Can't see students in dashboard
- **Solution**: 
  - Ensure user role is "facilitator"
  - Must have courses created first
  - Wait for students to enroll

### Problem: Certificate not appearing
- **Solution**: 
  - Course progress must be exactly 100%
  - Refresh page after completion
  - Check different courses if available

### Problem: Notifications not received
- **Solution**: 
  - Check notification center settings
  - Ensure community app is installed
  - Verify notification model exists

---

## Performance Tips

### For High-Volume Users
- Use pagination on endpoints (25 per page default)
- Search/filter before export for large datasets
- Cache enrollment list on client side

### For Facilitators with Many Students
- Use export feature to analyze data offline
- Filter by status to focus on active students
- Search by course to manage per-course students

---

## Support

For issues or questions:
1. Check API error messages
2. Review browser console for frontend errors
3. Check Django logs for backend errors
4. Verify authentication token is valid
5. Ensure user role is appropriate for action

