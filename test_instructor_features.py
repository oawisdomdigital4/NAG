#!/usr/bin/env python
"""
Test script for instructor quiz analytics and assignment grading features
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, CourseModule, Lesson, QuizQuestion, QuizSubmission, AssignmentSubmission, Enrollment
from datetime import datetime, timedelta

User = get_user_model()

def create_test_data():
    """Create test data for instructor feature testing"""
    print("Creating test data...")
    
    # Get or create facilitator
    facilitator, _ = User.objects.get_or_create(
        username='instructor_test',
        defaults={
            'email': 'instructor@test.com',
            'first_name': 'Test',
            'last_name': 'Instructor',
            'is_staff': True
        }
    )
    
    # Get or create student
    student, _ = User.objects.get_or_create(
        username='student_test',
        defaults={
            'email': 'student@test.com',
            'first_name': 'Test',
            'last_name': 'Student'
        }
    )
    
    # Create test course
    course, _ = Course.objects.get_or_create(
        title='Instructor Features Test Course',
        slug='instructor-test-course',
        defaults={
            'short_description': 'Test course for instructor features',
            'full_description': 'This is a comprehensive test course for instructor features',
            'facilitator': facilitator,
            'category': 'Technology',
            'level': 'Beginner'
        }
    )
    
    # Create module
    module, _ = CourseModule.objects.get_or_create(
        course=course,
        title='Test Module',
        defaults={
            'order': 1,
            'content': 'Test module content'
        }
    )
    
    # Create quiz lesson
    quiz_lesson, created = Lesson.objects.get_or_create(
        module=module,
        title='Test Quiz',
        defaults={
            'lesson_type': 'quiz',
            'order': 1,
            'description': 'Test quiz for analytics',
            'passing_score': 70,
            'quiz_title': 'Test Quiz'
        }
    )
    
    if created:
        print(f"✅ Created quiz lesson: {quiz_lesson.title}")
    
    # Create quiz questions
    q1, _ = QuizQuestion.objects.get_or_create(
        lesson=quiz_lesson,
        question_text='What is 2+2?',
        defaults={
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_option': 'b'
        }
    )
    
    q2, _ = QuizQuestion.objects.get_or_create(
        lesson=quiz_lesson,
        question_text='What is the capital of France?',
        defaults={
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_option': 'a'
        }
    )
    
    # Create assignment lesson
    assignment_lesson, created = Lesson.objects.get_or_create(
        module=module,
        title='Test Assignment',
        defaults={
            'lesson_type': 'assignment',
            'order': 2,
            'description': 'Test assignment for grading',
            'assignment_title': 'Test Assignment',
            'due_date': datetime.now() + timedelta(days=7),
            'points_total': 100
        }
    )
    
    if created:
        print(f"✅ Created assignment lesson: {assignment_lesson.title}")
    
    # Create enrollment
    enrollment, _ = Enrollment.objects.get_or_create(
        user=student,
        course=course,
        defaults={
            'progress': 0
        }
    )
    
    # Create quiz submissions
    for i in range(3):
        submission, created = QuizSubmission.objects.get_or_create(
            enrollment=enrollment,
            lesson=quiz_lesson,
            defaults={
                'score': 75 + (i * 10),
                'answers': {
                    str(q1.id): 'b',
                    str(q2.id): 'a' if i < 2 else 'b'  # Some will fail q2
                },
                'submitted_at': datetime.now() - timedelta(hours=i)
            }
        )
        if created:
            print(f"✅ Created quiz submission {i+1} with score {submission.score}")
    
    # Create assignment submissions
    for i in range(2):
        submission, created = AssignmentSubmission.objects.get_or_create(
            enrollment=enrollment,
            lesson=assignment_lesson,
            defaults={
                'content': f'This is my assignment response #{i+1}. ' * 50,  # ~300 words
                'score': None if i == 0 else 85,
                'feedback': '' if i == 0 else 'Great work!',
                'graded': i > 0,
                'auto_graded': False,
                'submitted_at': datetime.now() - timedelta(hours=i)
            }
        )
        if created:
            print(f"✅ Created assignment submission {i+1}")
    
    print("\n✅ Test data created successfully!")
    return course, quiz_lesson, assignment_lesson

def test_quiz_analytics():
    """Test quiz analytics endpoint"""
    print("\n" + "="*50)
    print("Testing Quiz Analytics Endpoint")
    print("="*50)
    
    from rest_framework.test import APIRequestFactory
    from courses.views import LessonViewSet
    
    course, quiz_lesson, _ = create_test_data()
    facilitator = course.facilitator
    
    factory = APIRequestFactory()
    request = factory.get(f'/api/courses/lessons/{quiz_lesson.id}/quiz-analytics/')
    request.user = facilitator
    
    view = LessonViewSet.as_view({'get': 'quiz_analytics'})
    response = view(request, pk=quiz_lesson.id)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Quiz analytics endpoint working!")
        data = response.data.get('analytics', {})
        print(f"   - Total Submissions: {data.get('total_submissions')}")
        print(f"   - Average Score: {data.get('average_score'):.1f}")
        print(f"   - Pass Rate: {data.get('pass_rate'):.1f}%")
        print(f"   - Questions Data: {len(data.get('questions_data', []))} questions")
    else:
        print(f"❌ Error: {response.data}")

def test_assignment_submissions():
    """Test assignment submissions endpoint"""
    print("\n" + "="*50)
    print("Testing Assignment Submissions Endpoint")
    print("="*50)
    
    from rest_framework.test import APIRequestFactory
    from courses.views import LessonViewSet
    
    course, _, assignment_lesson = create_test_data()
    facilitator = course.facilitator
    
    factory = APIRequestFactory()
    request = factory.get(f'/api/courses/lessons/{assignment_lesson.id}/assignment-submissions/')
    request.user = facilitator
    
    view = LessonViewSet.as_view({'get': 'assignment_submissions'})
    response = view(request, pk=assignment_lesson.id)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Assignment submissions endpoint working!")
        submissions = response.data.get('submissions', [])
        print(f"   - Total Submissions: {len(submissions)}")
        for i, sub in enumerate(submissions, 1):
            print(f"   - Submission {i}: {sub['student_name']}, Graded: {sub['graded']}")
    else:
        print(f"❌ Error: {response.data}")

def test_assignment_grading():
    """Test assignment grading endpoint"""
    print("\n" + "="*50)
    print("Testing Assignment Grading Endpoint")
    print("="*50)
    
    from rest_framework.test import APIRequestFactory
    from courses.views import LessonViewSet
    
    course, _, assignment_lesson = create_test_data()
    facilitator = course.facilitator
    
    # Get first ungraded submission
    submission = AssignmentSubmission.objects.filter(
        lesson=assignment_lesson,
        graded=False
    ).first()
    
    if not submission:
        print("No ungraded submissions found")
        return
    
    print(f"Facilitator: {facilitator.username} ({facilitator.id})")
    print(f"Submission: {submission.id}")
    
    factory = APIRequestFactory()
    request = factory.put(
        f'/api/courses/lessons/{assignment_lesson.id}/assignment-submissions/{submission.id}/grade/',
        {'score': 90, 'feedback': 'Excellent work!'},
        format='json'
    )
    request.user = facilitator
    
    # Test the view directly
    print(f"\nTesting endpoint with facilitator user...")
    print(f"Lesson module course facilitator: {assignment_lesson.module.course.facilitator.username}")
    print(f"Request user: {request.user.username}")
    print(f"Are they equal? {assignment_lesson.module.course.facilitator == request.user}")
    
    view = LessonViewSet.as_view({'put': 'assignment_submission_grade'})
    response = view(request, pk=assignment_lesson.id, submission_id=submission.id)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Assignment grading endpoint working!")
        print(f"   - Message: {response.data.get('message')}")
        
        # Verify the submission was updated
        submission.refresh_from_db()
        print(f"   - Submission Score: {submission.score}")
        print(f"   - Submission Feedback: {submission.feedback}")
        print(f"   - Submission Graded: {submission.graded}")
    else:
        print(f"❌ Error: {response.data}")

if __name__ == '__main__':
    try:
        print("\n🚀 Testing Instructor Features\n")
        test_quiz_analytics()
        test_assignment_submissions()
        test_assignment_grading()
        print("\n✅ All tests completed!\n")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}\n")
        import traceback
        traceback.print_exc()
